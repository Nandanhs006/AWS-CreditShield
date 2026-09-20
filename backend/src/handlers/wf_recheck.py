"""
Step Functions Task: RecheckPolicy
Re-evaluates Cedar policy right before execution to prevent race condition modifications.
"""
from typing import Dict, Any
from ..common import ddb
from ..governance import authorize
from ..governance import decisionlog


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    case_id = event.get("case_id")
    account_id = event.get("account_id")
    plan = event.get("plan", {})

    account = ddb.get_account(account_id)
    if not account:
        raise ValueError(f"Account {account_id} not found")

    action = plan.get("action")
    params = plan.get("params", {})

    auth_res = authorize.authorize_relief(account, action, params)
    outcome = auth_res.get("outcome", "DENIED")

    decisionlog.append_log_entry(
        case_id,
        "POLICY_DECISION",
        {"kind": "SYSTEM", "id": "avp:cedar-engine"},
        {
            "phase": "recheck",
            "action": action,
            "params": params,
            "outcome": outcome,
            "determining_policies": auth_res.get("determining_policies", [])
        }
    )

    event["auth"] = auth_res
    event["outcome"] = outcome
    return event
