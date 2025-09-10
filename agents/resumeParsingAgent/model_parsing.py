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
# The client setup you provided
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)

# --- Main Refinement Function ---
def refine_resume_json_with_llm(input_file_path):
    """
    Reads an inconsistent JSON file and uses a generative LLM to structure it.
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {input_file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {input_file_path}")
        return

    # A better, more comprehensive prompt to handle the inconsistencies
    prompt = f"""
    You are an expert resume parser. You are given an inconsistent JSON file extracted from a resume. 
    Your task is to correct the data, identify the correct key-value pairs, and produce a clean, structured JSON output.

    The input JSON has several problems:
    - Many keys are actually values (e.g., "CGPA: 8.63" is a key with an empty string as a value).
    - Content is split across multiple keys and sections.
    - Some keys are simply numbers or dates.
    - The content is not granular (e.g., job titles and companies are in a single string).
    
    You must use your knowledge to infer the correct structure and relationships.

    Target Schema:
    ```json
    {{
      "candidate_name": string,
      "contact_info": {{
        "email": string,
        "phone": string,
        "linkedin_url": string
      }},
      "summary": string,
      "experience": [
        {{
          "job_title": string,
          "company_name": string,
          "start_date": string,
          "end_date": string,
          "responsibilities": [string]
        }}
      ],
      "education": [
        {{
          "degree": string,
          "institution": string,
          "start_date": string,
          "end_date": string,
          "gpa": string
        }}
      ],
      "skills": {{
        "languages": [string],
        "frameworks_tools": [string],
        "databases": [string],
        "ai_ml": [string],
        "cloud_devops": [string]
      }},
      "projects": [
        {{
          "project_name": string,
          "year": string,
          "description": string
        }}
      ],
      "awards_honors": [string],
      "publications": [string]
    }}
    ```

    Input JSON to Correct:
    ```json
    {json.dumps(raw_data, indent=2)}
    ```

    Follow these rules:
    1.  **Extract and Consolidate**: Find all relevant information (e.g., "CGPA," "B.Tech") from across all sections, including the `categorized_sections` and `experience`/`education`/`skills` arrays.
    2.  **Granularize**: Break down long strings into distinct fields like `job_title`, `company_name`, `start_date`, and `end_date`.
    3.  **Use Lists**: For skills, split comma-separated or bullet-pointed lists into arrays of strings.
    4.  **Infer and Structure**: Based on the context, correctly place each piece of data under the appropriate key in the target schema.
    5.  **Strict Output**: Produce ONLY the final JSON object. Do not include any additional text, markdown, or comments before or after the JSON. The JSON must be perfectly valid.
    
    Begin your response with the JSON object.
    """

    print(f"Processing {os.path.basename(input_file_path)}...")

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b:fireworks-ai",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        # With response_format, the response content is guaranteed to be a valid JSON string.
        response_text = completion.choices[0].message.content
        refined_data = json.loads(response_text)

        # Save the refined JSON to the final output folder
        output_file_name = os.path.basename(input_file_path).replace(".json", "_structured.json")
        output_file_path = os.path.join(FINAL_OUTPUT_FOLDER, output_file_name)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(refined_data, f, indent=2, ensure_ascii=False)
        
        print(f"Refined JSON saved to {output_file_path}")

    except Exception as e:
        print(f"An unexpected error occurred during LLM processing: {e}")
        # The json.loads error should be prevented by response_format, but other API errors can still occur.

# --- Main execution loop ---
if __name__ == "__main__":
    json_files = [f for f in os.listdir(RAW_JSON_FOLDER) if f.endswith('.json')]
    if not json_files:
        print(f"No JSON files found in '{RAW_JSON_FOLDER}'. Please run your resume parser first.")
    
    for file_name in json_files:
        input_path = os.path.join(RAW_JSON_FOLDER, file_name)
        refine_resume_json_with_llm(input_path)