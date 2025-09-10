import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';

const API_URL = 'http://127.0.0.1:8080';

const JobView = () => {
    const { jobId } = useParams();
    const [job, setJob] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchJobDetails = async () => {
            try {
                const response = await axios.get(`${API_URL}/api/job/${jobId}`);
                setJob(response.data);
            } catch (err) {
                setError('Failed to fetch job details.');
                console.error(err);
            }
        };
        fetchJobDetails();
    }, [jobId]);

    if (error) {
        return <p style={{ color: 'red' }}>{error}</p>;
    }

    if (!job) {
        return <p>Loading job details...</p>;
    }

    return (
        <div>
            <Link to="/">&laquo; Back to All Jobs</Link>
            <h2>{job.job_profile.job_title}</h2>

            <div className="controls">
                {/* File upload would be more complex, this is a placeholder */}
                <button>Upload Resumes</button>
                <button>Run Matching Pipeline</button>
            </div>

            <h3>Final Shortlist ({job.shortlist.length})</h3>
            {job.shortlist.length > 0 ? (
                 <table>
                    <thead>
                        <tr>
                            <th>Candidate Name</th>
                            <th>Match Score</th>
                            <th>Reason</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {job.shortlist.map((candidate, index) => (
                            <tr key={index}>
                                <td>{candidate.candidate_name}</td>
                                <td>{candidate.final_match_score}</td>
                                <td>{candidate.explanation}</td>
                                <td>
                                    <button>Schedule</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : <p>No shortlist available.</p>}

            <h3 style={{marginTop: '40px'}}>Loaded Candidates ({job.candidates.length})</h3>
             {job.candidates.length > 0 ? (
                 <table>
                    <thead>
                        <tr>
                            <th>Candidate Name</th>
                            <th>Email</th>
                        </tr>
                    </thead>
                    <tbody>
                        {job.candidates.map((candidate, index) => (
                            <tr key={index}>
                                <td>{candidate.candidate_name}</td>
                                <td>{candidate.contact_info.email}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : <p>No candidates loaded for this job.</p>}
        </div>
    );
};

export default JobView;
