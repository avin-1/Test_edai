import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

const API_URL = 'http://127.0.0.1:8080';

const JobList = () => {
    const [jobs, setJobs] = useState([]);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchJobs = async () => {
            try {
                const response = await axios.get(`${API_URL}/api/jobs`);
                setJobs(response.data);
            } catch (err) {
                setError('Failed to fetch jobs. Is the backend server running?');
                console.error(err);
            }
        };
        fetchJobs();
    }, []);

    return (
        <div>
            <h2>All Jobs</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {jobs.length > 0 ? (
                <table>
                    <thead>
                        <tr>
                            <th>Job Title</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {jobs.map(job => (
                            <tr key={job.id}>
                                <td>{job.title}</td>
                                <td>
                                    <Link to={`/job/${job.id}`}>View Details</Link>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : (
                !error && <p>No jobs found. Create one via the API.</p>
            )}
        </div>
    );
};

export default JobList;
