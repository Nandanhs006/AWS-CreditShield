"""
CreditShield Cedar Policy Authorization Engine (Amazon Verified Permissions)
Implements two-tier authorization:
1. May the AI Agent offer this alone? (ALLOW -> ALLOWED)
2. May a Human Manager approve this? (ALLOW -> NEEDS_MANAGER_APPROVAL)
3. Otherwise -> DENIED
"""
import boto3
from typing import Dict, Any, List, Optional
from ..common import config

_avp = None
_policy_cache = {}


def get_avp():
    global _avp
    if _avp is None:
        _avp = boto3.client("verifiedpermissions", region_name=config.AWS_REGION)
    return _avp


def _build_entities(loan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Constructs Verified Permissions Cedar entities payload."""
    account_id = str(loan.get("account_id", loan.get("id", "ACC-UNKNOWN")))
    return [
        {
            "identifier": {
                "entityType": "Relief::Loan",
                "entityId": account_id
            },
            "attributes": {
                "dpd": {"long": int(loan.get("dpd", 0))},
                "priorReliefs": {"long": int(loan.get("prior_reliefs", loan.get("priorReliefs", 0)))},
                "legalHold": {"boolean": bool(loan.get("legal_hold", loan.get("legalHold", False)))},
                "emi": {"long": int(loan.get("emi", 0))},
                "outstanding": {"long": int(loan.get("outstanding", 0))}
            }
        }
    ]


def _build_context(action: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Maps action and params to Cedar context attributes."""
    ctx = {}
    if action == "DUE_DATE_SHIFT":
        ctx["days"] = {"long": int(params.get("days", 0))}
    elif action == "PARTIAL_PLAN":
        ctx["upfrontPct"] = {"long": int(params.get("upfront_pct", 50))}
        ctx["installments"] = {"long": int(params.get("installments", 3))}
    elif action == "TENURE_EXTENSION":
        ctx["months"] = {"long": int(params.get("months", 0))}
    elif action == "FEE_WAIVER":
        ctx["amount"] = {"long": int(params.get("amount", 0))}
    return ctx


ACTION_MAPPING = {
    "DUE_DATE_SHIFT": "OfferDueDateShift",
    "PARTIAL_PLAN": "OfferPartialPlan",
    "TENURE_EXTENSION": "OfferTenureExtension",
    "FEE_WAIVER": "OfferFeeWaiver"
}


def _local_evaluate_cedar(loan: Dict[str, Any], action: str, params: Dict[str, Any], principal_type: str) -> bool:
    """
    Exact local replica of the 11 Cedar policies for unit tests and standby resilience.
    """
    legal_hold = bool(loan.get("legal_hold", loan.get("legalHold", False)))
    dpd = int(loan.get("dpd", 0))
    prior = int(loan.get("prior_reliefs", loan.get("priorReliefs", 0)))

    # Global Forbids: F1, F2, F3
    if legal_hold:
        return False
    if dpd > 90:
        return False
    if prior >= 3:
        return False

    if action == "DUE_DATE_SHIFT":
        days = int(params.get("days", 0))
        if days > 30:
            return False  # Nobody may grant >30d
        if principal_type == "AiAgent":
            return (1 <= days <= 10) and (dpd <= 30) and (prior < 2)
        elif principal_type == "Manager":
            return (1 <= days <= 30) and (dpd <= 60) and (prior < 3)

    elif action == "PARTIAL_PLAN":
        upfront = int(params.get("upfront_pct", 50))
        installments = int(params.get("installments", 3))
        if principal_type == "AiAgent":
            return (upfront >= 50) and (installments <= 3) and (dpd <= 30) and (prior < 2)
        elif principal_type == "Manager":
            return (upfront >= 25) and (installments <= 6) and (dpd <= 60) and (prior < 3)

    elif action == "TENURE_EXTENSION":
        months = int(params.get("months", 0))
        if months > 6:
            return False  # P6: Max 6 months forbidden for all
        if principal_type == "AiAgent":
            return (1 <= months <= 3) and (prior == 0) and (dpd <= 30)
        elif principal_type == "Manager":
            return (1 <= months <= 6) and (dpd <= 60) and (prior < 2)

    elif action == "FEE_WAIVER":
        amount = int(params.get("amount", 0))
        if amount > 2000:
            return False  # Nobody may grant >2000
        if principal_type == "AiAgent":
            return (amount <= 500) and (dpd <= 30) and (prior < 2)
        elif principal_type == "Manager":
            return (amount <= 2000) and (dpd <= 60) and (prior < 3)

    return False


def authorize_relief(loan: Dict[str, Any], action: str, params: Dict[str, Any], approver_sub: Optional[str] = None) -> Dict[str, Any]:
    """
    Main authorization entry point implementing the two-tier Cedar verification.
    """
    # 1. Validate inputs (fail closed)
    if action not in ACTION_MAPPING:
        return {
            "outcome": "DENIED",
            "reason": "Unknown action type.",
            "determining_policies": []
        }

    for k, v in params.items():
        if not isinstance(v, int) or v < 0 or v > 100000:
            return {
                "outcome": "DENIED",
                "reason": f"Invalid parameter range for {k}.",
                "determining_policies": []
            }

    cedar_action = ACTION_MAPPING[action]
    account_id = str(loan.get("account_id", loan.get("id", "ACC-UNKNOWN")))

    # Check if live Verified Permissions is configured
    if config.POLICY_STORE_ID:
        try:
            avp = get_avp()
            entities = {"entityList": _build_entities(loan)}
            context = {"contextMap": _build_context(action, params)}
            resource = {"entityType": "Relief::Loan", "entityId": account_id}

            # Tier 1: Agent alone check
            res_agent = avp.is_authorized(
                policyStoreId=config.POLICY_STORE_ID,
                principal={"entityType": "Relief::AiAgent", "entityId": "agent-v1"},
                action={"actionType": "Relief::Action", "actionId": cedar_action},
                resource=resource,
                context=context,
                entities=entities
            )

            if res_agent.get("decision") == "ALLOW":
                return {
                    "outcome": "ALLOWED",
                    "agent_decision": "ALLOW",
                    "manager_decision": None,
                    "determining_policies": res_agent.get("determiningPolicies", []),
                    "reason": "Permitted autonomously under Cedar agent policy."
                }

            # Tier 2: Manager approval check
            manager_id = approver_sub if approver_sub else "manager-tier"
            res_mgr = avp.is_authorized(
                policyStoreId=config.POLICY_STORE_ID,
                principal={"entityType": "Relief::Manager", "entityId": manager_id},
                action={"actionType": "Relief::Action", "actionId": cedar_action},
                resource=resource,
                context=context,
                entities=entities
            )

            if res_mgr.get("decision") == "ALLOW":
                return {
                    "outcome": "NEEDS_MANAGER_APPROVAL",
                    "agent_decision": "DENY",
                    "manager_decision": "ALLOW",
                    "determining_policies": res_mgr.get("determiningPolicies", []),
                    "reason": "Exceeds agent threshold. Allowed subject to Senior Manager approval."
                }

            return {
                "outcome": "DENIED",
                "agent_decision": "DENY",
                "manager_decision": "DENY",
                "determining_policies": res_mgr.get("determiningPolicies", []),
                "reason": "Denied by Cedar policy boundaries for all principals."
            }

        except Exception as e:
            # Fall back to local evaluation if AVP store is unreachable
            pass

    # Local fallback / standalone evaluation
    if _local_evaluate_cedar(loan, action, params, "AiAgent"):
        return {
            "outcome": "ALLOWED",
            "agent_decision": "ALLOW",
            "manager_decision": None,
            "determining_policies": [{"id": f"P1_{action.lower()}", "description": "Allowed for agent alone"}],
            "reason": "Permitted autonomously by policy."
        }

    if _local_evaluate_cedar(loan, action, params, "Manager"):
        return {
            "outcome": "NEEDS_MANAGER_APPROVAL",
            "agent_decision": "DENY",
            "manager_decision": "ALLOW",
            "determining_policies": [{"id": f"P2_{action.lower()}", "description": "Allowed for manager review"}],
            "reason": "Exceeds agent autonomy limit; eligible for Senior Manager discretion."
        }

    return {
        "outcome": "DENIED",
        "agent_decision": "DENY",
        "manager_decision": "DENY",
        "determining_policies": [{"id": "F1_global_forbid", "description": "Forbidden by credit governance policy"}],
        "reason": "Concession request outside authorized parameters."
    }


def get_relief_options(loan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Limits probing over numeric ladders so the LLM agent only proposes reachable terms.
    """
    options = {
        "alone": [],
        "needs_manager": []
    }

    # 1. Due Date Shift ladder
    for d in [1, 3, 5, 7, 10, 14, 21, 30]:
        res = authorize_relief(loan, "DUE_DATE_SHIFT", {"days": d})
        if res["outcome"] == "ALLOWED":
            options["alone"].append(f"DUE_DATE_SHIFT ({d} days)")
        elif res["outcome"] == "NEEDS_MANAGER_APPROVAL":
            options["needs_manager"].append(f"DUE_DATE_SHIFT ({d} days)")

    # 2. Partial Plan ladder
    for pct, inst in [(50, 3), (25, 6)]:
        res = authorize_relief(loan, "PARTIAL_PLAN", {"upfront_pct": pct, "installments": inst})
        label = f"PARTIAL_PLAN ({pct}% upfront, {inst} installments)"
        if res["outcome"] == "ALLOWED":
            options["alone"].append(label)
        elif res["outcome"] == "NEEDS_MANAGER_APPROVAL":
            options["needs_manager"].append(label)

    # 3. Fee Waiver
    late_fee = int(loan.get("late_fee_due", 0))
    if late_fee > 0:
        res = authorize_relief(loan, "FEE_WAIVER", {"amount": min(500, late_fee)})
        if res["outcome"] == "ALLOWED":
            options["alone"].append(f"FEE_WAIVER (₹{min(500, late_fee)})")
        res_mgr = authorize_relief(loan, "FEE_WAIVER", {"amount": min(2000, late_fee)})
        if res_mgr["outcome"] == "NEEDS_MANAGER_APPROVAL":
            options["needs_manager"].append(f"FEE_WAIVER (₹{min(2000, late_fee)})")

    return options
