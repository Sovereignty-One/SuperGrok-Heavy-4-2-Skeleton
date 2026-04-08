import datetime
import uuid
import ast
import csv

def is_code_clean(code_snippet: str) -> bool:
    """Check if the Python snippet is syntactically valid."""
    try:
        ast.parse(code_snippet)
        return True
    except SyntaxError:
        return False

def ai_feedback_on_code(is_clean: bool, log_file: str, session_id: str):
    """Provide feedback based on code cleanliness and log the result."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if is_clean:
        feedback = "✅ Great job! Your code is clean and syntactically correct."
        suggestion = "💡 Suggestions: Consider adding safety checks or optimizations for stability."
    else:
        feedback = "⚠️ The code could use improvements."
        suggestion = "💡 Suggestions: Work on readability, error handling, and security measures."

    print(feedback)
    print(suggestion)

    with open(log_file, "a") as f:
        f.write(f"[{{timestamp}}] [Session: {{session_id}}] {{feedback}} {{suggestion}}\n")

def log_session_summary(log_file: str, summary_file: str, csv_file: str,
                        session_id: str, positive: int, negative: int,
                        total_length: int, submissions: int) -> str:
    """Record a session summary in log, summary, and CSV files."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    avg_length = total_length / submissions if submissions else 0

    summary = (
        f"\n=== Session Summary [{{session_id}}] @ {{timestamp}} ===\n"
        f"Positive feedbacks: {{positive}}\n"
        f"Negative feedbacks: {{negative}}\n"
        f"Total submissions: {{submissions}}\n"
        f"Average code length: {{avg_length:.2f}} characters\n"
        "===============================\n"
    )

    with open(log_file, "a") as f:
        f.write(summary)
    with open(summary_file, "a") as f:
        f.write(summary)
    with open(csv_file, "a", newline="") as f:
        csv.writer(f).writerow([session_id, timestamp, positive, negative, submissions, f"{{avg_length:.2f}}"])

    return summary

def search_previous_summaries(log_file: str):
    """Display lines from log that look like session summaries."""
    print("\n=== Previous Session Summaries ===")
    try:
        with open(log_file, "r") as f:
            for line in f:
                if line.startswith("=== Session Summary") or any(
                    line.startswith(prefix) for prefix in ["Positive", "Negative", "Total", "Average"]):
                    print(line.strip())
    except FileNotFoundError:
        print("No previous logs found.")

def main():
    print("👋 Welcome to the AI Code Feedback Tool!")

    session_id = str(uuid.uuid4())[:8]
    log_file = input("Enter log filename (e.g., feedback_log.txt): ").strip() or "feedback_log.txt"
    summary_file = input("Enter summary filename (e.g., summary_log.txt): ").strip() or "summary_log.txt"
    csv_file = input("Enter CSV filename (e.g., summary_log.csv): ").strip() or "summary_log.csv"

    positive = 0
    negative = 0
    total_length = 0
    submissions = 0

    while True:
        code_snippet = input("Enter your Python code snippet (or 'quit' to exit): ").strip()
        if code_snippet.lower() == 'quit':
            break
        is_clean = is_code_clean(code_snippet)
        ai_feedback_on_code(is_clean, log_file, session_id)
        if is_clean:
            positive += 1
        else:
            negative += 1
        total_length += len(code_snippet)
        submissions += 1

    if submissions > 0:
        log_session_summary(log_file, summary_file, csv_file, session_id, positive, negative, total_length, submissions)
    search_previous_summaries(log_file)

if __name__ == "__main__":
    main()