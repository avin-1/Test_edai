import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash
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

# --- Configuration ---
JD_INPUT_DIR = os.path.join('agents', 'JobDescriptionParsingAgent', 'Input')
RESUME_INPUT_DIR = os.path.join('agents', 'resumeParsingAgent', 'input')
ALLOWED_EXTENSIONS = {'pdf'}
app.config['SECRET_KEY'] = 'a_secure_random_secret_key_for_mvp'

# --- Initialize Database ---
db.init_db()

# --- Helper ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Flask Routes ---

import datetime

@app.route('/')
def index():
    """Main dashboard, shows a list of all jobs."""
    all_jobs = db.get_all_jobs()
    # Format the timestamp for display
    for job in all_jobs:
        job['created_at_formatted'] = datetime.datetime.fromtimestamp(job['created_at']).strftime('%Y-%m-%d %H:%M')
    return render_template('index.html', title='HR Dashboard', jobs=all_jobs)

@app.route('/job/<job_id>')
def job_view(job_id):
    """Displays the details for a single job, including candidates and shortlist."""
    job_data = db.get_job(job_id)
    if not job_data:
        flash(f"Job with ID {job_id} not found.", 'error')
        return redirect(url_for('index'))

    return render_template('job_view.html', title=job_data['job_profile'].get('job_title', 'Job Details'), job=job_data, job_id=job_id)

@app.route('/add_job', methods=['GET', 'POST'])
def add_job():
    """Handles creating a new job."""
    if request.method == 'POST':
        jd_text = request.form['jd_text']
        if not jd_text:
            flash('Job Description text cannot be empty.', 'error')
            return redirect(request.url)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=jd_text.encode('latin-1', 'replace').decode('latin-1'))
        pdf_path = os.path.join(JD_INPUT_DIR, f"jd_{uuid.uuid4()}.pdf")
        pdf.output(pdf_path)

        parsed_job_data = process_job_description(pdf_path)
        if parsed_job_data:
            job_id = db.create_job(parsed_job_data)
            flash(f"New job '{parsed_job_data.get('job_title')}' created.", 'success')
            return redirect(url_for('job_view', job_id=job_id))
        else:
            flash('Failed to parse the provided job description.', 'error')
            return redirect(request.url)

    return render_template('add_job.html', title='Add New Job')

@app.route('/job/<job_id>/upload_resumes', methods=['GET', 'POST'])
def upload_resumes(job_id):
    """Handles uploading resumes for a specific job."""
    job_data = db.get_job(job_id)
    if not job_data:
        flash('Job not found.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        files = request.files.getlist('resumes')
        if not files or files[0].filename == '':
            flash('No selected files.', 'error')
            return redirect(request.url)

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

        flash(f'Successfully parsed and added {parsed_count} new resumes.', 'success')
        return redirect(url_for('job_view', job_id=job_id))

    return render_template('upload_resumes.html', title='Upload Resumes', job=job_data, job_id=job_id)

@app.route('/job/<job_id>/run_pipeline', methods=['POST'])
def run_pipeline(job_id):
    """Runs the full matching and shortlisting pipeline for a job."""
    job_data = db.get_job(job_id)
    if not job_data:
        flash('Job not found.', 'error')
        return redirect(url_for('index'))

    candidates = db.get_candidates_for_job(job_id)
    if not candidates:
        flash('No candidates for this job. Please upload resumes first.', 'error')
        return redirect(url_for('job_view', job_id=job_id))

    ranked_list = run_matching_pipeline(job_data['job_profile'], candidates)
    final_shortlist = run_shortlisting_pipeline(ranked_list)
    db.save_shortlist(job_id, final_shortlist)

    flash(f"Pipeline complete! {len(final_shortlist)} candidates were shortlisted.", 'success')
    return redirect(url_for('job_view', job_id=job_id))

@app.route('/job/<job_id>/schedule/<int:candidate_index>', methods=['POST'])
def schedule(job_id, candidate_index):
    """Schedules an interview."""
    shortlist = db.get_shortlist(job_id)
    job_data = db.get_job(job_id)

    if candidate_index >= len(shortlist):
        flash('Invalid candidate.', 'error')
        return redirect(url_for('job_view', job_id=job_id))

    candidate = shortlist[candidate_index]
    candidate_name = candidate.get('candidate_name', 'N/A')
    candidate_email = candidate.get('contact_info', {}).get('email', 'email_not_found')
    job_title = job_data['job_profile'].get('job_title', 'N/A')

    if schedule_interview(candidate_name, candidate_email, job_title):
        flash(f"Interview scheduled with {candidate_name}.", 'success')
    else:
        flash(f"Failed to schedule interview.", 'error')

    return redirect(url_for('job_view', job_id=job_id))

@app.route('/job/<job_id>/feedback/<int:candidate_index>/<feedback_type>', methods=['POST'])
def feedback(job_id, candidate_index, feedback_type):
    """Logs feedback for a candidate."""
    shortlist = db.get_shortlist(job_id)
    job_data = db.get_job(job_id)

    if feedback_type not in ['positive', 'negative'] or candidate_index >= len(shortlist):
        flash('Invalid request.', 'error')
        return redirect(url_for('job_view', job_id=job_id))

    candidate = shortlist[candidate_index]
    candidate_name = candidate.get('candidate_name', 'N/A')
    job_title = job_data['job_profile'].get('job_title', 'N/A')

    if log_feedback(candidate_name, job_title, feedback_type):
        flash(f"Feedback logged for {candidate_name}.", 'success')
    else:
        flash('Failed to log feedback.', 'error')

    return redirect(url_for('job_view', job_id=job_id))

if __name__ == '__main__':
    # Need to import uuid for the pdf name
    import uuid
    app.run(debug=True, host='0.0.0.0', port=8080)
