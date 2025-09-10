import os
import datetime

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
LOG_FILE = os.path.join(OUTPUT_DIR, "feedback.log")

def log_feedback(candidate_name, job_title, feedback_type):
    """
    Simulates collecting feedback by writing to a log file.
    'feedback_type' should be 'positive' or 'negative'.
    """
    print(f"Logging '{feedback_type}' feedback for {candidate_name} for job '{job_title}'")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = (
        f"[{timestamp}] - Candidate '{candidate_name}' received {feedback_type} "
        f"feedback for the position of '{job_title}'.\n"
    )

    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message)
        print(f"Successfully logged feedback to {LOG_FILE}")
        return True
    except IOError as e:
        print(f"Error writing to log file {LOG_FILE}: {e}")
        return False

if __name__ == '__main__':
    print("Running feedback agent in standalone test mode...")
    log_feedback("Jane Smith", "Product Manager", "positive")
    log_feedback("Bob Johnson", "Data Analyst", "negative")
