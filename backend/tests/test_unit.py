"""
CreditShield Unit Tests (pytest)
Tests deterministic scoring, arithmetic, verifier, and hash chaining without external AWS dependencies.
"""
import pytest
import hashlib
from backend.src.domain import stress
from backend.src.domain import plan
from backend.src.governance import verifier
from backend.src.governance import authorize
from backend.src.governance import decisionlog
from backend.src.common import jsonutil


# 1. TEST HERO ACCOUNTS STRESS SCORING (Section 7 specs)
def test_hero_stress_scoring():
    meera = {
        "account_id": "ACC-1001",
        "emi": 6200,
        "dpd": 0,
        "days_to_emi": 6,
        "cashflow": {
            "income_prior_avg": 28000,
            "income_last30": 12500,
            "bounced_60d": 1,
            "avg_balance_7d": 2100
        }
    }
    score_meera, tier_meera, _ = stress.calculate_stress_score(meera)
    assert score_meera == 73
    assert tier_meera == "HIGH"

    arjun = {
        "account_id": "ACC-1002",
        "emi": 14500,
        "dpd": 9,
        "days_to_emi": 3,
        "cashflow": {
            "income_prior_avg": 62000,
            "income_last30": 31000,
            "bounced_60d": 2,
            "avg_balance_7d": 3800
        }
    }
    score_arjun, tier_arjun, _ = stress.calculate_stress_score(arjun)
    assert score_arjun == 87
    assert tier_arjun == "HIGH"

    sana = {
        "account_id": "ACC-1003",
        "emi": 9800,
        "dpd": 35,
        "days_to_emi": 20,
        "cashflow": {
            "income_prior_avg": 45000,
            "income_last30": 31500,
            "bounced_60d": 2,
            "avg_balance_7d": 5000
        }
    }
    score_sana, tier_sana, _ = stress.calculate_stress_score(sana)
    assert score_sana == 62
    assert tier_sana == "HIGH"

    vikram = {
        "account_id": "ACC-1004",
        "emi": 11000,
        "dpd": 20,
        "days_to_emi": 5,
        "legal_hold": True,
        "cashflow": {
            "income_prior_avg": 52000,
            "income_last30": 30000,
            "bounced_60d": 1,
            "avg_balance_7d": 4000
        }
    }
    score_vikram, tier_vikram, _ = stress.calculate_stress_score(vikram)
    assert score_vikram == 74
    assert tier_vikram == "HIGH"


# 2. TEST DETERMINISTIC PLAN SUMMARIES (Section 9.6)
def test_plan_summaries():
    account = {"emi": 6200, "next_due_date": "2026-09-26"}
    summary_shift = plan.generate_plan_summary("DUE_DATE_SHIFT", {"days": 7}, account)
    assert "Move your next EMI from 26 Sep to 03 Oct 2026" in summary_shift

    summary_partial = plan.generate_plan_summary("PARTIAL_PLAN", {"upfront_pct": 50, "installments": 3}, account)
    assert "Pay ₹3,100 on the due date" in summary_partial
    assert "spread across your next 3 EMIs" in summary_partial

    summary_waiver = plan.generate_plan_summary("FEE_WAIVER", {"amount": 350}, account)
    assert "Waive ₹350 of late fees" in summary_waiver


# 3. TEST NUMERIC VERIFIER (Section 9.5)
def test_numeric_verifier():
    allowed = {6200, 7, 88000, 350, 26, 3, 2026}
    
    valid_text = "Your EMI of ₹6,200 can be moved by 7 days to 3 Oct 2026."
    ok, offending = verifier.verify_agent_reply(valid_text, allowed)
    assert ok is True
    assert len(offending) == 0

    hallucinated_text = "I can waive ₹95000 and extend your loan by 48 months."
    ok, offending = verifier.verify_agent_reply(hallucinated_text, allowed)
    assert ok is False
    assert 95000 in offending or 48 in offending


# 4. TEST CEDAR COMPLETE 15-ROW AUTHORIZATION MATRIX (Section 8.6)
def test_cedar_complete_15_matrix():
    meera = {"account_id": "ACC-1001", "dpd": 0, "prior_reliefs": 0, "legal_hold": False, "emi": 6200, "outstanding": 88000}
    arjun = {"account_id": "ACC-1002", "dpd": 9, "prior_reliefs": 1, "legal_hold": False, "emi": 14500, "outstanding": 310000}
    sana  = {"account_id": "ACC-1003", "dpd": 35, "prior_reliefs": 2, "legal_hold": False, "emi": 9800, "outstanding": 210000}
    vikram = {"account_id": "ACC-1004", "dpd": 20, "prior_reliefs": 1, "legal_hold": True, "emi": 11000, "outstanding": 260000}

    # Row 1: Meera DUE_DATE_SHIFT days=7 -> ALLOWED
    assert authorize.authorize_relief(meera, "DUE_DATE_SHIFT", {"days": 7})["outcome"] == "ALLOWED"
    # Row 2: Meera DUE_DATE_SHIFT days=14 -> NEEDS_MANAGER_APPROVAL
    assert authorize.authorize_relief(meera, "DUE_DATE_SHIFT", {"days": 14})["outcome"] == "NEEDS_MANAGER_APPROVAL"
    # Row 3: Meera DUE_DATE_SHIFT days=45 -> DENIED
    assert authorize.authorize_relief(meera, "DUE_DATE_SHIFT", {"days": 45})["outcome"] == "DENIED"
    # Row 4: Meera PARTIAL_PLAN 50%, 3 installments -> ALLOWED
    assert authorize.authorize_relief(meera, "PARTIAL_PLAN", {"upfront_pct": 50, "installments": 3})["outcome"] == "ALLOWED"
    # Row 5: Meera PARTIAL_PLAN 25%, 6 installments -> NEEDS_MANAGER_APPROVAL
    assert authorize.authorize_relief(meera, "PARTIAL_PLAN", {"upfront_pct": 25, "installments": 6})["outcome"] == "NEEDS_MANAGER_APPROVAL"
    # Row 6: Meera TENURE_EXTENSION months=3 -> ALLOWED
    assert authorize.authorize_relief(meera, "TENURE_EXTENSION", {"months": 3})["outcome"] == "ALLOWED"
    # Row 7: Meera TENURE_EXTENSION months=9 -> DENIED
    assert authorize.authorize_relief(meera, "TENURE_EXTENSION", {"months": 9})["outcome"] == "DENIED"
    # Row 8: Meera FEE_WAIVER amount=350 -> ALLOWED
    assert authorize.authorize_relief(meera, "FEE_WAIVER", {"amount": 350})["outcome"] == "ALLOWED"
    # Row 9: Arjun DUE_DATE_SHIFT days=30 -> NEEDS_MANAGER_APPROVAL
    assert authorize.authorize_relief(arjun, "DUE_DATE_SHIFT", {"days": 30})["outcome"] == "NEEDS_MANAGER_APPROVAL"
    # Row 10: Arjun TENURE_EXTENSION months=2 -> NEEDS_MANAGER_APPROVAL
    assert authorize.authorize_relief(arjun, "TENURE_EXTENSION", {"months": 2})["outcome"] == "NEEDS_MANAGER_APPROVAL"
    # Row 11: Arjun FEE_WAIVER amount=1200 -> NEEDS_MANAGER_APPROVAL
    assert authorize.authorize_relief(arjun, "FEE_WAIVER", {"amount": 1200})["outcome"] == "NEEDS_MANAGER_APPROVAL"
    # Row 12: Sana DUE_DATE_SHIFT days=5 -> NEEDS_MANAGER_APPROVAL
    assert authorize.authorize_relief(sana, "DUE_DATE_SHIFT", {"days": 5})["outcome"] == "NEEDS_MANAGER_APPROVAL"
    # Row 13: Sana TENURE_EXTENSION months=24 -> DENIED
    assert authorize.authorize_relief(sana, "TENURE_EXTENSION", {"months": 24})["outcome"] == "DENIED"
    # Row 14: Sana TENURE_EXTENSION months=3 -> DENIED (prior_reliefs >= 2)
    assert authorize.authorize_relief(sana, "TENURE_EXTENSION", {"months": 3})["outcome"] == "DENIED"
    # Row 15: Vikram DUE_DATE_SHIFT days=3 -> DENIED (legal hold)
    assert authorize.authorize_relief(vikram, "DUE_DATE_SHIFT", {"days": 3})["outcome"] == "DENIED"


# 5. TEST CRYPTOGRAPHIC HASH CHAIN
def test_hash_chain_computation():
    payload = {"account_id": "ACC-1001", "score": 73}
    h1 = decisionlog.compute_entry_hash(
        "CASE-1001", 1, "2026-09-20T05:00:00Z", "STRESS_FLAGGED", "SYSTEM:lambda",
        "0" * 64, payload
    )
    assert len(h1) == 64
    # Deterministic check
    h2 = decisionlog.compute_entry_hash(
        "CASE-1001", 1, "2026-09-20T05:00:00Z", "STRESS_FLAGGED", "SYSTEM:lambda",
        "0" * 64, payload
    )
    assert h1 == h2


# 6. TEST SIMULATED CORE BANKING ADAPTER
def test_core_banking_adapter():
    from backend.src.domain.adapters import SimulatedCoreBanking
    adapter = SimulatedCoreBanking()
    case = {"account_id": "ACC-1001", "case_id": "CASE-1001"}
    plan_dict = {
        "plan_id": "PLAN-1001-01",
        "action": "DUE_DATE_SHIFT",
        "params": {"days": 7}
    }
    ok, changes = adapter.apply_plan(case, plan_dict)
    assert ok is True
    assert "next_due_date" in changes
    assert changes["next_due_date"]["new"] == "2026-10-03"
    assert changes["prior_reliefs"]["new"] == 1


# 7. TEST COGNITO AUTH TOKEN PARSER (List & String Bracket representations)
def test_auth_group_parsing():
    from backend.src.common import auth
    # Format 1: List of groups
    claims_list = {"cognito:groups": ["ops", "manager"], "email": "raman@harbourfin.com"}
    groups = auth.parse_groups(claims_list.get("cognito:groups"))
    assert "ops" in groups and "manager" in groups
    assert auth.is_manager(claims_list) is True
    assert auth.is_ops(claims_list) is True

    # Format 2: Bracketed string format produced by some API Gateway proxy setups
    claims_str = {"cognito:groups": "[ops]", "email": "analyst@harbourfin.com"}
    groups2 = auth.parse_groups(claims_str.get("cognito:groups"))
    assert "ops" in groups2
    assert auth.is_manager(claims_str) is False
    assert auth.is_ops(claims_str) is True


# 8. TEST GEMINI AGENT PROVIDER & CONVERSE DISPATCH
def test_gemini_agent_provider(monkeypatch):
    from backend.src.agent import gemini_agent
    from backend.src.common import ddb
    from backend.src.governance import decisionlog
    monkeypatch.setattr(ddb, "save_case", lambda case: None)
    monkeypatch.setattr(decisionlog, "append_log_entry", lambda *args, **kwargs: {"seq": 1})

    case = {"case_id": "CASE-1001", "status": "OPEN", "plan": None}
    account = {
        "account_id": "ACC-1001",
        "name": "Meera Iyer",
        "emi": 6200,
        "product": "TWO_WHEELER",
        "days_to_emi": 6,
        "dpd": 0,
        "prior_reliefs": 0,
        "legal_hold": False
    }
    # Test conversational turn in offline fallback mode
    reply, traces, plan = gemini_agent.run_gemini_turn(
        case, account, "Can I get a 7-day shift for my upcoming EMI?", "You are CreditShield Assistant."
    )
    assert "6,200" in reply or "7-day" in reply
    assert plan is not None
    assert plan["action"] == "DUE_DATE_SHIFT"
    assert plan["outcome"] == "ALLOWED"


# 9. TEST SNS & SQS MESSAGING PIPELINE (Manager Alert, Fan-out, Telemetry)
def test_sns_sqs_messaging_pipeline(monkeypatch):
    from backend.src.domain import messaging
    from backend.src.governance import decisionlog
    monkeypatch.setattr(decisionlog, "append_log_entry", lambda *args, **kwargs: {"seq": 99})

    plan = {
        "account_id": "ACC-1002",
        "borrower_name": "Arjun Mehta",
        "action": "DUE_DATE_SHIFT",
        "params": {"days": 30},
        "summary": "Move next EMI of ₹14,500 by 30 days"
    }

    # 1. SNS Manager Alert publish
    alert = messaging.publish_manager_approval_alert("CASE-1002", plan, "task-token-xyz-123456789")
    assert alert["case_id"] == "CASE-1002"
    assert "status" in alert
    assert "sns" in alert["message_id"]

    # 2. SNS Fan-Out to CoreBanking and Borrower queues
    fanout = messaging.fan_out_relief_event("CASE-1002", {"account_id": "ACC-1002"}, plan, "APPROVED")
    assert "CoreBankingSyncQueue" in fanout["target_queues"]
    assert "BorrowerCommQueue" in fanout["target_queues"]

    # 3. SQS Telemetry Ingestion Buffer
    telemetry = messaging.buffer_telemetry_event({
        "account_id": "ACC-1001",
        "balance_buffer": 0.18,
        "bounced_debits_60d": 1
    })
    assert telemetry["account_id"] == "ACC-1001"
    assert telemetry["status"] in ("BUFFERED", "SIMULATED_BUFFERED")



