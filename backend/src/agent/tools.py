"""
CreditShield Bedrock Converse Tools Specification & Execution Dispatcher
"""
import uuid
from typing import Dict, Any, List, Tuple
from ..common import ddb
from ..domain import plan
from ..governance import authorize
from ..governance import decisionlog

# Bedrock Converse toolConfig schema
TOOL_SPECS = [
    {
        "toolSpec": {
            "name": "get_case_context",
            "description": "Retrieves hardship context, outstanding balance, EMI details, and past relief count for this borrower.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_relief_options",
            "description": "Probes Cedar policy engine to retrieve options allowed for the assistant alone or requiring manager review.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "propose_relief",
            "description": "Formulates an official relief proposal, validates it against Cedar policies, and stages a plan card for borrower acceptance.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "required": ["action"],
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["DUE_DATE_SHIFT", "PARTIAL_PLAN", "TENURE_EXTENSION", "FEE_WAIVER"]
                        },
                        "days": {"type": "integer", "description": "Number of days to shift due date (1 to 30)"},
                        "upfront_pct": {"type": "integer", "description": "Upfront payment percentage (e.g. 50)"},
                        "installments": {"type": "integer", "description": "Number of monthly installments (e.g. 3)"},
                        "months": {"type": "integer", "description": "Tenure extension in months (1 to 6)"},
                        "amount": {"type": "integer", "description": "Late fee waiver amount in whole rupees"},
                        "borrower_reason": {"type": "string", "description": "Borrower hardship rationale"}
                    }
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "request_human_handoff",
            "description": "Transfers case to a Senior Credit Resolution Officer when borrower requests a human or legal holds apply.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "required": ["reason"],
                    "properties": {
                        "reason": {"type": "string"},
                        "urgency": {"type": "string", "enum": ["NORMAL", "HIGH"]}
                    }
                }
            }
        }
    }
]


def execute_tool(name: str, tool_input: Dict[str, Any], case: Dict[str, Any], account: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """
    Executes a requested tool safely within the authenticated case boundary.
    Returns: (tool_output_dict, proposed_plan_or_none)
    """
    case_id = case["case_id"]

    if name == "get_case_context":
        factors = account.get("stress_factors", [])
        stress_notes = [f.get("note", "") for f in factors if "note" in f]
        output = {
            "first_name": account.get("first_name", account.get("name", "Borrower").split()[0]),
            "segment": account.get("segment", "RETAIL"),
            "emi": int(account.get("emi", 0)),
            "next_due_date": account.get("next_due_date", "2026-09-26"),
            "days_to_emi": int(account.get("days_to_emi", 7)),
            "dpd": int(account.get("dpd", 0)),
            "prior_reliefs": int(account.get("prior_reliefs", 0)),
            "late_fee_due": int(account.get("late_fee_due", 0)),
            "stress_summary": stress_notes,
            "legal_hold": bool(account.get("legal_hold", False)),
            "plan_status": case.get("plan", {}).get("status", "NONE")
        }
        return output, None

    elif name == "get_relief_options":
        options = authorize.get_relief_options(account)
        return options, None

    elif name == "propose_relief":
        action = tool_input.get("action")
        params = {}
        for k in ["days", "upfront_pct", "installments", "months", "amount"]:
            if k in tool_input:
                params[k] = int(tool_input[k])

        auth_res = authorize.authorize_relief(account, action, params)
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        plan_obj = plan.build_plan_object(plan_id, action, params, account, auth_res)

        # Update case
        case["plan"] = plan_obj
        case["status"] = "PLAN_PROPOSED"
        ddb.save_case(case)

        # Append to Decision Log
        decisionlog.append_log_entry(
            case_id,
            "POLICY_DECISION",
            {"kind": "SYSTEM", "id": "avp:cedar-engine"},
            {
                "phase": "propose",
                "action": action,
                "params": params,
                "outcome": auth_res["outcome"],
                "determining_policies": auth_res.get("determining_policies", [])
            }
        )
        decisionlog.append_log_entry(
            case_id,
            "PLAN_PROPOSED",
            {"kind": "AGENT", "id": "bedrock:nova-lite"},
            {"plan": plan_obj}
        )

        output = {
            "outcome": auth_res["outcome"],
            "plan_id": plan_id,
            "summary": plan_obj["summary"],
            "envelope": plan_obj["envelope"],
            "can_accept": plan_obj["can_accept"],
            "reason_for_borrower": auth_res.get("reason", "")
        }
        return output, plan_obj

    elif name == "request_human_handoff":
        reason = tool_input.get("reason", "Borrower requested human specialist")
        urgency = tool_input.get("urgency", "NORMAL")

        case["status"] = "ESCALATED"
        ddb.save_case(case)

        decisionlog.append_log_entry(
            case_id,
            "HANDOFF_REQUESTED",
            {"kind": "AGENT", "id": "bedrock:nova-lite"},
            {"reason": reason, "urgency": urgency}
        )

        return {"status": "handoff_requested", "urgency": urgency}, None

    return {"error": f"Unknown tool: {name}"}, None
