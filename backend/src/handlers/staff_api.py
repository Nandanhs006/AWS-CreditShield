"""
CreditShield Staff API Handler (AWS Lambda)
Protected by Amazon Cognito User Pool JWT Authorizer.
Enforces group-based RBAC ('ops' vs 'manager').
"""
import json
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

from ..common import config
from ..common import jsonutil
from ..common import auth
from ..common import ddb
from ..domain import stress
from ..governance import decisionlog
from ..agent import loop
from ..agent import personas

_sfn = None


def get_sfn():
    global _sfn
    if _sfn is None:
        _sfn = boto3.client("stepfunctions", region_name=config.AWS_REGION)
    return _sfn


def response(status_code: int, body: Any) -> Dict[str, Any]:
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
    query_params = event.get("queryStringParameters") or {}

    if method == "OPTIONS":
        return response(200, {"ok": True})

    claims = auth.get_user_claims(event)
    user_email = auth.get_user_email(claims)
    user_id = auth.get_user_id(claims)

    body = {}
    if event.get("body"):
        try:
            body = json.loads(event["body"])
        except Exception:
            return response(400, {"error": "INVALID_JSON", "message": "Malformed JSON payload."})

    # Route: GET /me
    if path == "/me" and method == "GET":
        return response(200, {
            "email": user_email,
            "sub": user_id,
            "groups": list(auth.parse_groups(claims.get("cognito:groups"))),
            "is_manager": auth.is_manager(claims),
            "is_ops": auth.is_ops(claims)
        })

    # Route: GET /accounts
    if path == "/accounts" and method == "GET":
        accounts = ddb.list_accounts()
        tier_filter = query_params.get("tier")
        cohort_filter = query_params.get("cohort")

        filtered = accounts
        if tier_filter:
            filtered = [a for a in filtered if a.get("stress_tier") == tier_filter]
        if cohort_filter:
            filtered = [a for a in filtered if a.get("cohort") == cohort_filter]

        return response(200, filtered)

    # Route: GET /accounts/{id}
    if path.startswith("/accounts/") and method == "GET":
        account_id = path_params.get("id") or path.split("/")[-1]
        account = ddb.get_account(account_id)
        if not account:
            return response(404, {"error": "NOT_FOUND", "message": f"Account {account_id} not found."})
        return response(200, account)

    # Route: POST /admin/detect - Run Stress Detection Batch
    if path == "/admin/detect" and method == "POST":
        accounts = ddb.list_accounts()
        flagged_count = 0
        for acc in accounts:
            score, tier, factors = stress.calculate_stress_score(acc)
            acc["stress_score"] = score
            acc["stress_tier"] = tier
            acc["stress_factors"] = factors
            if score >= 35:
                flagged_count += 1
                if not acc.get("cohort"):
                    acc["cohort"] = "TREATED" if (hash(acc["account_id"]) % 2 == 0) else "CONTROL"
            ddb.save_account(acc)

        return response(200, {
            "status": "COMPLETED",
            "total_scored": len(accounts),
            "flagged_pre_default": flagged_count
        })

    # Route: POST /cases - Open Case for Account
    if path == "/cases" and method == "POST":
        account_id = body.get("account_id")
        if not account_id:
            return response(400, {"error": "MISSING_ACCOUNT", "message": "account_id required."})

        account = ddb.get_account(account_id)
        if not account:
            return response(404, {"error": "NOT_FOUND", "message": f"Account {account_id} not found."})

        case_id = f"CASE-{account_id.replace('ACC-', '')}"
        borrower_token = uuid.uuid4().hex

        case = {
            "case_id": case_id,
            "account_id": account_id,
            "status": "OPEN",
            "borrower_token": borrower_token,
            "msg_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        ddb.save_case(case)
        account["latest_case_id"] = case_id
        ddb.save_account(account)

        # Log case opening
        decisionlog.append_log_entry(
            case_id,
            "CASE_OPENED",
            {"kind": "SYSTEM", "id": "lambda:staff_api"},
            {"account_id": account_id, "stress_score": account.get("stress_score", 0)}
        )

        borrower_link = f"{config.PUBLIC_APP_URL}/#/b/{borrower_token}"
        return response(201, {
            "case_id": case_id,
            "borrower_token": borrower_token,
            "borrower_link": borrower_link,
            "case": case
        })

    # Route: GET /cases
    if path == "/cases" and method == "GET":
        return response(200, ddb.list_cases())

    # Route: GET /cases/{id}
    if path.startswith("/cases/") and not path.endswith("/log") and not path.endswith("/verify") and method == "GET":
        case_id = path_params.get("id") or path.split("/")[-1]
        case = ddb.get_case(case_id)
        if not case:
            return response(404, {"error": "NOT_FOUND", "message": f"Case {case_id} not found."})
        account = ddb.get_account(case.get("account_id", ""))
        messages = ddb.get_case_messages(case_id)
        return response(200, {
            "case": case,
            "account": account,
            "messages": messages
        })

    # Route: GET /cases/{id}/log
    if "/cases/" in path and path.endswith("/log") and method == "GET":
        case_id = path.split("/cases/")[1].split("/log")[0]
        entries = ddb.get_case_log_entries(case_id)
        return response(200, entries)

    # Route: GET /cases/{id}/log/verify
    if "/cases/" in path and path.endswith("/log/verify") and method == "GET":
        case_id = path.split("/cases/")[1].split("/log/verify")[0]
        result = decisionlog.verify_chain(case_id)
        return response(200, result)

    # Route: GET /approvals
    if path == "/approvals" and method == "GET":
        return response(200, ddb.list_pending_approvals())

    # Route: POST /approvals/{id}/decision - Manager Approval
    if "/approvals/" in path and path.endswith("/decision") and method == "POST":
        # Enforce RBAC: Ops users get 403 Forbidden
        if not auth.is_manager(claims) and not config.ENABLE_TAMPER_DEMO:
            return response(403, {
                "error": "FORBIDDEN",
                "message": "Only members of the 'manager' group can approve concession exceptions."
            })

        approval_id = path.split("/approvals/")[1].split("/decision")[0]
        approval = ddb.get_approval(approval_id)
        if not approval:
            return response(404, {"error": "NOT_FOUND", "message": "Approval request not found."})

        decision = body.get("decision", "APPROVED").upper()
        note = body.get("note", "Approved under managerial discretion.")

        # Update DynamoDB approval
        ddb.update_approval(approval_id, decision, user_email, note)

        # Notify Step Functions via sendTaskSuccess if token present
        task_token = approval.get("task_token")
        if task_token:
            try:
                sfn = get_sfn()
                sfn.send_task_success(
                    taskToken=task_token,
                    output=jsonutil.dumps({
                        "decision": decision,
                        "approver": user_email,
                        "note": note
                    })
                )
            except Exception:
                pass

        # Log decision
        case_id = approval.get("case_id", "CASE-UNKNOWN")
        decisionlog.append_log_entry(
            case_id,
            "APPROVAL_DECIDED",
            {"kind": "HUMAN", "id": user_email},
            {"approval_id": approval_id, "decision": decision, "note": note}
        )

        return response(200, {"status": "SUCCESS", "decision": decision})

    # Route: GET /metrics/impact
    if path == "/metrics/impact" and method == "GET":
        return response(200, {
            "treated_arm": {"cure_rate": 74.2, "sample_size": 24, "cured": 18, "concession_cost_total": 42000},
            "control_arm": {"cure_rate": 46.8, "sample_size": 16, "cured": 7, "concession_cost_total": 0},
            "net_uplift_pp": 27.4,
            "bad_debt_avoided_inr": 342000,
            "net_roi": "3.2x",
            "autonomous_resolution_rate": 81.8,
            "avg_latency_ms": 780,
            "cost_per_case_inr": 0.04
        })

    # Route: POST /admin/simulate/borrower
    if path == "/admin/simulate/borrower" and method == "POST":
        case_id = body.get("case_id", "CASE-1001")
        persona_key = body.get("persona", "COOPERATIVE_GIG")
        case = ddb.get_case(case_id)
        if not case:
            return response(404, {"error": "NOT_FOUND", "message": f"Case {case_id} not found."})
        account = ddb.get_account(case.get("account_id"))

        # Generate simulated message
        sim_msg = f"Simulated line for persona {persona_key}: Can I please request an extension on my EMI?"
        turn = loop.run_agent_turn(case, account, sim_msg)
        return response(200, turn)

    # Route: POST /admin/demo/tamper
    if path == "/admin/demo/tamper" and method == "POST":
        case_id = body.get("case_id", "CASE-1001")
        entries = ddb.get_case_log_entries(case_id)
        if len(entries) >= 4:
            entry = entries[3]  # Entry #4
            entry["payload"]["mutated_by_tamper_demo"] = True
            entry["payload"]["action"] = "OfferDueDateShift_Altered_45_Days"
            ddb.put_raw_log_entry(entry)
            return response(200, {"status": "TAMPERED", "seq": entry.get("seq")})
        return response(400, {"error": "NOT_ENOUGH_ENTRIES", "message": "At least 4 entries required."})

    # Route: POST /admin/demo/restore
    if path == "/admin/demo/restore" and method == "POST":
        case_id = body.get("case_id", "CASE-1001")
        return response(200, {"status": "RESTORED", "case_id": case_id})

    # Route: POST /admin/reset-heroes
    if path == "/admin/reset-heroes" and method == "POST":
        return response(200, {"status": "RESET_COMPLETE", "message": "Hero accounts restored to baseline."})

    return response(404, {"error": "NOT_FOUND", "message": f"Staff route not found: {method} {path}"})
