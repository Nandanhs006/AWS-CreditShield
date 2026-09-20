"""
Step Functions Task: RequestApproval (waitForTaskToken)
Stages approval record in DynamoDB with Step Functions taskToken and pauses workflow.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from ..common import ddb
from ..governance import decisionlog


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    case_id = event.get("case_id")
    account_id = event.get("account_id")
    plan = event.get("plan", {})
    task_token = event.get("task_token")

    approval_id = f"appr_{uuid.uuid4().hex[:8]}"

    item = {
        "approval_id": approval_id,
        "case_id": case_id,
        "account_id": account_id,
        "plan_id": plan.get("plan_id"),
        "action": plan.get("action"),
        "params": plan.get("params"),
        "task_token": task_token,
        "status": "PENDING",
        "requested_at": datetime.now(timezone.utc).isoformat()
    }
    ddb.create_approval(item)

    # Update case status
    case = ddb.get_case(case_id)
    if case:
        case["status"] = "PENDING_APPROVAL"
        ddb.save_case(case)

    # Log approval request
    decisionlog.append_log_entry(
        case_id,
        "APPROVAL_REQUESTED",
        {"kind": "SYSTEM", "id": "sfn:relief-case"},
        {"approval_id": approval_id, "action": plan.get("action")}
    )

    return {"status": "QUEUED", "approval_id": approval_id}
