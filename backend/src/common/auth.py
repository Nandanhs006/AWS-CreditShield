"""
CreditShield Authentication & RBAC Utilities
Parses Cognito JWT claims and enforces group-based authorization.
"""
from typing import Set, Dict, Any, List, Optional


def parse_groups(raw_groups: Any) -> Set[str]:
    """
    Cognito groups can arrive in HTTP API JWT claims as:
    - A space-separated bracketed string: "[ops manager]"
    - A single string: "manager"
    - A JSON list: ["ops", "manager"]
    """
    if not raw_groups:
        return set()
    if isinstance(raw_groups, list):
        return set(raw_groups)
    if isinstance(raw_groups, str):
        cleaned = raw_groups.strip("[]'\" ").replace(",", " ")
        return {g.strip() for g in cleaned.split() if g.strip()}
    return set()


def get_user_claims(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract claims dictionary from API Gateway HTTP API proxy event."""
    try:
        return event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {}) or {}
    except Exception:
        return {}


def get_user_id(claims: Dict[str, Any]) -> str:
    """Extract Cognito sub or username."""
    return claims.get("sub") or claims.get("cognito:username") or "anonymous"


def get_user_email(claims: Dict[str, Any]) -> str:
    """Extract Cognito email."""
    return claims.get("email") or "unknown@harbourfin.com"


def has_group(claims: Dict[str, Any], group: str) -> bool:
    """Check if claims contain a specific group."""
    groups = parse_groups(claims.get("cognito:groups"))
    return group in groups


def is_manager(claims: Dict[str, Any]) -> bool:
    """Check if user has manager role."""
    groups = parse_groups(claims.get("cognito:groups"))
    return "manager" in groups or "CreditManagersGroup" in groups


def is_ops(claims: Dict[str, Any]) -> bool:
    """Check if user has ops role."""
    groups = parse_groups(claims.get("cognito:groups"))
    return "ops" in groups or "OperationsGroup" in groups or is_manager(claims)
