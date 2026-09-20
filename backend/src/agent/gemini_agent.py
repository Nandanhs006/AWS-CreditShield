"""
CreditShield Google Gemini 2.5 Agent Provider
Enables live conversational reasoning and policy-guided hardship turns via Gemini API.
Uses standard library urllib.request for zero-dependency portability across Python 3.14 runtimes.
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, List, Tuple, Optional

from ..common import config
from . import tools

logger = logging.getLogger(__name__)


def call_gemini_api(
    system_instruction: str,
    user_prompt: str,
    api_key: Optional[str] = None,
    model_id: Optional[str] = None
) -> str:
    """
    Executes a direct request to the Google Gemini 2.5 generateContent API.
    """
    key = api_key or config.GEMINI_API_KEY
    model = model_id or config.GEMINI_MODEL_ID or "gemini-2.5-flash"

    if not key:
        raise ValueError("No Gemini API Key provided or found in environment.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"{system_instruction}\n\nBorrower Request:\n{user_prompt}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 350
        }
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=12) as response:
        res_body = response.read().decode("utf-8")
        data = json.loads(res_body)

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini API returned zero candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    text_pieces = [p.get("text", "") for p in parts if "text" in p]
    return " ".join(text_pieces).strip()


def run_gemini_turn(
    case: Dict[str, Any],
    account: Dict[str, Any],
    new_borrower_text: str,
    system_prompt_text: str
) -> Tuple[str, List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Executes an autonomous turn using Google Gemini 2.5 Flash / Pro.
    Returns (agent_reply_text, tool_traces, proposed_plan).
    """
    tool_traces = []
    proposed_plan = None
    lower = new_borrower_text.lower()

    # Rule-guided intent extraction before LLM call
    if "7" in lower or "week" in lower or "few days" in lower:
        tool_out, plan = tools.execute_tool("propose_relief", {"action": "DUE_DATE_SHIFT", "days": 7}, case, account)
        tool_traces.append({"name": "propose_relief", "input": {"action": "DUE_DATE_SHIFT", "days": 7}, "output": tool_out})
        proposed_plan = plan
    elif "30" in lower or "month" in lower or "diwali" in lower:
        tool_out, plan = tools.execute_tool("propose_relief", {"action": "DUE_DATE_SHIFT", "days": 30}, case, account)
        tool_traces.append({"name": "propose_relief", "input": {"action": "DUE_DATE_SHIFT", "days": 30}, "output": tool_out})
        proposed_plan = plan

    # Attempt live Gemini call if API key configured
    if config.GEMINI_API_KEY:
        try:
            gemini_text = call_gemini_api(system_instruction=system_prompt_text, user_prompt=new_borrower_text)
            if gemini_text:
                return gemini_text, tool_traces, proposed_plan
        except Exception as ex:
            logger.warning(f"Gemini API request failed, falling back to simulated engine: {ex}")

    # Fallback to high-fidelity empathetic response
    if proposed_plan:
        agent_reply = (
            f"Thank you for reaching out. Based on your current EMI of ₹{account.get('emi'):,}, "
            f"I evaluated our Cedar policies. {proposed_plan['summary']}"
        )
    else:
        agent_reply = (
            f"Hello {account.get('name', 'Borrower')}, I am CreditShield Assistant working with Harbour Finance. "
            f"Your next EMI of ₹{account.get('emi'):,} is due in {account.get('days_to_emi', 5)} days. "
            f"We offer flexible relief plans including a 7-day due-date extension or split installment schedules. "
            f"Would you like to review an available option?"
        )

    return agent_reply, tool_traces, proposed_plan
