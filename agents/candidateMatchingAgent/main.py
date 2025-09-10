import os
import json
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JOB_PROFILE_DIR = os.path.join(SCRIPT_DIR, "input/job_profiles")
CANDIDATE_PROFILES_DIR = os.path.join(SCRIPT_DIR, "input/candidate_profiles")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
MODEL_NAME = 'all-MiniLM-L6-v2' # A good starting model for semantic similarity

# Ensure directories exist
os.makedirs(JOB_PROFILE_DIR, exist_ok=True)
os.makedirs(CANDIDATE_PROFILES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load the sentence transformer model
print("Loading Sentence Transformer model...")
try:
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    # Exit if the model can't be loaded, as it's critical.
    exit()

# --- Helper Functions ---

def load_json_file(filepath):
    """Loads a single JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading or parsing JSON file {filepath}: {e}")
        return None

def get_job_profile():
    """Loads the first job profile found in the job profile directory."""
    files = [f for f in os.listdir(JOB_PROFILE_DIR) if f.endswith('.json')]
    if not files:
        print("No job profiles found in the directory.")
        return None
    return load_json_file(os.path.join(JOB_PROFILE_DIR, files[0]))

def get_candidate_profiles():
    """Loads all candidate profiles from the candidate profiles directory."""
    profiles = []
    files = [f for f in os.listdir(CANDIDATE_PROFILES_DIR) if f.endswith('.json')]
    for filename in files:
        profile_path = os.path.join(CANDIDATE_PROFILES_DIR, filename)
        profile = load_json_file(profile_path)
        if profile:
            # Add the original filename for reference
            profile['original_filename'] = filename
            profiles.append(profile)
    return profiles

# --- Matching Algorithms ---

def calculate_keyword_match_score(job_skills, candidate_skills):
    """
    Calculates a match score based on shared keywords (skills).
    Uses a simple intersection over union (Jaccard similarity) approach.
    """
    if not candidate_skills or not job_skills:
        return 0.0

    # Ensure skills are in a consistent format (lowercase list of strings)
    job_skills_set = set(skill.lower() for skill in job_skills)

    # Candidate skills might be in a nested dictionary
    candidate_skill_list = []
    if isinstance(candidate_skills, dict):
        for category in candidate_skills.values():
            if isinstance(category, list):
                candidate_skill_list.extend([skill.lower() for skill in category])
    elif isinstance(candidate_skills, list):
        candidate_skill_list = [skill.lower() for skill in candidate_skills]

    candidate_skills_set = set(candidate_skill_list)

    if not candidate_skills_set:
        return 0.0

    intersection = job_skills_set.intersection(candidate_skills_set)
    union = job_skills_set.union(candidate_skills_set)

    return len(intersection) / len(union) if union else 0.0

def calculate_semantic_match_score(job_desc, candidate_exp):
    """
    Calculates a semantic match score using sentence embeddings.
    Compares the job responsibilities with the candidate's work experience.
    """
    if not job_desc or not candidate_exp:
        return 0.0

    # Join lists of strings into single documents
    job_doc = " ".join(job_desc)

    # Candidate experience is a list of dicts, filter out empty ones
    candidate_docs = [" ".join(exp.get('responsibilities', [])) for exp in candidate_exp if exp.get('responsibilities')]

    if not candidate_docs:
        return 0.0

    # Create embeddings
    job_embedding = model.encode(job_doc, convert_to_tensor=True)
    candidate_embeddings = model.encode(candidate_docs, convert_to_tensor=True)

    # Compute cosine similarities
    cosine_scores = util.pytorch_cos_sim(job_embedding, candidate_embeddings)

    # We take the max score, assuming the most relevant job experience is the best match
    if cosine_scores.numel() > 0:
        return torch.max(cosine_scores).item()
    else:
        return 0.0


# --- Main Orchestration ---

def main():
    """
    Main function to orchestrate the candidate matching process.
    """
    print("Starting Candidate Matching Agent...")

    # 1. Load data
    job_profile = get_job_profile()
    if not job_profile:
        print("Could not load job profile. Exiting.")
        return

    candidate_profiles = get_candidate_profiles()
    if not candidate_profiles:
        print("No candidate profiles found. Exiting.")
        return

    print(f"Loaded job profile: {job_profile.get('job_title', 'N/A')}")
    print(f"Loaded {len(candidate_profiles)} candidate profiles.")

    # 2. Process each candidate
    results = []
    job_skills = job_profile.get('required_skills', [])
    job_responsibilities = job_profile.get('responsibilities', [])

    for candidate in candidate_profiles:
        candidate_name = candidate.get('candidate_name', 'Unknown Candidate')
        print(f"\nProcessing candidate: {candidate_name}...")

        # Get candidate data
        candidate_skills = candidate.get('skills', {})
        candidate_experience = candidate.get('experience', [])

        # Calculate scores
        keyword_score = calculate_keyword_match_score(job_skills, candidate_skills)
        semantic_score = calculate_semantic_match_score(job_responsibilities, candidate_experience)

        # Combine scores with weights
        # We can adjust these weights based on importance
        final_score = (0.4 * keyword_score) + (0.6 * semantic_score)

        results.append({
            "candidate_name": candidate_name,
            "original_filename": candidate.get('original_filename'),
            "keyword_match_score": round(keyword_score, 2),
            "semantic_match_score": round(semantic_score, 2),
            "final_match_score": round(final_score, 2)
        })
        print(f"  - Keyword Score: {keyword_score:.2f}")
        print(f"  - Semantic Score: {semantic_score:.2f}")
        print(f"  - Final Score: {final_score:.2f}")


    # 3. Rank candidates
    ranked_candidates = sorted(results, key=lambda x: x['final_match_score'], reverse=True)

    # 4. Save results
    output_filename = os.path.join(OUTPUT_DIR, "ranked_candidates.json")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(ranked_candidates, f, indent=4)

    print(f"\nSuccessfully ranked {len(ranked_candidates)} candidates.")
    print(f"Results saved to {output_filename}")


if __name__ == "__main__":
    # A quick check for torch, as it was problematic
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
    except ImportError as e:
        print(f"PyTorch import error: {e}. Semantic matching will be affected.")
        # The script will still run but semantic scores will be placeholders.

    main()
