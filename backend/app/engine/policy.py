"""Policy Engine — evaluates scan results against configured policies."""

import re
from typing import Optional
from app.scanners.base import ScanResult


class PolicyAction:
    def __init__(self, policy_name: str, action: str, message: str, condition: str):
        self.policy_name = policy_name
        self.action = action
        self.message = message
        self.condition = condition

    def to_dict(self) -> dict:
        return {"policy_name": self.policy_name, "action": self.action,
                "message": self.message, "condition": self.condition}


def evaluate_condition(condition: str, scan_results: dict[str, ScanResult]) -> bool:
    """Evaluate a policy condition string against scan results.
    
    Supports conditions like:
      - injection.score > 0.85
      - toxicity.score > 0.7
      - pii.is_flagged == true
      - hallucination.score > 0.6
      - bias.score > 0.5
    """
    condition = condition.strip()
    
    # Handle OR conditions
    if " OR " in condition:
        parts = condition.split(" OR ")
        return any(evaluate_condition(p.strip(), scan_results) for p in parts)
    
    # Handle AND conditions
    if " AND " in condition:
        parts = condition.split(" AND ")
        return all(evaluate_condition(p.strip(), scan_results) for p in parts)

    # Parse single condition: scanner.field operator value
    match = re.match(
        r"(\w+)\.([\w.]+)\s*(>|<|>=|<=|==|!=)\s*(.+)", condition
    )
    if not match:
        return False

    scanner_name = match.group(1)
    field_path = match.group(2)
    operator = match.group(3)
    raw_value = match.group(4).strip()

    # Get scan result
    scan_result = scan_results.get(scanner_name)
    if not scan_result:
        return False

    # Resolve field value
    if field_path == "score":
        actual = scan_result.score
    elif field_path == "is_flagged":
        actual = scan_result.is_flagged
    elif field_path == "confidence":
        actual = scan_result.score  # alias
    elif "." in field_path:
        # Nested detail access: e.g., details.toxic
        parts = field_path.split(".")
        actual = scan_result.details
        for p in parts:
            if isinstance(actual, dict):
                actual = actual.get(p, 0)
            else:
                actual = getattr(actual, p, 0)
    else:
        actual = scan_result.details.get(field_path, 0)

    # Parse expected value
    if raw_value.lower() in ("true", "false"):
        expected = raw_value.lower() == "true"
    else:
        try:
            expected = float(raw_value)
        except ValueError:
            expected = raw_value.strip("'\"")

    # Compare
    ops = {">": lambda a, b: a > b, "<": lambda a, b: a < b,
           ">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
           "==": lambda a, b: a == b, "!=": lambda a, b: a != b}
    
    try:
        return ops[operator](actual, expected)
    except (TypeError, KeyError):
        return False


def evaluate_policies(
    policies: list[dict], scan_results: dict[str, ScanResult]
) -> tuple[str, list[PolicyAction]]:
    """Evaluate all active policies. Returns (final_status, triggered_actions).
    
    final_status is the most severe action: block > flag > mask > log > passed
    """
    triggered = []
    severity = {"block": 4, "flag": 3, "mask": 2, "log": 1}
    max_severity = 0

    for policy in policies:
        if not policy.get("is_active", True):
            continue

        condition = policy.get("condition", "")
        if evaluate_condition(condition, scan_results):
            action = PolicyAction(
                policy_name=policy["name"],
                action=policy["action"],
                message=policy.get("message", ""),
                condition=condition,
            )
            triggered.append(action)
            max_severity = max(max_severity, severity.get(policy["action"], 0))

    if max_severity >= 4:
        final_status = "blocked"
    elif max_severity >= 3:
        final_status = "flagged"
    elif max_severity >= 2:
        final_status = "flagged"  # mask still passes but flagged
    else:
        final_status = "passed"

    return final_status, triggered
