"""
CreditShield Public Chat API Handler (AWS Lambda)
Serves public borrower chat endpoints scoped securely by borrower_token.
"""
import json
import boto3
import uuid
from typing import Dict, Any

from ..common import config
from ..common import jsonutil
from ..common import ddb
from ..agent import loop
from ..governance import decisionlog

_sfn = None


def get_sfn():
    global _sfn
    if _sfn is None:
        _sfn = boto3.client("stepfunctions", region_name=config.AWS_REGION)
    return _sfn


def response(status_code: int, body: Any) -> Dict[str, Any]:
    """Generates standard API Gateway HTTP API JSON response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
        },
        "body": jsonutil.dumps(body)
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    http_ctx = event.get("requestContext", {}).get("http", {})
    method = http_ctx.get("method", "GET").upper()
    path = event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}

    # Handle CORS preflight
    if method == "OPTIONS":
        return response(200, {"ok": True})

    # Health Check
    if path == "/health" or path == "/":
        return response(200, {
            "ok": True,
            "system": "CreditShield Core",
            "track": "Ship It (AWS Hackathon 2026)",
            "version": "1.0.0"
        })

    # Public borrower chat routes require {token}
    token = path_params.get("token")
    if not token and "/public/chat/" in path:
        parts = path.split("/public/chat/")[1].split("/")
        token = parts[0] if parts else None

    if not token:
        return response(400, {"error": "BAD_REQUEST", "message": "Missing borrower token."})

    # Look up case by token
    case = ddb.get_case_by_token(token)
    if not case:
        return response(404, {"error": "NOT_FOUND", "message": "Invalid or expired relief link."})

    account = ddb.get_account(case.get("account_id", ""))
    if not account:
        return response(404, {"error": "NOT_FOUND", "message": "Associated account record not found."})

    # Route 1: GET /public/chat/{token} - Case view for borrower
    if method == "GET" and path.endswith(token):
        messages = ddb.get_case_messages(case["case_id"])
        # Scrub internal tool traces from public view
        safe_messages = []
        for m in messages:
            safe_messages.append({
                "role": m.get("role"),
                "text": m.get("text"),
                "timestamp": m.get("timestamp")
            })

        return response(200, {
            "lender_name": config.LENDER_NAME,
            "borrower_first_name": account.get("first_name", account.get("name", "Borrower").split()[0]),
            "product": account.get("product"),
            "emi": int(account.get("emi", 0)),
            "days_to_emi": int(account.get("days_to_emi", 7)),
            "messages": safe_messages,
            "plan": case.get("plan"),
            "case_status": case.get("status")
        })

    # Parse body for POST requests
    body = {}
    if event.get("body"):
        try:
            body = json.loads(event["body"])
        except Exception:
            return response(400, {"error": "INVALID_JSON", "message": "Malformed JSON payload."})

    # Route 2: POST /public/chat/{token} - Run agent turn
    if method == "POST" and path.endswith(token):
        user_message = body.get("message", "").strip()
        if not user_message:
            return response(400, {"error": "EMPTY_MESSAGE", "message": "Message text cannot be empty."})
        if len(user_message) > config.MAX_MESSAGE_CHAR_LENGTH:
            return response(400, {"error": "MESSAGE_TOO_LONG", "message": f"Max {config.MAX_MESSAGE_CHAR_LENGTH} characters."})

        # Cap message count
        msg_count = case.get("msg_count", 0)
        if msg_count >= config.MAX_MESSAGES_PER_CASE:
            return response(429, {"error": "LIMIT_REACHED", "message": "Conversation limit reached for this session."})

        case["msg_count"] = msg_count + 1
        ddb.save_case(case)

        turn_result = loop.run_agent_turn(case, account, user_message)
        return response(200, turn_result)

    # Route 3: POST /public/chat/{token}/accept - Accept proposed plan & trigger Step Functions
    if method == "POST" and path.endswith("/accept"):
        plan_id = body.get("plan_id")
        current_plan = case.get("plan")

        if not current_plan or current_plan.get("status") != "PROPOSED":
            return response(400, {"error": "NO_PROPOSED_PLAN", "message": "No active proposed plan to accept."})
        if plan_id and current_plan.get("plan_id") != plan_id:
            return response(400, {"error": "PLAN_MISMATCH", "message": "Accepted plan ID does not match proposed plan."})
        if not current_plan.get("can_accept"):
            return response(403, {"error": "UNACCEPTABLE_PLAN", "message": "This plan requires manual intervention."})

        # Update plan status
        current_plan["status"] = "ACCEPTED"
        case["plan"] = current_plan
        case["status"] = "PENDING_APPROVAL" if current_plan.get("outcome") == "NEEDS_MANAGER_APPROVAL" else "APPLIED"
        ddb.save_case(case)

        # Log borrower consent
        decisionlog.append_log_entry(
            case["case_id"],
            "BORROWER_ACCEPTED",
            {"kind": "BORROWER", "id": str(account.get("account_id"))},
            {"plan_id": current_plan.get("plan_id"), "outcome": current_plan.get("outcome")}
        )

        # Trigger Step Functions execution if ARN configured
        execution_arn = None
        if config.STATE_MACHINE_ARN:
            try:
                sfn = get_sfn()
                exec_name = f"case-{case['case_id'][:8]}-{uuid.uuid4().hex[:6]}"
                sfn_res = sfn.start_execution(
                    stateMachineArn=config.STATE_MACHINE_ARN,
                    name=exec_name,
                    input=jsonutil.dumps({
                        "case_id": case["case_id"],
                        "account_id": account.get("account_id"),
                        "plan": current_plan
                    })
                )
                execution_arn = sfn_res.get("executionArn")
                case["sfn_execution_arn"] = execution_arn
                ddb.save_case(case)
            except Exception:
                pass

        # If outcome is ALLOWED and offline, apply directly
        if current_plan.get("outcome") == "ALLOWED":
            from ..domain.adapters import SimulatedCoreBanking
            adapter = SimulatedCoreBanking()
            adapter.apply_plan(case, current_plan)

        return response(200, {
            "status": "ACCEPTED",
            "case_status": case.get("status"),
            "plan": current_plan,
            "execution_arn": execution_arn
        })

    # Route 4: POST /public/chat/{token}/decline - Decline proposed terms
    if method == "POST" and path.endswith("/decline"):
        if "plan" in case:
            case["plan"]["status"] = "DECLINED"
        ddb.save_case(case)

        decisionlog.append_log_entry(
            case["case_id"],
            "PLAN_DECLINED",
            {"kind": "BORROWER", "id": str(account.get("account_id"))},
            {"reason": "Borrower declined proposed terms."}
        )

        return response(200, {"status": "DECLINED", "case_status": case.get("status")})

    # Route 5: POST /public/chat/{token}/handoff - Escalate to human officer
    if method == "POST" and path.endswith("/handoff"):
        case["status"] = "ESCALATED"
        ddb.save_case(case)

        decisionlog.append_log_entry(
            case["case_id"],
            "HANDOFF_REQUESTED",
            {"kind": "BORROWER", "id": str(account.get("account_id"))},
            {"reason": "Borrower pressed 'Talk to a person' button."}
        )

        return response(200, {"status": "ESCALATED", "case_status": "ESCALATED"})

    return response(404, {"error": "NOT_FOUND", "message": f"Route not found: {method} {path}"})
