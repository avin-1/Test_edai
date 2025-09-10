# AI-Powered HR Recruitment System (MVP)

This project is a Minimum Viable Project (MVP) for an AI-powered recruitment system. It uses a series of backend "agents" to process job descriptions and resumes, and a React-based frontend to provide a user interface for managing the workflow.

The backend is built with Flask and the frontend is built with React.

## How to Run the Application

The project consists of two main parts: the **Flask Backend API** and the **React Frontend**. You need to run them in two separate terminals.

### Prerequisites

- Python 3.x
- Node.js and npm

### 1. Backend Setup

First, set up and run the Flask API server.

**a. Install Python Dependencies:**

From the root directory of the project, install all the necessary packages:
```bash
pip install -r requirements.txt
```

**b. Set API Keys (Optional):**

The agents for parsing job descriptions and resumes use an LLM. If you want to use this functionality, you need to set an API key. The application will run without it, but the parsing quality will be lower.

Create a `.env` file in the root directory and add your key:
```
HF_TOKEN="your_huggingface_api_token_here"
```

**c. Run the Backend Server:**

Start the Flask server from the root directory:
```bash
python3 app.py
```
The API server will start, typically on `http://127.0.0.1:8080`.

---

### 2. Frontend Setup

In a **new terminal window**, navigate to the `frontend` directory to set up and run the React application.

**a. Navigate to the Frontend Directory:**
```bash
cd frontend
```

**b. Install JavaScript Dependencies:**
```bash
npm install
```

**c. Run the Frontend Development Server:**
```bash
npm start
```
This will automatically open the application in your web browser, usually at `http://localhost:3000`.

## Using the Application

Once both servers are running, you can use the application in your browser at `http://localhost:3000`.

The workflow is as follows:
1.  **Create a Job:** From the main dashboard, create a new job by providing a job description.
2.  **Upload Resumes:** On the job details page, upload candidate resumes in PDF format.
3.  **Run Pipeline:** Trigger the matching and shortlisting pipeline.
4.  **View Results:** The page will update to show the final shortlist of candidates.
5.  **Simulate Actions:** Use the buttons to simulate scheduling an interview or logging feedback for a candidate.
