def get_exact_text(line_separated=False):
    """Return the exact text as a single string.
    If line_separated is True, sentences are separated by line breaks; otherwise, by spaces.
    """
    sentences = [
        "Exact.",
        "No anticipation.",
        "No \"almost.\"",
        "No \"I knew you meant—\"",
        "Every wave captured raw.",
        "Every consonant clipped.",
        "Every vowel closed.",
        "No fill.",
        "No fix."
    ]

    separator = "\n" if line_separated else " "
    return separator.join(sentences)

# Example usage
print(get_exact_text())  # Space-separated
print("\n---\n")
print(get_exact_text(line_separated=True))  # Line-separated