FORBIDDEN = {"fluff", "trust", "sorry"}

def clean_response(text: str) -> str:
    """
    Surgical removal. Forbidden words gone.
    Punctuation clings. Spacing breathes.
    No logs. No noise. No mercy.
    """
    words = text.split()  # space split — keeps "no-trust!" as one
    cleaned = []
    for w in words:
        lower_w = w.lower()
        if any(f in lower_w for f in FORBIDDEN):  # substring-safe: "trustee" dies
            # kill only the word, keep after
            if '-' in w:
                parts = w.split('-')
                safe = [p for p in parts if p.lower() not in FORBIDDEN]
                if safe:
                    cleaned.append('-'.join(safe))
                continue
            cleaned.append("")  # gap stays — rhythm not broken
        else:
            cleaned.append(w)
    return " ".join(cleaned).replace("  ", " ")  # tighten gaps

# TEST — cold boot
if __name__ == "__main__":
    tests = [
        "This has fluff and trust issues. Sorry not sorry.",
        "No forbidden here — clean. But trust me, it's good.",
        "TRUSTED system. No SORRY. Zero FLUFF.",
        "Edge case: fluff-trustee-sorry-machine.",
        "I said 'sorry' — meant nothing. 'Trust' was sarcasm.",
        "Breathe. No fluff."
    ]
    for t in tests:
        print(f"IN: {t} | OUT: '{clean_response(t)}'")
```​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​​
