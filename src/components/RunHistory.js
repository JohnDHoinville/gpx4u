//**Persist data:** Persistant runs.db is set to /var/render/data
import React, { useState, useEffect } from 'react';
import { API_URL } from '../config';
import './RunHistory.css';
import { safelyParseJSON } from '../utils';

const RunHistory = () => {
    // IMPORTANT: Initialize runs as an empty array, never null or undefined
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Ensure runs is always an array, even if state somehow gets corrupted
    const safeRuns = Array.isArray(runs) ? runs : [];

    useEffect(() => {
        let isMounted = true;
        
        const fetchRuns = async () => {
            setLoading(true);
            try {
                const response = await fetch(`${API_URL}/runs`, {
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}`);
                }
                
                const responseText = await response.text();
                const data = safelyParseJSON(responseText) || [];
                
                if (isMounted) {
                    setRuns(data);
                    setError(null);
                }
            } catch (err) {
                console.error("Error fetching runs:", err);
                if (isMounted) {
                    setError("Failed to load runs. Please try again later.");
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };
        
        fetchRuns();
        
        return () => {
            isMounted = false;
        };
    }, []);

    // Render loading state
    if (loading) {
        return <div className="loading-indicator">Loading runs history...</div>;
    }

    // Render error state
    if (error) {
        return <div className="error-message">Error: {error}</div>;
    }

    // Render empty state
    if (!Array.isArray(safeRuns) || safeRuns.length === 0) {
        return (
            <div className="run-history-container">
                <h2>Run History</h2>
                <p className="no-runs-message">No runs found. Upload a GPX file to get started!</p>
            </div>
        );
    }

    // Only get here if safeRuns is definitely an array with items
    return (
        <div className="run-history-container">
            <h2>Run History</h2>
            <div className="runs-list">
                {safeRuns.map((run, index) => {
                    // More defensive checks for each run item
                    const runId = run?.id || index;
                    const date = run?.date || 'Unknown Date';
                    const distance = (run?.total_distance !== undefined) 
                        ? Number(run.total_distance).toFixed(2) 
                        : '0';
                    const pace = formatPace(run?.avg_pace);
                    const heartRate = run?.avg_hr 
                        ? Math.round(Number(run.avg_hr)) 
                        : null;
                    
                    // Extract fast segments information
                    let fastSegments = [];
                    try {
                        // Access fast_segments from data object
                        if (run.data && run.data.fast_segments && Array.isArray(run.data.fast_segments)) {
                            fastSegments = run.data.fast_segments;
                        }
                    } catch (e) {
                        console.error(`Error processing fast segments for run ${runId}:`, e);
                    }
                        
                    return (
                        <div key={runId} className="run-item">
                            <h3>Run on {date}</h3>
                            <p>Distance: {distance} miles</p>
                            <p>Average Pace: {pace} min/mile</p>
                            {heartRate && <p>Average Heart Rate: {heartRate} bpm</p>}
                            
                            {/* Fast segments section */}
                            {fastSegments.length > 0 && (
                                <div className="fast-segments">
                                    <h4>Fast Segments</h4>
                                    {fastSegments.map((segment, i) => {
                                        const segmentDistance = segment.distance ? 
                                            Number(segment.distance).toFixed(2) : '0';
                                        const segmentPace = formatPace(segment.pace);
                                        
                                        return (
                                            <div key={i} className="segment-item">
                                                <p>Segment {i+1}: {segmentDistance} miles at {segmentPace} min/mile</p>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// Helper function to format pace (seconds to min:sec)
const formatPace = (paceInSeconds) => {
    if (!paceInSeconds) return '0:00';
    try {
        const paceNum = Number(paceInSeconds);
        if (isNaN(paceNum)) return '0:00';
        
        const minutes = Math.floor(paceNum / 60);
        const seconds = Math.floor(paceNum % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    } catch (e) {
        console.error('Error formatting pace:', e);
        return '0:00';
    }
};

export default RunHistory; 