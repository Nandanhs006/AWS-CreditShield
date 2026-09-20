"""
CreditShield Money Helpers
Enforces whole integer rupees. No floats in financial or policy logic.
"""


def format_inr(amount: int) -> str:
    """
    Format whole integer rupees in the Indian numbering format (e.g. 1,00,000).
    """
    if not isinstance(amount, (int, float)):
        return "₹0"
    val = int(amount)
    s = str(abs(val))
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted = ",".join(groups) + "," + last3
    
    return f"-₹{formatted}" if val < 0 else f"₹{formatted}"
