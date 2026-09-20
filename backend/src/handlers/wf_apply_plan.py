"""
Step Functions Task: ApplyPlan
Applies approved concession in simulated core banking and updates borrower account state.
"""
from typing import Dict, Any
from ..common import ddb
from ..domain.adapters import SimulatedCoreBanking
from ..governance import decisionlog


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    case_id = event.get("case_id")
    plan = event.get("plan", {})

    case = ddb.get_case(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")

    adapter = SimulatedCoreBanking()
    success, changes = adapter.apply_plan(case, plan)

    if not success:
        raise RuntimeError("Failed to apply plan in core banking")

    decisionlog.append_log_entry(
        case_id,
        "PLAN_APPLIED",
        {"kind": "SYSTEM", "id": "adapter:core-banking"},
        {"plan_id": plan.get("plan_id"), "changes": changes}
    )

    event["changes"] = changes
    event["applied"] = True
    return event
