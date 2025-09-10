import shelve
import time
import uuid

DB_FILE = 'hr_app_state.db'

def create_job(job_data):
    """
    Saves a new job profile to the database.
    Returns a unique ID for the job.
    """
    with shelve.open(DB_FILE, writeback=True) as db:
        job_id = str(uuid.uuid4())
        db[job_id] = {
            'job_profile': job_data,
            'created_at': time.time(),
            'candidates': [],
            'shortlist': []
        }
    return job_id

def add_candidate(job_id, candidate_data):
    """Adds a parsed candidate profile to a specific job."""
    with shelve.open(DB_FILE, writeback=True) as db:
        if job_id in db:
            db[job_id]['candidates'].append(candidate_data)
        else:
            raise ValueError(f"Job ID {job_id} not found in database.")

def get_job(job_id):
    """Retrieves a job's data from the database."""
    with shelve.open(DB_FILE) as db:
        return db.get(job_id)

def get_all_jobs():
    """Returns a list of all jobs, sorted by creation date."""
    with shelve.open(DB_FILE) as db:
        jobs = []
        for key in db.keys():
            job_info = {
                'id': key,
                'title': db[key]['job_profile'].get('job_title', 'N/A'),
                'created_at': db[key]['created_at']
            }
            jobs.append(job_info)
    # Sort jobs by most recent first
    return sorted(jobs, key=lambda x: x['created_at'], reverse=True)

def get_candidates_for_job(job_id):
    """Retrieves all candidate profiles for a specific job."""
    with shelve.open(DB_FILE) as db:
        if job_id in db:
            return db[job_id]['candidates']
        return []

def save_shortlist(job_id, shortlist_data):
    """Saves the final shortlist for a job."""
    with shelve.open(DB_FILE, writeback=True) as db:
        if job_id in db:
            db[job_id]['shortlist'] = shortlist_data
        else:
            raise ValueError(f"Job ID {job_id} not found in database.")

def get_shortlist(job_id):
    """Retrieves the shortlist for a job."""
    with shelve.open(DB_FILE) as db:
        if job_id in db:
            return db[job_id]['shortlist']
        return []

# A simple function to initialize or check the DB.
# Can be called at the start of the Flask app.
def init_db():
    """Initializes the shelve file if it doesn't exist."""
    with shelve.open(DB_FILE) as db:
        print(f"Database initialized. Contains {len(db.keys())} jobs.")
