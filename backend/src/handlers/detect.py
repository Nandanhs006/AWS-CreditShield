"""
CreditShield Batch Stress Detection Lambda Handler
Can be triggered periodically via Amazon EventBridge Scheduler.
"""
from typing import Dict, Any
from ..common import ddb
from ..domain import stress


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    accounts = ddb.list_accounts()
    flagged = 0

    for acc in accounts:
        score, tier, factors = stress.calculate_stress_score(acc)
        acc["stress_score"] = score
        acc["stress_tier"] = tier
        acc["stress_factors"] = factors
        if score >= 35:
            flagged += 1
            if not acc.get("cohort"):
                acc["cohort"] = "TREATED" if (hash(acc["account_id"]) % 2 == 0) else "CONTROL"
        ddb.save_account(acc)

    return {
        "status": "COMPLETED",
        "total_accounts": len(accounts),
        "flagged_accounts": flagged
    }
