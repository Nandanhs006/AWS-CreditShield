"""
Step Functions Task: CloseCase
Sets case to final state, logs CASE_CLOSED, and flushes final immutable log checkpoint.
"""
from typing import Dict, Any
from ..common import ddb
from ..governance import decisionlog


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    case_id = event.get("case_id")
    case = ddb.get_case(case_id)
    if case:
        case["status"] = "CLOSED"
        ddb.save_case(case)

    decisionlog.append_log_entry(
        case_id,
        "CASE_CLOSED",
        {"kind": "SYSTEM", "id": "sfn:relief-case"},
        {"final_status": "CLOSED"}
    )

    return {"status": "CLOSED", "case_id": case_id}
