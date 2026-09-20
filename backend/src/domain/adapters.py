"""
CreditShield Core Banking Adapter Interface & Simulated Implementation
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from ..common import ddb


class CoreBankingAdapter:
    def apply_plan(self, case: Dict[str, Any], plan: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        raise NotImplementedError


class SimulatedCoreBanking(CoreBankingAdapter):
    def apply_plan(self, case: Dict[str, Any], plan: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        account_id = case.get("account_id")
        account = None
        try:
            account = ddb.get_account(account_id)
        except Exception:
            pass

        if not account:
            account = case.get("account", {"account_id": account_id, "prior_reliefs": 0, "next_due_date": "2026-09-26"})

        action = plan.get("action")
        params = plan.get("params", {})
        changes = {}

        if action == "DUE_DATE_SHIFT":
            days = int(params.get("days", 7))
            old_due = account.get("next_due_date", "2026-09-26")
            base = datetime.strptime(old_due, "%Y-%m-%d").date()
            new_due = (base + timedelta(days=days)).isoformat()
            account["next_due_date"] = new_due
            changes["next_due_date"] = {"old": old_due, "new": new_due}

        elif action == "FEE_WAIVER":
            amount = int(params.get("amount", 0))
            old_fee = account.get("late_fee_due", 0)
            new_fee = max(0, old_fee - amount)
            account["late_fee_due"] = new_fee
            changes["late_fee_due"] = {"old": old_fee, "new": new_fee}
            account["concession_cost"] = account.get("concession_cost", 0) + amount

        elif action == "PARTIAL_PLAN":
            changes["plan_type"] = "PARTIAL_INSTALLMENT"

        elif action == "TENURE_EXTENSION":
            months = int(params.get("months", 3))
            changes["tenure_extended_months"] = months

        # Increment prior reliefs counter
        old_reliefs = account.get("prior_reliefs", 0)
        account["prior_reliefs"] = old_reliefs + 1
        changes["prior_reliefs"] = {"old": old_reliefs, "new": old_reliefs + 1}
        account["case_status"] = "APPLIED"

        try:
            ddb.save_account(account)
        except Exception:
            pass

        # Update case
        case["status"] = "APPLIED"
        if "plan" in case:
            case["plan"]["status"] = "APPLIED"
        try:
            ddb.save_case(case)
        except Exception:
            pass

        return True, changes
