"""
Step Functions Task: NotifyBorrower
Injects deterministic system confirmation message into the chat channel.
"""
from typing import Dict, Any
from ..common import ddb


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    case_id = event.get("case_id")
    plan = event.get("plan", {})
    applied = event.get("applied", False)

    if applied:
        msg = f"Your relief plan has been confirmed and applied: {plan.get('summary', 'Arrangement active.')}"
    else:
        msg = "Your requested concession could not be approved at this time. Please speak with a specialist for other options."

    ddb.append_message(case_id, "system", msg)
    return event
