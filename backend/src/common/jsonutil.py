"""
CreditShield JSON Utilities
Handles Decimal normalization and canonical serialization for SHA-256 hashing.
"""
import json
from decimal import Decimal
from datetime import datetime, date


def normalize(obj):
    """
    Recursively normalize objects from DynamoDB or Python types:
    - Decimal with no fractional part -> int
    - Decimal with fractional part -> float
    - datetime / date -> ISO 8601 string
    - dict -> normalized dict
    - list / tuple / set -> normalized list
    """
    if isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [normalize(item) for item in obj]
    return obj


def dumps(obj, **kwargs) -> str:
    """Standard JSON serializer with Decimal normalization."""
    return json.dumps(normalize(obj), **kwargs)


def canonical_dumps(obj) -> str:
    """
    Canonical JSON serialization for cryptographic hash chaining:
    - Keys sorted
    - Compact separators (no whitespace)
    - UTF-8 compatible
    """
    return json.dumps(normalize(obj), sort_keys=True, separators=(",", ":"))


def loads(s: str):
    """Standard JSON deserializer."""
    return json.loads(s)
