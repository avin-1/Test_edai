import os
import json
from openai import OpenAI
import re
from dotenv import load_dotenv

load_dotenv()

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Configuration ---
RAW_JSON_FOLDER = os.path.join(SCRIPT_DIR, "output")
FINAL_OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "model_output")

# Ensure output directory exists
os.makedirs(FINAL_OUTPUT_FOLDER, exist_ok=True)

# --- OpenAI Client Initialization ---
client = None
if os.environ.get("HF_TOKEN"):
    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.environ["HF_TOKEN"],
    )

# --- Main Refinement Function ---
def run_llm_resume_refinement(raw_data):
    """
    Takes semi-structured resume data and uses an LLM to refine it.
    Returns the final, structured candidate data.
    """
    if not client:
        print("LLM client not initialized. Cannot refine resume data.")
        # Return the raw data so the pipeline can continue with non-LLM data
        return raw_data
    if not raw_data:
        print("No raw data provided for LLM refinement.")
        return None

    prompt = f"""
    You are an expert resume parser. You are given an inconsistent JSON file extracted from a resume. 
    Your task is to correct the data, identify the correct key-value pairs, and produce a clean, structured JSON output.
    Target Schema:
    {{
      "candidate_name": string, "contact_info": {{"email": string, "phone": string, "linkedin_url": string}},
      "summary": string, "experience": [{{"job_title": string, "company_name": string, "start_date": string, "end_date": string, "responsibilities": [string]}}],
      "education": [{{"degree": string, "institution": string, "start_date": string, "end_date": string, "gpa": string}}],
      "skills": {{"languages": [string], "frameworks_tools": [string], "databases": [string], "ai_ml": [string], "cloud_devops": [string]}},
      "projects": [{{"project_name": string, "year": string, "description": string}}],
      "awards_honors": [string], "publications": [string]
    }}
    Input JSON to Correct:
    {json.dumps(raw_data, indent=2)}
    Follow these rules:
    1. Extract and Consolidate: Find all relevant information.
    2. Granularize: Break down long strings into distinct fields.
    3. Use Lists: Split comma-separated or bullet-pointed lists into arrays.
    4. Infer and Structure: Correctly place each piece of data under the appropriate key.
    5. Strict Output: Produce ONLY the final JSON object. Do not include any additional text, markdown, or comments.
    """

    print("  - Sending data to LLM for refinement...")

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b:fireworks-ai",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        response_text = completion.choices[0].message.content
        
        json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        json_str = json_match.group(1) if json_match else response_text
        json_str = json_str.strip()
        
        refined_data = json.loads(json_str)
        print("  - LLM refinement successful.")
        return refined_data

    except json.JSONDecodeError as e:
        print(f"LLM produced invalid JSON: {e}")
        print("Raw LLM output:\n", response_text)
        return None
    except Exception as e:
        print(f"An unexpected error occurred during LLM processing: {e}")
        return None


def refine_resume_json_with_llm_from_file(input_file_path):
    """
    Original function to read from a file, for standalone use.
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading or parsing file {input_file_path}: {e}")
        return

    refined_data = run_llm_resume_refinement(raw_data)

    if refined_data:
        output_file_name = os.path.basename(input_file_path).replace(".json", "_structured.json")
        output_file_path = os.path.join(FINAL_OUTPUT_FOLDER, output_file_name)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(refined_data, f, indent=2, ensure_ascii=False)
        print(f"Refined JSON saved to {output_file_path}")

# --- Main execution loop ---
if __name__ == "__main__":
    json_files = [f for f in os.listdir(RAW_JSON_FOLDER) if f.endswith('.json')]
    if not json_files:
        print(f"No JSON files found in '{RAW_JSON_FOLDER}'. Please run your resume parser first.")
    
    for file_name in json_files:
        input_path = os.path.join(RAW_JSON_FOLDER, file_name)
        refine_resume_json_with_llm(input_path)