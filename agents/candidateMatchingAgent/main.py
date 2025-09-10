import os
import json
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity # <-- This import was missing

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JOB_PROFILE_DIR = os.path.join(SCRIPT_DIR, "input/job_profiles")
CANDIDATE_PROFILES_DIR = os.path.join(SCRIPT_DIR, "input/candidate_profiles")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
MODEL_NAME = 'all-MiniLM-L6-v2'  # A good starting model for semantic similarity

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
    Calculates a match score using TF-IDF.
    """
    # Candidate skills might be in a nested dictionary
    candidate_skill_list = []
    if isinstance(candidate_skills, dict):
        for category in candidate_skills.values():
            if isinstance(category, list):
                candidate_skill_list.extend([skill.lower() for skill in category])
    elif isinstance(candidate_skills, list):
        candidate_skill_list = [skill.lower() for skill in candidate_skills]

    if not candidate_skill_list or not job_skills:
        return 0.0

    documents = [" ".join(job_skills)] + [" ".join(candidate_skill_list)]
    
    vectorizer = TfidfVectorizer().fit_transform(documents)
    
    # Calculate cosine similarity between the job profile and candidate profile
    # The first document is the job profile, the second is the candidate profile
    cosine_similarity_matrix = cosine_similarity(vectorizer[0:1], vectorizer[1:])[0]
    
    # Return the first (and only) score
    return cosine_similarity_matrix[0]


def calculate_semantic_match_score(job_desc, candidate_exp):
    """
    Calculates a holistic semantic match score.
    Compares the job responsibilities with the candidate's work experience.
    """
    if not job_desc or not candidate_exp:
        return 0.0

    # Candidate experience is a list of dicts or strings, filter out empty ones
    candidate_docs = []
    for exp in candidate_exp:
        if isinstance(exp, dict) and exp.get('responsibilities'):
            candidate_docs.append(" ".join(exp.get('responsibilities')))
        elif isinstance(exp, str) and exp.strip():
            candidate_docs.append(exp)

    if not candidate_docs:
        return 0.0

    # Create embeddings for both job responsibilities and all candidate experience chunks
    job_embeddings = model.encode(job_desc, convert_to_tensor=True)
    candidate_embeddings = model.encode(candidate_docs, convert_to_tensor=True)

    # Compute a full similarity matrix comparing every job sentence to every candidate sentence
    cosine_scores = util.pytorch_cos_sim(job_embeddings, candidate_embeddings)

    # Aggregate scores holistically by taking the average
    if cosine_scores.numel() > 0:
        return torch.mean(cosine_scores).item()
    else:
        return 0.0

# --- Main Orchestration ---

def run_matching_pipeline(job_profile, candidate_profiles):
    """
    Runs the candidate matching process on the given data.
    Accepts data as arguments and returns the ranked list.
    """
    print("Running candidate matching pipeline...")
    if not job_profile or not candidate_profiles:
        print("Missing job profile or candidate profiles.")
        return []

    results = []
    job_skills = job_profile.get('required_skills', [])
    job_responsibilities = job_profile.get('responsibilities', [])

    for candidate in candidate_profiles:
        candidate_name = candidate.get('candidate_name', 'Unknown Candidate')
        print(f"  - Matching candidate: {candidate_name}")

        candidate_skills = candidate.get('skills', {})
        candidate_experience = candidate.get('experience', [])

        keyword_score = calculate_keyword_match_score(job_skills, candidate_skills)
        semantic_score = calculate_semantic_match_score(job_responsibilities, candidate_experience)
        
        final_score = (0.4 * keyword_score) + (0.6 * semantic_score)


        results.append({
            "candidate_name": candidate_name,
            "original_filename": candidate.get('original_filename'),
            "keyword_match_score": round(keyword_score, 2),
            "semantic_match_score": round(semantic_score, 2),
            "final_match_score": round(final_score, 2)
        })

    ranked_candidates = sorted(results, key=lambda x: x['final_match_score'], reverse=True)
    print(f"Successfully ranked {len(ranked_candidates)} candidates.")
    return ranked_candidates

def main_file_based():
    """
    Original main function for running the agent from files.
    Kept for testing or standalone use.
    """
    print("Starting Candidate Matching Agent (File-based)...")
    job_profile = get_job_profile()
    candidate_profiles = get_candidate_profiles()

    ranked_candidates = run_matching_pipeline(job_profile, candidate_profiles)


    if ranked_candidates:
        # Save results
        output_filename = os.path.join(OUTPUT_DIR, "ranked_candidates.json")
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(ranked_candidates, f, indent=4)
        print(f"Results saved to {output_filename}")

if __name__ == "__main__":
    main_file_based()
