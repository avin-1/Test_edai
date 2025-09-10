import os
import sys
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from fpdf import FPDF
import database as db

# --- Add agents directory to sys.path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'agents')))

# --- Import Agent Functions ---
from JobDescriptionParsingAgent.main import process_job_description
from resumeParsingAgent.main import run_local_resume_parsing
from resumeParsingAgent.model_parsing import run_llm_resume_refinement
from candidateMatchingAgent.main import run_matching_pipeline
from candidateShortlistingAgent.main import run_shortlisting_pipeline
from interviewSchedulingAgent.main import schedule_interview
from feedbackAgent.main import log_feedback

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# --- Configuration ---
JD_INPUT_DIR = os.path.join('agents', 'JobDescriptionParsingAgent', 'Input')
RESUME_INPUT_DIR = os.path.join('agents', 'resumeParsingAgent', 'input')
ALLOWED_EXTENSIONS = {'pdf'}

db.init_db()

# --- Helper ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- API Routes ---

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """API endpoint to get a list of all jobs."""
    all_jobs = db.get_all_jobs()
    return jsonify(all_jobs)

@app.route('/api/job/<job_id>', methods=['GET'])
def get_job_details(job_id):
    """API endpoint to get details for a single job."""
    job_data = db.get_job(job_id)
    if not job_data:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job_data)

@app.route('/api/jobs', methods=['POST'])
def create_new_job():
    """API endpoint to create a new job."""
    jd_text = request.json.get('jd_text')
    if not jd_text:
        return jsonify({"error": "jd_text is required"}), 400

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=jd_text.encode('latin-1', 'replace').decode('latin-1'))
    pdf_path = os.path.join(JD_INPUT_DIR, f"jd_{uuid.uuid4()}.pdf")
    pdf.output(pdf_path)

    parsed_job_data = process_job_description(pdf_path)
    if parsed_job_data:
        job_id = db.create_job(parsed_job_data)
        new_job = db.get_job(job_id)
        return jsonify({"message": "Job created successfully", "job": new_job}), 201
    else:
        return jsonify({"error": "Failed to parse job description"}), 500

@app.route('/api/job/<job_id>/resumes', methods=['POST'])
def upload_job_resumes(job_id):
    """API endpoint to upload resumes for a specific job."""
    if 'resumes' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('resumes')
    if not files or files[0].filename == '':
        return jsonify({"error": "No selected files"}), 400

    parsed_count = 0
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(RESUME_INPUT_DIR, filename)
            file.save(save_path)

            raw_data = run_local_resume_parsing(save_path)
            if raw_data:
                refined_data = run_llm_resume_refinement(raw_data)
                if refined_data:
                    refined_data['original_filename'] = filename
                    db.add_candidate(job_id, refined_data)
                    parsed_count += 1

    return jsonify({"message": f"Successfully parsed and added {parsed_count} new resumes."}), 200

@app.route('/api/job/<job_id>/run_pipeline', methods=['POST'])
def run_job_pipeline(job_id):
    """API endpoint to run the full pipeline for a job."""
    job_data = db.get_job(job_id)
    if not job_data:
        return jsonify({"error": "Job not found"}), 404

    candidates = db.get_candidates_for_job(job_id)
    if not candidates:
        return jsonify({"error": "No candidates for this job"}), 400

    ranked_list = run_matching_pipeline(job_data['job_profile'], candidates)
    final_shortlist = run_shortlisting_pipeline(ranked_list)
    db.save_shortlist(job_id, final_shortlist)

    return jsonify({"message": "Pipeline complete", "shortlist": final_shortlist}), 200

@app.route('/api/job/<job_id>/schedule/<int:candidate_index>', methods=['POST'])
def schedule_api(job_id, candidate_index):
    """API endpoint for scheduling."""
    shortlist = db.get_shortlist(job_id)
    job_data = db.get_job(job_id)
    if candidate_index >= len(shortlist):
        return jsonify({"error": "Invalid candidate index"}), 400

    candidate = shortlist[candidate_index]
    if schedule_interview(candidate.get('candidate_name'), candidate.get('contact_info', {}).get('email'), job_data['job_profile'].get('job_title')):
        return jsonify({"message": f"Interview scheduled with {candidate.get('candidate_name')}"}), 200
    else:
        return jsonify({"error": "Failed to schedule interview"}), 500

@app.route('/api/job/<job_id>/feedback/<int:candidate_index>/<feedback_type>', methods=['POST'])
def feedback_api(job_id, candidate_index, feedback_type):
    """API endpoint for logging feedback."""
    shortlist = db.get_shortlist(job_id)
    job_data = db.get_job(job_id)
    if feedback_type not in ['positive', 'negative'] or candidate_index >= len(shortlist):
        return jsonify({"error": "Invalid request"}), 400

    candidate = shortlist[candidate_index]
    if log_feedback(candidate.get('candidate_name'), job_data['job_profile'].get('job_title'), feedback_type):
        return jsonify({"message": f"Feedback logged for {candidate.get('candidate_name')}"}), 200
    else:
        return jsonify({"error": "Failed to log feedback"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
