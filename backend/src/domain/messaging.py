"""
CreditShield Amazon SNS & Amazon SQS Messaging Integration
Handles:
1. Manager Escalation Alerts via SNS (ManagerApprovalTopic)
2. Post-Relief Event Fan-out via SNS -> SQS (ReliefEventsTopic -> CoreBanking & BorrowerComm queues)
3. High-Throughput Banking Telemetry Buffering via SQS (TelemetryQueue + DLQ)
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional, List

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..common import config
from ..governance import decisionlog

logger = logging.getLogger(__name__)

_sns = None
_sqs = None


def get_sns():
    global _sns
    if _sns is None:
        _sns = boto3.client("sns", region_name=config.AWS_REGION)
    return _sns


def get_sqs():
    global _sqs
    if _sqs is None:
        _sqs = boto3.client("sqs", region_name=config.AWS_REGION)
    return _sqs


def publish_manager_approval_alert(case_id: str, plan: Dict[str, Any], task_token: str) -> Dict[str, Any]:
    """
    Publishes an immediate push notification to the Credit Risk Manager via Amazon SNS.
    Triggered when Step Functions pauses on waitForTaskToken.
    """
    account_id = plan.get("account_id", "ACC-UNKNOWN")
    borrower_name = plan.get("borrower_name", "Borrower")
    option_type = plan.get("action", plan.get("option_type", "DUE_DATE_SHIFT"))
    requested_val = plan.get("params", {}).get("days") or plan.get("requested_value", 30)
    unit = "days" if "DUE_DATE" in option_type else "months"

    message_body = (
        f"🚨 [CreditShield Alert] Manager Approval Required\n"
        f"==================================================\n"
        f"Case ID:        {case_id}\n"
        f"Account:        {account_id} ({borrower_name})\n"
        f"Concession Ask: {option_type} ({requested_val} {unit})\n"
        f"Summary:        {plan.get('summary', 'Hardship relief requested')}\n"
        f"Policy Status:  NEEDS_MANAGER_APPROVAL\n"
        f"==================================================\n"
        f"Action Link:\n"
        f"{config.PUBLIC_APP_URL}/#approvals?case={case_id}&token={task_token[:24]}...\n"
    )

    alert_result = {
        "status": "QUEUED",
        "case_id": case_id,
        "channel": "SNS",
        "topic": config.MANAGER_APPROVAL_TOPIC_ARN or "arn:aws:sns:ap-south-1:123456789012:creditshield-manager-approvals",
        "message_id": f"sns_{uuid.uuid4().hex[:12]}"
    }

    if config.MANAGER_APPROVAL_TOPIC_ARN:
        try:
            sns = get_sns()
            response = sns.publish(
                TopicArn=config.MANAGER_APPROVAL_TOPIC_ARN,
                Subject=f"Approval Required: {case_id} - {borrower_name}",
                Message=message_body,
                MessageAttributes={
                    "case_id": {"DataType": "String", "StringValue": case_id},
                    "relief_type": {"DataType": "String", "StringValue": option_type},
                    "urgency": {"DataType": "String", "StringValue": "HIGH"}
                }
            )
            alert_result["message_id"] = response.get("MessageId", alert_result["message_id"])
            alert_result["status"] = "PUBLISHED"
        except (ClientError, NoCredentialsError) as ex:
            logger.warning(f"SNS Publish skipped (offline/dev fallback): {ex}")
            alert_result["status"] = "SIMULATED_PUBLISHED"

    # Append to immutable cryptographic decision log
    decisionlog.append_log_entry(
        case_id,
        "SNS_ALERT_DISPATCHED",
        {"kind": "SYSTEM", "id": "sns:ManagerApprovalTopic"},
        {
            "topic": alert_result["topic"],
            "message_id": alert_result["message_id"],
            "recipient": "Credit Operations Manager",
            "delivery_status": alert_result["status"]
        }
    )

    return alert_result


def fan_out_relief_event(case_id: str, account: Dict[str, Any], plan: Dict[str, Any], decision: str) -> Dict[str, Any]:
    """
    Publishes post-relief event to SNS ReliefEventsTopic.
    Amazon SNS fans this out to:
    - CoreBankingSyncQueue (CBS ledger reschedule)
    - BorrowerCommQueue (WhatsApp / SMS official confirmation)
    """
    event_payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": "RELIEF_PLAN_APPLIED" if decision == "APPROVED" else "RELIEF_PLAN_REJECTED",
        "case_id": case_id,
        "account_id": account.get("account_id"),
        "decision": decision,
        "plan": plan,
        "applied_at": plan.get("applied_at")
    }

    fanout_result = {
        "status": "FANOUT_INITIATED",
        "event_id": event_payload["event_id"],
        "target_queues": ["CoreBankingSyncQueue", "BorrowerCommQueue"]
    }

    if config.RELIEF_EVENTS_TOPIC_ARN:
        try:
            sns = get_sns()
            res = sns.publish(
                TopicArn=config.RELIEF_EVENTS_TOPIC_ARN,
                Subject=f"Relief Plan {decision}: {case_id}",
                Message=json.dumps(event_payload),
                MessageAttributes={
                    "event_type": {"DataType": "String", "StringValue": event_payload["event_type"]},
                    "account_id": {"DataType": "String", "StringValue": str(account.get("account_id", ""))}
                }
            )
            fanout_result["sns_message_id"] = res.get("MessageId")
            fanout_result["status"] = "FANOUT_CONFIRMED"
        except (ClientError, NoCredentialsError) as ex:
            logger.warning(f"Relief event fan-out simulated: {ex}")
            fanout_result["status"] = "FANOUT_SIMULATED"

    # Log to ledger
    decisionlog.append_log_entry(
        case_id,
        "EVENT_FANOUT",
        {"kind": "SYSTEM", "id": "sns:ReliefEventsTopic"},
        {
            "event_id": event_payload["event_id"],
            "queues_targeted": fanout_result["target_queues"],
            "decision": decision
        }
    )

    return fanout_result


def buffer_telemetry_event(telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Buffers banking events (balance drops, UPI bounced debits) into SQS TelemetryQueue.
    Protects DynamoDB write limits and smooths high-frequency transaction spikes.
    """
    msg_body = json.dumps(telemetry_data)
    result = {
        "status": "BUFFERED",
        "queue": config.TELEMETRY_QUEUE_URL or "creditshield-telemetry-queue",
        "account_id": telemetry_data.get("account_id")
    }

    if config.TELEMETRY_QUEUE_URL:
        try:
            sqs = get_sqs()
            res = sqs.send_message(
                QueueUrl=config.TELEMETRY_QUEUE_URL,
                MessageBody=msg_body,
                MessageAttributes={
                    "account_id": {"DataType": "String", "StringValue": str(telemetry_data.get("account_id", ""))}
                }
            )
            result["message_id"] = res.get("MessageId")
        except (ClientError, NoCredentialsError) as ex:
            logger.warning(f"SQS buffer simulation: {ex}")
            result["status"] = "SIMULATED_BUFFERED"

    return result
