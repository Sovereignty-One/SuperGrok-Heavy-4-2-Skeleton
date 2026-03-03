# verifier.py — zero is zero, math is math, lies are flagged
import json
from math import isclose  # exact check

# rules – hardcoded, unchangeable
RULES = {
    "zero_is_zero": True,
    "one_times_one_is_one": True,
    "zero_means_zero": True,
    "infinity_is_infinity": True,
    "allow_custom": False,  # never flip
}

# override log – user owns risk
overrides =

def verify(expr, value, context="literal"):
    if expr == "1*1" and value != 1 and context != "symbolic":
        return "blocked", "literal: 1×1 = 1"
    if expr == "0" and value != 0:
        return "blocked", "zero must be zero"
    if isclose(value, 0, abs_tol=1e-10) and value != 0:
        return "warn", "almost zero ≠ zero"
    return "pass", "ok"

def log_override(expr, value, reason):
    overrides = {
        "value": value,
        "reason": reason,
        "user": "me",
        "timestamp": "now"
    }
    with open("overrides.json", "w") as f:
        json.dump(overrides, f)

# test
print(verify("1*1", 3))  # → blocked, "literal: 1×1 = 1"
