import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import JobList from './JobList';
import JobView from './JobView';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>HR Recruitment Dashboard</h1>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<JobList />} />
            <Route path="/job/:jobId" element={<JobView />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
