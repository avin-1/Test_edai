import os
import json

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "input")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

# The name of the file we expect from the matching agent
INPUT_FILENAME = "ranked_candidates.json"
OUTPUT_FILENAME = "final_shortlist.json"

# Shortlisting Criteria
SCORE_THRESHOLD = 0.1 # Minimum final_match_score to be considered
TOP_N = 5 # Maximum number of candidates to shortlist

# --- Helper Functions ---

def load_ranked_candidates():
    """Loads the ranked candidate list from the input directory."""
    input_file = os.path.join(INPUT_DIR, INPUT_FILENAME)
    if not os.path.exists(input_file):
        print(f"Error: Input file not found at {input_file}")
        return None
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading or parsing JSON file {input_file}: {e}")
        return None

def generate_explanation(candidate):
    """Generates a simple explanation for why a candidate was shortlisted."""
    explanation = f"Strong candidate with a final match score of {candidate['final_match_score']:.2f}. "

    if candidate['semantic_match_score'] > 0.5:
        explanation += f"Excellent semantic alignment ({candidate['semantic_match_score']:.2f}) on experience. "
    elif candidate['semantic_match_score'] > 0.2:
        explanation += f"Good semantic alignment ({candidate['semantic_match_score']:.2f}) on experience. "

    if candidate['keyword_match_score'] > 0.5:
        explanation += f"Matches a high number of key skills ({candidate['keyword_match_score']:.2f})."
    elif candidate['keyword_match_score'] > 0.1:
        explanation += f"Matches several key skills ({candidate['keyword_match_score']:.2f})."

    if candidate['final_match_score'] < 0.2:
         explanation += "Considered a potential fit despite a lower overall score."

    return explanation.strip()

# --- Main Orchestration ---

def run_shortlisting_pipeline(ranked_candidates):
    """
    Runs the candidate shortlisting process on the given data.
    Accepts a ranked list and returns a final, explained shortlist.
    """
    print("Running candidate shortlisting pipeline...")
    if ranked_candidates is None:
        print("No ranked candidates provided.")
        return []

    # Filter candidates by score threshold
    filtered_candidates = [
        c for c in ranked_candidates if c.get('final_match_score', 0) >= SCORE_THRESHOLD
    ]
    print(f"  - Found {len(filtered_candidates)} candidates above the score threshold of {SCORE_THRESHOLD}.")

    # Take the top N candidates
    shortlisted_candidates = filtered_candidates[:TOP_N]
    print(f"  - Selected the top {len(shortlisted_candidates)} candidates for the final shortlist.")

    # Generate explanations
    final_shortlist = []
    for candidate in shortlisted_candidates:
        candidate['explanation'] = generate_explanation(candidate)
        final_shortlist.append(candidate)

    print(f"Successfully created a shortlist of {len(final_shortlist)} candidates.")
    return final_shortlist

def main_file_based():
    """
    Original main function for running the agent from a file.
    """
    print("Starting Candidate Shortlisting Agent (File-based)...")
    ranked_candidates = load_ranked_candidates()
    final_shortlist = run_shortlisting_pipeline(ranked_candidates)

    if final_shortlist:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_shortlist, f, indent=4)
            print(f"Successfully saved final shortlist to {output_path}")
        except IOError as e:
            print(f"Error saving final shortlist to {output_path}: {e}")

if __name__ == "__main__":
    main_file_based()
