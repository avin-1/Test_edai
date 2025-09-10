import os
import datetime

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
LOG_FILE = os.path.join(OUTPUT_DIR, "interviews.log")

def schedule_interview(candidate_name, candidate_email, job_title):
    """
    Simulates scheduling an interview by writing to a log file.
    In a real application, this would integrate with a calendar API
    and an email service.
    """
    print(f"Simulating interview schedule for {candidate_name} for job '{job_title}'")

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = (
        f"[{timestamp}] - Simulated interview invitation sent to "
        f"{candidate_name} ({candidate_email}) for the position of '{job_title}'.\n"
    )

    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message)
        print(f"Successfully logged to {LOG_FILE}")
        return True
    except IOError as e:
        print(f"Error writing to log file {LOG_FILE}: {e}")
        return False

if __name__ == '__main__':
    # Example usage for standalone testing
    print("Running interview scheduling agent in standalone test mode...")
    test_candidate_name = "John Doe"
    test_candidate_email = "john.doe@example.com"
    test_job_title = "Senior Software Engineer"
    schedule_interview(test_candidate_name, test_candidate_email, test_job_title)
