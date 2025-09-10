# Candidate Matching Agent

This agent matches candidates to a job description based on skills and experience.

## How it Works

The agent takes a structured job profile (JSON) and a directory of structured candidate profiles (JSON) as input. It then performs the following steps:

1.  **Keyword Matching**: It compares the `required_skills` from the job profile with the `skills` in each candidate's profile.
2.  **Semantic Matching**: It uses a sentence transformer model to calculate the semantic similarity between the job `responsibilities` and the candidate's work `experience`.
3.  **Scoring and Ranking**: It combines the keyword and semantic scores into a final match score and ranks the candidates from best to worst match.

## How to Run

1.  **Place Data**:
    *   Place one structured job profile JSON file in the `input/job_profiles/` directory.
    *   Place one or more structured candidate profile JSON files in the `input/candidate_profiles/` directory.
2.  **Execute the Script**:
    Run the agent from the root of the repository using the following command:
    ```bash
    python3 agents/candidateMatchingAgent/main.py
    ```
3.  **View Results**:
    The ranked list of candidates will be saved in the `output/ranked_candidates.json` file.
