"""
CreditShield Plan Summary Generator
Deterministic integer arithmetic for hardship concession proposals.
"""
import math
from datetime import datetime, timedelta, date
from typing import Dict, Any


def generate_plan_summary(action: str, params: Dict[str, Any], account: Dict[str, Any]) -> str:
    """
    Builds a plain-language summary for the borrower and audit log.
    Enforces integer arithmetic only.
    """
    emi = int(account.get("emi", 0))
    next_due_str = account.get("next_due_date", "2026-09-26")

    if action == "DUE_DATE_SHIFT":
        days = int(params.get("days", 7))
        try:
            base_date = datetime.strptime(next_due_str, "%Y-%m-%d").date()
            new_date = base_date + timedelta(days=days)
            old_formatted = base_date.strftime("%d %b")
            new_formatted = new_date.strftime("%d %b %Y")
            return f"Move your next EMI from {old_formatted} to {new_formatted}. The amount does not change."
        except Exception:
            return f"Move your next EMI by {days} days. The amount does not change."

    elif action == "PARTIAL_PLAN":
        pct = int(params.get("upfront_pct", 50))
        installments = int(params.get("installments", 3))
        upfront = math.ceil(emi * pct / 100)
        remainder = emi - upfront
        per_installment = math.ceil(remainder / installments) if installments > 0 else 0
        return (
            f"Pay ₹{upfront:,} on the due date. "
            f"The remaining ₹{remainder:,} is spread across your next {installments} EMIs "
            f"(₹{per_installment:,} extra each)."
        )

    elif action == "TENURE_EXTENSION":
        months = int(params.get("months", 3))
        return f"Extend your loan term by {months} months. The lender will confirm the revised EMI in writing."

    elif action == "FEE_WAIVER":
        amount = int(params.get("amount", 0))
        return f"Waive ₹{amount:,} of late fees assessed on your account."

    return "Temporary relief plan arrangement."


def build_plan_object(plan_id: str, action: str, params: Dict[str, Any], account: Dict[str, Any], auth_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assembles standard plan dictionary according to Section 6.2.
    """
    summary = generate_plan_summary(action, params, account)
    outcome = auth_result.get("outcome", "DENIED")
    
    envelope = {}
    if action == "DUE_DATE_SHIFT":
        envelope = {
            "param": "days",
            "requested": int(params.get("days", 0)),
            "agent_max": 10,
            "manager_max": 30,
            "unit": "days"
        }
    elif action == "TENURE_EXTENSION":
        envelope = {
            "param": "months",
            "requested": int(params.get("months", 0)),
            "agent_max": 3,
            "manager_max": 6,
            "unit": "months"
        }
    elif action == "FEE_WAIVER":
        envelope = {
            "param": "amount",
            "requested": int(params.get("amount", 0)),
            "agent_max": 500,
            "manager_max": 2000,
            "unit": "rupees"
        }
    else:
        envelope = {
            "param": "upfront_pct",
            "requested": int(params.get("upfront_pct", 50)),
            "agent_max": 50,
            "manager_max": 25,
            "unit": "percent"
        }

    return {
        "plan_id": plan_id,
        "action": action,
        "params": params,
        "summary": summary,
        "outcome": outcome,
        "envelope": envelope,
        "determining_policies": auth_result.get("determining_policies", []),
        "status": "PROPOSED",
        "can_accept": (outcome in ("ALLOWED", "NEEDS_MANAGER_APPROVAL"))
    }
