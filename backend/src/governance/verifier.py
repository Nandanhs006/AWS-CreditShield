"""
CreditShield Numeric Verifier
Enforces that no figure in an agent message is hallucinated or invented.
Every number must originate in tool results, case state, or borrower messages.
"""
import re
import unicodedata
from typing import Set, Dict, Any, List, Tuple


def extract_numbers(text: str) -> Set[int]:
    """
    Extracts all numeric tokens from text as integers,
    ignoring commas, currency symbols, and normalizing Unicode digits.
    """
    normalized = unicodedata.normalize("NFKC", text)
    cleaned = re.sub(r"[,₹$€£]", "", normalized)
    matches = re.findall(r"\b\d+\b", cleaned)
    return {int(m) for m in matches}


def build_allowed_numbers(case_state: Dict[str, Any], tool_traces: List[Dict[str, Any]], borrower_messages: List[str]) -> Set[int]:
    """
    Builds the complete set of authorized numbers from case state, tools, and user text.
    """
    allowed = set()

    # 1. From Case State
    for v in case_state.values():
        if isinstance(v, (int, float)):
            allowed.add(int(v))
        elif isinstance(v, str):
            allowed.update(extract_numbers(v))

    # 2. From Tool Traces
    for trace in tool_traces:
        out_str = str(trace.get("output", trace.get("output_summary", "")))
        allowed.update(extract_numbers(out_str))
        in_str = str(trace.get("input", ""))
        allowed.update(extract_numbers(in_str))

    # 3. From Borrower Messages
    for msg in borrower_messages:
        allowed.update(extract_numbers(msg))

    # 4. Standard conversational numbers (e.g. 1st, 2, 3 parts, 24/7)
    allowed.update({1, 2, 3, 4, 5, 6, 7, 10, 14, 21, 30})

    return allowed


def verify_agent_reply(reply_text: str, allowed_numbers: Set[int]) -> Tuple[bool, Set[int]]:
    """
    Verifies that all numbers in reply_text are within the allowed set.
    Returns: (is_valid: bool, offending_numbers: set)
    """
    found = extract_numbers(reply_text)
    offending = found - allowed_numbers
    return (len(offending) == 0), offending
