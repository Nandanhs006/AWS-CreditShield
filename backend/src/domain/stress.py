"""
CreditShield Stress Detection Engine
Deterministic explainable cashflow scoring. No machine learning.
"""
import math
from typing import Dict, Any, Tuple, List


def calculate_stress_score(account: Dict[str, Any], as_of_date=None) -> Tuple[int, str, List[Dict[str, Any]]]:
    """
    Computes deterministic early stress telemetry for an account.
    Returns: (stress_score: int, stress_tier: str, stress_factors: list)
    """
    cashflow = account.get("cashflow", {})
    income_prior = int(cashflow.get("income_prior_avg", 30000))
    income_last30 = int(cashflow.get("income_last30", 30000))
    bounced_60d = int(cashflow.get("bounced_60d", 0))
    avg_balance_7d = int(cashflow.get("avg_balance_7d", 5000))
    
    emi = int(account.get("emi", 5000))
    dpd = int(account.get("dpd", 0))
    days_to_emi = int(account.get("days_to_emi", 15))
    legal_hold = bool(account.get("legal_hold", False))

    factors = []
    total_points = 0

    # 1. Income Drop Points: min(40, floor(income_drop_pct * 0.7))
    if income_prior > 0:
        income_drop_pct = round(max(0, (income_prior - income_last30) / income_prior * 100))
    else:
        income_drop_pct = 0

    if income_drop_pct > 0:
        pts = min(40, math.floor(income_drop_pct * 0.7))
        if pts > 0:
            factors.append({
                "name": "Income drop",
                "points": pts,
                "note": f"Income fell {income_drop_pct}% against prior 3-month average."
            })
            total_points += pts

    # 2. Bounced Debits: min(25, bounced_60d * 13)
    if bounced_60d > 0:
        pts = min(25, bounced_60d * 13)
        factors.append({
            "name": "Bounced debits",
            "points": pts,
            "note": f"{bounced_60d} automated debit bounces in past 60 days."
        })
        total_points += pts

    # 3. Balance Buffer: buffer_ratio = avg_balance_7d / emi
    buffer_ratio = (avg_balance_7d / emi) if emi > 0 else 1.0
    buffer_pts = 0
    if buffer_ratio < 0.25:
        buffer_pts = 20
    elif buffer_ratio < 0.5:
        buffer_pts = 12
    elif buffer_ratio < 1.0:
        buffer_pts = 6

    if buffer_pts > 0:
        factors.append({
            "name": "Balance buffer",
            "points": buffer_pts,
            "note": f"7-day average balance ₹{avg_balance_7d:,} is {buffer_ratio:.0%} of monthly EMI."
        })
        total_points += buffer_pts

    # 4. EMI Proximity
    proximity_pts = 0
    if buffer_ratio < 1.0:
        if days_to_emi <= 7:
            proximity_pts = 10
        elif days_to_emi <= 14:
            proximity_pts = 5

    if proximity_pts > 0:
        factors.append({
            "name": "EMI proximity",
            "points": proximity_pts,
            "note": f"Next instalment due in {days_to_emi} days with low balance buffer."
        })
        total_points += proximity_pts

    # 5. Days Past Due
    dpd_pts = 0
    if dpd >= 15:
        dpd_pts = 10
    elif dpd >= 1:
        dpd_pts = 5

    if dpd_pts > 0:
        factors.append({
            "name": "Days past due",
            "points": dpd_pts,
            "note": f"Account currently {dpd} days past due."
        })
        total_points += dpd_pts

    # Legal Hold Flag Note
    if legal_hold:
        factors.append({
            "name": "Legal dispute hold",
            "points": 0,
            "note": "Account has an active legal hold or court dispute notice."
        })

    # Final Score and Tier
    final_score = min(100, total_points)
    if final_score >= 60:
        tier = "HIGH"
    elif final_score >= 35:
        tier = "WATCH"
    else:
        tier = "LOW"

    return final_score, tier, factors
