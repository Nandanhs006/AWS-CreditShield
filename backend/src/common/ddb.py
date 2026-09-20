"""
CreditShield DynamoDB Client & Storage Adapters
"""
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from . import config
from . import jsonutil

_dynamodb = None


def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", region_name=config.AWS_REGION)
    return _dynamodb


# =============================================================================
# ACCOUNTS
# =============================================================================
def get_account(account_id: str) -> Optional[Dict[str, Any]]:
    table = get_dynamodb().Table(config.TABLE_ACCOUNTS)
    res = table.get_item(Key={"account_id": account_id})
    item = res.get("Item")
    return jsonutil.normalize(item) if item else None


def save_account(account: Dict[str, Any]):
    table = get_dynamodb().Table(config.TABLE_ACCOUNTS)
    table.put_item(Item=jsonutil.normalize(account))


def list_accounts() -> List[Dict[str, Any]]:
    table = get_dynamodb().Table(config.TABLE_ACCOUNTS)
    res = table.scan()
    return jsonutil.normalize(res.get("Items", []))


# =============================================================================
# CASES
# =============================================================================
def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    table = get_dynamodb().Table(config.TABLE_CASES)
    res = table.get_item(Key={"case_id": case_id})
    item = res.get("Item")
    return jsonutil.normalize(item) if item else None


def save_case(case: Dict[str, Any]):
    table = get_dynamodb().Table(config.TABLE_CASES)
    case["updated_at"] = datetime.now(timezone.utc).isoformat()
    table.put_item(Item=jsonutil.normalize(case))


def get_case_by_token(token: str) -> Optional[Dict[str, Any]]:
    table = get_dynamodb().Table(config.TABLE_CASES)
    res = table.query(
        IndexName="by_token",
        KeyConditionExpression=Key("borrower_token").eq(token)
    )
    items = res.get("Items", [])
    return jsonutil.normalize(items[0]) if items else None


def list_cases() -> List[Dict[str, Any]]:
    table = get_dynamodb().Table(config.TABLE_CASES)
    res = table.scan()
    return jsonutil.normalize(res.get("Items", []))


# =============================================================================
# MESSAGES
# =============================================================================
def append_message(case_id: str, role: str, text: str, **kwargs) -> Dict[str, Any]:
    table = get_dynamodb().Table(config.TABLE_MESSAGES)
    now = datetime.now(timezone.utc).isoformat()
    ts_id = f"{now}#{kwargs.get('msg_id', 'm0')}"
    item = {
        "case_id": case_id,
        "ts_id": ts_id,
        "role": role,
        "text": text,
        "timestamp": now,
        **kwargs
    }
    table.put_item(Item=jsonutil.normalize(item))
    return jsonutil.normalize(item)


def get_case_messages(case_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    table = get_dynamodb().Table(config.TABLE_MESSAGES)
    res = table.query(
        KeyConditionExpression=Key("case_id").eq(case_id),
        ScanIndexForward=True,
        Limit=limit
    )
    return jsonutil.normalize(res.get("Items", []))


# =============================================================================
# APPROVALS
# =============================================================================
def create_approval(approval_item: Dict[str, Any]):
    table = get_dynamodb().Table(config.TABLE_APPROVALS)
    table.put_item(Item=jsonutil.normalize(approval_item))


def get_approval(approval_id: str) -> Optional[Dict[str, Any]]:
    table = get_dynamodb().Table(config.TABLE_APPROVALS)
    res = table.get_item(Key={"approval_id": approval_id})
    item = res.get("Item")
    return jsonutil.normalize(item) if item else None


def update_approval(approval_id: str, status: str, decided_by: str, note: str = ""):
    table = get_dynamodb().Table(config.TABLE_APPROVALS)
    now = datetime.now(timezone.utc).isoformat()
    table.update_item(
        Key={"approval_id": approval_id},
        UpdateExpression="SET #s = :s, decided_by = :db, decided_at = :da, decision_note = :dn",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": status,
            ":db": decided_by,
            ":da": now,
            ":dn": note
        }
    )


def list_pending_approvals() -> List[Dict[str, Any]]:
    table = get_dynamodb().Table(config.TABLE_APPROVALS)
    try:
        res = table.query(
            IndexName="by_status",
            KeyConditionExpression=Key("status").eq("PENDING")
        )
        return jsonutil.normalize(res.get("Items", []))
    except Exception:
        # Fallback to scan if GSI is still indexing
        res = table.scan(FilterExpression=Attr("status").eq("PENDING"))
        return jsonutil.normalize(res.get("Items", []))


# =============================================================================
# DECISION LOG
# =============================================================================
def get_case_log_entries(case_id: str) -> List[Dict[str, Any]]:
    table = get_dynamodb().Table(config.TABLE_LOG)
    res = table.query(
        KeyConditionExpression=Key("case_id").eq(case_id),
        ScanIndexForward=True
    )
    return jsonutil.normalize(res.get("Items", []))


def put_raw_log_entry(entry: Dict[str, Any]):
    table = get_dynamodb().Table(config.TABLE_LOG)
    table.put_item(Item=jsonutil.normalize(entry))
