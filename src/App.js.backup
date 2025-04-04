/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, createContext, useContext, useEffect, useRef, useMemo } from 'react';
import './App.css';
import LoadingSpinner from './components/LoadingSpinner';
import LoginForm from './components/LoginForm';
import TrainingZones from './components/TrainingZones';
import AdvancedMetrics from './components/AdvancedMetrics';
import RacePredictions from './components/RacePredictions';
import { API_URL } from './config';
import { safelyParseJSON, formatPace } from './utils';
import { Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  Filler
} from 'chart.js';
import { 
  MapContainer, 
  TileLayer, 
  Polyline,
  Tooltip as MapTooltip,
  Circle,
  CircleMarker
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import PaceProgressChart from './components/PaceProgressChart';
import HeartRatePaceCorrelation from './components/HeartRatePaceCorrelation';
import FatigueAnalysis from './components/FatigueAnalysis';
import PaceConsistency from './components/PaceConsistency';
import CustomSegments from './components/CustomSegments';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

// Create theme context
const ThemeContext = createContext();

// Add theme provider component
const ThemeProvider = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  return (
    <ThemeContext.Provider value={{ isDarkMode, setIsDarkMode }}>
      <div className={`theme ${isDarkMode ? 'dark' : 'light'}`}>
        {children}
      </div>
    </ThemeContext.Provider>
  );
};

// Add theme toggle component
const ThemeToggle = () => {
  const { isDarkMode, setIsDarkMode } = useContext(ThemeContext);
  return (
    <button 
      className="theme-toggle"
      onClick={() => setIsDarkMode(!isDarkMode)}
      aria-label="Toggle dark mode"
    >
      {isDarkMode ? '☀️' : '🌙'}
    </button>
  );
};

// Add ProfileMenu component after ThemeToggle
const ProfileMenu = ({ username, age, restingHR, onSave, onLogout, showUploadForm, setShowUploadForm }) => {
  const { isDarkMode, setIsDarkMode } = useContext(ThemeContext);
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [editAge, setEditAge] = useState(age || '');
  const [editRestingHR, setEditRestingHR] = useState(restingHR || '');
  const [editWeight, setEditWeight] = useState('70');
  const [editGender, setEditGender] = useState('1');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const menuRef = useRef(null);

  // Update local state when props change
  useEffect(() => {
    setEditAge(age || '');
    setEditRestingHR(restingHR || '');
    // Get weight and gender from profile
    fetch(`${API_URL}/profile`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        // Ensure weight is in pounds (backend might store in kg)
        const weightInPounds = data.weight_unit === 'kg' ? 
          Math.round(data.weight * 2.20462) : 
          data.weight;
        setEditWeight(weightInPounds?.toString() || '160');
        setEditGender(data.gender?.toString() || '1');
      });
  }, [age, restingHR]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSave = async () => {
    try {
      setError('');
      setSuccessMessage('');
      
      const response = await fetch(`${API_URL}/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          age: parseInt(editAge),
          resting_hr: parseInt(editRestingHR),
          weight: parseFloat(editWeight),
          weight_unit: 'lbs', // Explicitly specify weight is in pounds
          gender: parseInt(editGender)
        }),
      });

      if (response.ok) {
        onSave(editAge, editRestingHR);
        setSuccessMessage('Profile updated successfully');
      } else {
        const error = await response.json();
        setError(error.message || 'Failed to save profile');
      }
    } catch (error) {
      setError('Error saving profile. Please try again.');
    }
  };

  const handleChangePassword = async () => {
    try {
      setError('');
      setSuccessMessage('');

      if (newPassword !== confirmPassword) {
        setError('New passwords do not match');
        return;
      }

      const response = await fetch(`${API_URL}/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        }),
      });

      if (response.ok) {
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setSuccessMessage('Password updated successfully');
      } else {
        const error = await response.json();
        setError(error.message || 'Failed to update password');
      }
    } catch (error) {
      setError('Error updating password');
    }
  };

  return (
    <div className="profile-menu" ref={menuRef}>
      <div className="user-menu">
        <span className="username">👤 {username}</span>
        <button 
          className="add-run-button-header" 
          onClick={() => setShowUploadForm(!showUploadForm)}
          aria-label="Add new run"
        >
          +
        </button>
        <button 
          className="hamburger-button"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Menu"
        >
          ☰
        </button>
      </div>
      
      {isOpen && (
        <div className="profile-dropdown">
          <div className="profile-header">
            <h3>Profile Settings</h3>
            <button 
              className="close-button"
              onClick={() => setIsOpen(false)}
              aria-label="Close"
            >
              ×
            </button>
          </div>

          <div className="profile-tabs">
            <button 
              className={activeTab === 'profile' ? 'active' : ''}
              onClick={() => setActiveTab('profile')}
            >
              Profile
            </button>
            <button 
              className={activeTab === 'security' ? 'active' : ''}
              onClick={() => setActiveTab('security')}
            >
              Security
            </button>
          </div>

          {error && <div className="profile-error">{error}</div>}
          {successMessage && <div className="profile-success">{successMessage}</div>}

          {activeTab === 'profile' ? (
            <div className="profile-content">
              <div className="theme-toggle-container">
                <label>Theme</label>
                <button 
                  className="theme-toggle-button"
                  onClick={() => setIsDarkMode(!isDarkMode)}
                >
                  {isDarkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
                </button>
              </div>

              <div className="profile-stats">
                <div className="stat-item">
                  <span className="stat-label">Current Age</span>
                  <span className="stat-value">{age || 'Not set'}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Current Resting HR</span>
                  <span className="stat-value">{restingHR || 'Not set'} {restingHR && 'bpm'}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Current Weight</span>
                  <span className="stat-value">{editWeight || 'Not set'} {editWeight && 'lbs'}</span>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="profileAge">Update Age:</label>
                <input
                  type="number"
                  id="profileAge"
                  value={editAge}
                  onChange={(e) => setEditAge(e.target.value)}
                  min="0"
                  max="120"
                  placeholder="Enter your age"
                />
              </div>

              <div className="form-group">
                <label htmlFor="profileRestingHR">Update Resting Heart Rate (bpm):</label>
                <input
                  type="number"
                  id="profileRestingHR"
                  value={editRestingHR}
                  onChange={(e) => setEditRestingHR(e.target.value)}
                  min="30"
                  max="200"
                  placeholder="Enter resting heart rate"
                />
              </div>

              <div className="form-group">
                <label htmlFor="weight">Weight (lbs):</label>
                <input
                  type="number"
                  id="weight"
                  value={editWeight}
                  onChange={(e) => setEditWeight(e.target.value)}
                  min="50"
                  max="400"
                  placeholder="Enter your weight in pounds"
                />
              </div>

              <div className="form-group">
                <label htmlFor="gender">Gender:</label>
                <select
                  id="gender"
                  value={editGender}
                  onChange={(e) => setEditGender(e.target.value)}
                >
                  <option value="1">Male</option>
                  <option value="0">Female</option>
                </select>
              </div>

              <button onClick={handleSave} className="save-button">
                Save Changes
              </button>
            </div>
          ) : (
            <div className="security-content">
              <div className="form-group">
                <label htmlFor="currentPassword">Current Password:</label>
                <input
                  type="password"
                  id="currentPassword"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                />
              </div>

              <div className="form-group">
                <label htmlFor="newPassword">New Password:</label>
                <input
                  type="password"
                  id="newPassword"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                />
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm New Password:</label>
                <input
                  type="password"
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                />
              </div>

              <button onClick={handleChangePassword} className="save-button">
                Update Password
              </button>
            </div>
          )}

          <div className="profile-footer">
            <button onClick={onLogout} className="logout-button">
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Add these chart preparation functions
const preparePaceChart = (run) => {
  const data = typeof run.data === 'string' ? JSON.parse(run.data) : run.data;
  
  // Create quarter-mile interpolated data from mile splits
  const quarterMileSplits = [];
  const mileSplits = data.mile_splits || [];
  
  for (let i = 0; i < mileSplits.length - 1; i++) {
    const currentSplit = mileSplits[i];
    const nextSplit = mileSplits[i + 1];
    
    // Add current mile point
    quarterMileSplits.push({
      distance: currentSplit.mile,
      pace: currentSplit.split_pace
    });
    
    // Add three quarter points between miles
    for (let q = 1; q <= 3; q++) {
      const fraction = q / 4;
      const interpolatedPace = currentSplit.split_pace + 
        (nextSplit.split_pace - currentSplit.split_pace) * fraction;
      
      quarterMileSplits.push({
        distance: currentSplit.mile + fraction,
        pace: interpolatedPace
      });
    }
  }
  
  // Add the last mile point
  if (mileSplits.length > 0) {
    const lastSplit = mileSplits[mileSplits.length - 1];
    quarterMileSplits.push({
      distance: lastSplit.mile,
      pace: lastSplit.split_pace
    });
  }

  return {
    labels: quarterMileSplits.map(split => `Mile ${split.distance.toFixed(2)}`),
    datasets: [{
      label: 'Pace',
      data: quarterMileSplits.map(split => split.pace),
      borderColor: 'var(--accent-primary)',
      backgroundColor: 'rgba(112, 193, 179, 0.2)',
      fill: true,
      tension: 0.4
    }]
  };
};

const prepareHRChart = (run) => {
  const data = typeof run.data === 'string' ? JSON.parse(run.data) : run.data;
  
  // Create quarter-mile interpolated data from mile splits
  const quarterMileSplits = [];
  const mileSplits = data.mile_splits || [];
  
  for (let i = 0; i < mileSplits.length - 1; i++) {
    const currentSplit = mileSplits[i];
    const nextSplit = mileSplits[i + 1];
    
    // Add current mile point
    quarterMileSplits.push({
      distance: currentSplit.mile,
      hr: currentSplit.avg_hr
    });
    
    // Add three quarter points between miles
    for (let q = 1; q <= 3; q++) {
      const fraction = q / 4;
      const interpolatedHR = currentSplit.avg_hr + 
        (nextSplit.avg_hr - currentSplit.avg_hr) * fraction;
      
      quarterMileSplits.push({
        distance: currentSplit.mile + fraction,
        hr: interpolatedHR
      });
    }
  }
  
  // Add the last mile point
  if (mileSplits.length > 0) {
    const lastSplit = mileSplits[mileSplits.length - 1];
    quarterMileSplits.push({
      distance: lastSplit.mile,
      hr: lastSplit.avg_hr
    });
  }

  return {
    labels: quarterMileSplits.map(split => `Mile ${split.distance.toFixed(2)}`),
    datasets: [{
      label: 'Heart Rate',
      data: quarterMileSplits.map(split => split.hr),
      borderColor: 'var(--fast-color)',
      backgroundColor: 'rgba(231, 111, 81, 0.2)',
      fill: true,
      tension: 0.4
    }]
  };
};

const paceChartOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: 'top',
    },
    title: {
      display: true,
      text: 'Pace by Quarter Mile'
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: 'Distance'
      },
      ticks: {
        maxRotation: 45,
        minRotation: 45
      }
    },
    y: {
      title: {
        display: true,
        text: 'min/mile'
      }
    }
  }
};

const hrChartOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: 'top',
    },
    title: {
      display: true,
      text: 'Heart Rate by Quarter Mile'
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: 'Distance'
      },
      ticks: {
        maxRotation: 45,
        minRotation: 45
      }
    },
    y: {
      title: {
        display: true,
        text: 'bpm'
      }
    }
  }
};

// Add these chart preparation functions
const preparePaceComparisonData = (run1, run1Data, run2, run2Data) => {
  const getFastPace = (data) => {
    if (!data?.fast_segments?.length) return null;
    return data.fast_segments.reduce((sum, seg) => sum + (seg.pace || 0), 0) / data.fast_segments.length;
  };

  const getSlowPace = (data) => {
    if (!data?.slow_segments?.length) return null;
    return data.slow_segments.reduce((sum, seg) => sum + (seg.pace || 0), 0) / data.slow_segments.length;
  };

  return {
    labels: ['Fast Segments', 'Slow Segments', 'Overall'],
    datasets: [
      {
        label: `Run 1 (${run1.total_distance?.toFixed(1) || 'N/A'} mi)`,
        data: [
          getFastPace(run1Data) || 0,
          getSlowPace(run1Data) || 0,
          run1.avg_pace || 0
        ],
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
      },
      {
        label: `Run 2 (${run2.total_distance?.toFixed(1) || 'N/A'} mi)`,
        data: [
          getFastPace(run2Data) || 0,
          getSlowPace(run2Data) || 0,
          run2.avg_pace || 0
        ],
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
      }
    ]
  };
};

const prepareHRComparisonData = (run1Data, run2Data) => {
  return {
    labels: ['Fast Segments', 'Slow Segments', 'Overall'],
    datasets: [
      {
        label: `Run 1 (${run1Data.total_distance?.toFixed(1) || 'N/A'} mi)`,
        data: [
          run1Data?.avg_hr_fast || 0,
          run1Data?.avg_hr_slow || 0,
          run1Data?.avg_hr_all || 0
        ],
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
      },
      {
        label: `Run 2 (${run2Data.total_distance?.toFixed(1) || 'N/A'} mi)`,
        data: [
          run2Data?.avg_hr_fast || 0,
          run2Data?.avg_hr_slow || 0,
          run2Data?.avg_hr_all || 0
        ],
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
      }
    ]
  };
};

const comparisonChartOptions = {
  responsive: true,
  scales: {
    y: {
      beginAtZero: true,
    }
  },
  plugins: {
    legend: {
      display: true,
      position: 'top'
    },
    title: {
      display: true,
      text: (ctx) => {
        // Check first dataset point to determine if this is pace or HR chart
        const firstValue = ctx.chart.data.datasets[0].data[0];
        if (firstValue > 50) { // Assuming this is HR data
          return 'Heart Rate Comparison (bpm)';
        } else {
          return 'Pace Comparison (min/mi)';
        }
      }
    },
    tooltip: {
      callbacks: {
        label: function(context) {
          const value = context.parsed.y;
          const label = context.dataset.label;
          // Check if this is pace or HR data
          if (value < 50) { // Assuming this is pace data
            return `${label}: ${formatPace(value)} min/mi`;
          } else {
            return `${label}: ${Math.round(value)} bpm`;
          }
        }
      }
    }
  }
};

// Format time minutes to hh:mm display
const formatTime = (minutes) => {
  const hours = Math.floor(minutes / 60);
  const mins = Math.floor(minutes % 60);
  const secs = Math.round((minutes % 1) * 60);
  
  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// Helper function to format time in hours, minutes and seconds
const formatRunTime = (timeInMinutes) => {
  if (!timeInMinutes) return "0:00:00";
  
  const hours = Math.floor(timeInMinutes / 60);
  const minutes = Math.floor(timeInMinutes % 60);
  const seconds = Math.round((timeInMinutes % 1) * 60);
  
  return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
};

// Add this near the top of the file with other context definitions
const TableContext = createContext();

// Add this provider component
const TableProvider = ({ children }) => {
  const [openTables, setOpenTables] = useState(new Set());
  
  return (
    <TableContext.Provider value={{ openTables, setOpenTables }}>
      {children}
    </TableContext.Provider>
  );
};

// Update the CollapsibleTable component to use the context
const CollapsibleTable = ({ title, children, id }) => {
  const { openTables, setOpenTables } = useContext(TableContext);
  const isOpen = openTables.has(id);
  
  const toggleTable = () => {
    const newOpenTables = new Set(openTables);
    if (isOpen) {
      newOpenTables.delete(id);
    } else {
      newOpenTables.add(id);
    }
    setOpenTables(newOpenTables);
  };

  return (
    <div className="collapsible-table">
      <div 
        className="collapsible-header" 
        onClick={toggleTable}
      >
        <h4>{title}</h4>
        <span className="toggle-icon">{isOpen ? '▼' : '▶'}</span>
      </div>
      {isOpen && children}
    </div>
  );
};

// Add a loading animation component
const LoadingOverlay = () => (
  <div className="loading-overlay">
    <div className="loading-spinner"></div>
    <p>Analyzing your run...</p>
  </div>
);

const InfoTooltip = ({ text }) => (
  <span className="info-tooltip" title={text}>ⓘ</span>
);

const ErrorMessage = ({ message }) => (
  <div className="error-message">
    <span className="error-icon">⚠️</span>
    <p>{message}</p>
    <button className="retry-button" onClick={() => window.location.reload()}>
      Try Again
    </button>
  </div>
);

const SuccessMessage = ({ message }) => (
  <div className="success-message">
    <span className="success-icon">✓</span>
    <p>{message}</p>
  </div>
);

// Add this helper function near the top of your file
const calculateAveragePace = (segments) => {
  if (!segments || segments.length === 0) return 0;
  return segments.reduce((sum, segment) => sum + segment.pace, 0) / segments.length;
};

  const secs = Math.round((pace - mins) * 60);
  return <span>{mins}:{secs < 10 ? '0' + secs : secs}</span>;
};

// Modify the extractPaceValue function to add more debugging and better handling for slow pace
const extractPaceValue = (results, paceType) => {
  if (!results) return null;
  
  // For debugging
  if (paceType === 'slow') {
    console.log("Slow pace extraction:", {
      avg_pace_slow: results.avg_pace_slow,
      slow_pace: results.slow_pace,
      slow_segments: results.slow_segments,
      slow_distance: results.slow_distance,
      slow_time: results.slow_time
    });
    
    // If we have slow_time and slow_distance, calculate pace directly
    if (isFinite(results.slow_time) && isFinite(results.slow_distance) && results.slow_distance > 0) {
      const calculatedPace = results.slow_time / results.slow_distance;
      console.log("Calculated slow pace from time/distance:", calculatedPace);
      if (isFinite(calculatedPace) && calculatedPace > 0) {
        return calculatedPace;
      }
    }
  }
  
  // Existing logic
  if (paceType === 'fast') {
    if (isFinite(results.avg_pace_fast)) return results.avg_pace_fast;
    if (isFinite(results.fast_pace)) return results.fast_pace;
    
    // Calculate from segments if available
    if (results.fast_segments && results.fast_segments.length > 0) {
      return calculateAveragePace(results.fast_segments);
    }
  } else if (paceType === 'slow') {
    if (isFinite(results.avg_pace_slow)) return results.avg_pace_slow;
    if (isFinite(results.slow_pace)) return results.slow_pace;
    
    // Calculate from segments if available
    if (results.slow_segments && results.slow_segments.length > 0) {
      const segmentPaces = results.slow_segments
        .map(s => s.pace)
        .filter(pace => isFinite(pace) && pace > 0);
      
      if (segmentPaces.length > 0) {
        const avgPace = segmentPaces.reduce((sum, pace) => sum + pace, 0) / segmentPaces.length;
        console.log("Calculated slow pace from segments:", avgPace);
        return avgPace;
      }
    }
    
    // Last resort - if we have overall pace and fast pace, estimate slow pace
    if (isFinite(results.avg_pace_all) && isFinite(results.avg_pace_fast) &&
        isFinite(results.total_distance) && isFinite(results.fast_distance)) {
          
      const slowDistance = results.total_distance - results.fast_distance;
      if (slowDistance > 0) {
        const totalTime = results.avg_pace_all * results.total_distance;
        const fastTime = results.avg_pace_fast * results.fast_distance;
        const slowTime = totalTime - fastTime;
        const slowPace = slowTime / slowDistance;
        
        console.log("Estimated slow pace from overall and fast pace:", slowPace);
        return slowPace;
      }
    }
  } else if (paceType === 'overall') {
    if (isFinite(results.avg_pace_all)) return results.avg_pace_all;
    if (isFinite(results.avg_pace)) return results.avg_pace;
    if (isFinite(results.pace)) return results.pace;
  }
  
  return null; // Return null if no valid pace found
};

// Add this helper function to find mile splits from results
const findMileSplits = (results) => {
  // Function to detect if an array contains mile splits
  const isMileSplitsArray = (arr) => {
    if (!Array.isArray(arr) || arr.length === 0) return false;
    // Check if first item has typical mile split properties
    const firstItem = arr[0];
    return typeof firstItem === 'object' && 
           (firstItem.mile !== undefined || firstItem.split_number !== undefined) &&
           (firstItem.split_time !== undefined || firstItem.time !== undefined || 
            firstItem.split_pace !== undefined || firstItem.pace !== undefined);
  };
  
  // Search for any array that looks like mile splits
  const findMileSplitsArray = (obj, path = '') => {
    if (!obj || typeof obj !== 'object') return null;
    
    // Direct check for mile_splits property
    if (obj.mile_splits && isMileSplitsArray(obj.mile_splits)) {
      return obj.mile_splits;
    }
    
    // Check if this object itself is an array of mile splits
    if (Array.isArray(obj) && isMileSplitsArray(obj)) {
      return obj;
    }
    
    // Recursively search nested properties
    for (const key in obj) {
      if (obj[key] && typeof obj[key] === 'object') {
        const found = findMileSplitsArray(obj[key], `${path}.${key}`);
        if (found) return found;
      }
    }
    
    return null;
  };
  
  // Try to find mile splits in the results object
  let mileSplitsData = findMileSplitsArray(results);
  
  // If no mile splits found, generate them from segments
  if (!mileSplitsData || mileSplitsData.length === 0) {
    // Combine fast and slow segments
    const allSegments = [
      ...(results.fast_segments || []),
      ...(results.slow_segments || [])
    ].sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
    
    if (allSegments.length > 0 && results.total_distance) {
      // Generate approximate mile splits
      const syntheticSplits = [];
      
      let currentMileDistance = 0;
      let currentMileTime = 0;
      let currentMileHR = 0;
      let hrPointsCount = 0;
      let mileIndex = 1;
      
      // Process each segment to build up mile splits
      allSegments.forEach(segment => {
        const segmentDistance = segment.distance || 0;
        const remainingMileDistance = 1.0 - currentMileDistance;
        
        if (segmentDistance <= remainingMileDistance) {
          // Segment fits entirely within current mile
          currentMileDistance += segmentDistance;
          currentMileTime += segmentDistance * segment.pace;
          if (segment.avg_hr) {
            currentMileHR += segment.avg_hr;
            hrPointsCount++;
          }
        } else {
          // Segment crosses mile boundary
          // First, add contribution to current mile
          currentMileTime += remainingMileDistance * segment.pace;
          
          if (segment.avg_hr) {
            currentMileHR += segment.avg_hr;
            hrPointsCount++;
          }
          
          // Create current mile split
          syntheticSplits.push({
            mile: mileIndex,
            split_time: currentMileTime,
            split_pace: currentMileTime / 1.0, // Pace for exactly 1.0 miles
            avg_hr: hrPointsCount > 0 ? currentMileHR / hrPointsCount : 0
          });
          
          // Reset for next mile
          mileIndex++;
          const distanceUsed = remainingMileDistance;
          const distanceRemaining = segmentDistance - distanceUsed;
          
          // Process any complete miles within this segment
          const wholeMiles = Math.floor(distanceRemaining);
          if (wholeMiles > 0) {
            for (let i = 0; i < wholeMiles; i++) {
              syntheticSplits.push({
                mile: mileIndex,
                split_time: segment.pace, // Time for exactly 1.0 miles at this pace
                split_pace: segment.pace,
                avg_hr: segment.avg_hr || 0
              });
              mileIndex++;
            }
          }
          
          // Start a new partial mile with any remaining distance
          const leftover = distanceRemaining - wholeMiles;
          if (leftover > 0) {
            currentMileDistance = leftover;
            currentMileTime = leftover * segment.pace;
            currentMileHR = segment.avg_hr || 0;
            hrPointsCount = segment.avg_hr ? 1 : 0;
          } else {
            currentMileDistance = 0;
            currentMileTime = 0;
            currentMileHR = 0;
            hrPointsCount = 0;
          }
        }
      });
      
      // Add final partial mile if there's enough data
      if (currentMileDistance > 0.2) { // Only add if at least 0.2 miles
        syntheticSplits.push({
          mile: mileIndex,
          split_time: currentMileTime,
          split_pace: currentMileTime / currentMileDistance,
          avg_hr: hrPointsCount > 0 ? currentMileHR / hrPointsCount : 0,
          partial: true,
          distance: currentMileDistance
        });
      }
      
      if (syntheticSplits.length > 0) {
        mileSplitsData = syntheticSplits;
      }
    }
  }
  
  return mileSplitsData;
};

// Add a function to calculate the total pace from fast and slow segments
const calculateTotalPace = (results) => {
  if (!results) return null;
  
  // Method 1: If total distance and time are available, use them
  if (isFinite(results.total_distance) && isFinite(results.total_time) && 
      results.total_distance > 0 && results.total_time > 0) {
    return results.total_time / results.total_distance;
  }
  
  // Method 2: Calculate from fast and slow segments
  if (isFinite(results.fast_distance) && isFinite(results.slow_distance) && 
      isFinite(results.avg_pace_fast) && isFinite(results.avg_pace_slow) &&
      (results.fast_distance + results.slow_distance) > 0) {
    
    const fastTime = results.fast_distance * results.avg_pace_fast;
    const slowTime = results.slow_distance * results.avg_pace_slow;
    const totalTime = fastTime + slowTime;
    const totalDistance = results.fast_distance + results.slow_distance;
    
    return totalTime / totalDistance;
  }
  
  // Method 3: Calculate from segments directly
  if (results.fast_segments && results.slow_segments) {
    const fastSegments = results.fast_segments || [];
    const slowSegments = results.slow_segments || [];
    
    let totalDistance = 0;
    let totalTime = 0;
    
    // Add up fast segments
    for (const segment of fastSegments) {
      if (isFinite(segment.distance) && isFinite(segment.pace)) {
        totalDistance += segment.distance;
        totalTime += segment.distance * segment.pace;
      }
    }
    
    // Add up slow segments
    for (const segment of slowSegments) {
      if (isFinite(segment.distance) && isFinite(segment.pace)) {
        totalDistance += segment.distance;
        totalTime += segment.distance * segment.pace;
      }
    }
    
    if (totalDistance > 0) {
      return totalTime / totalDistance;
    }
  }
  
  // Method 4: Use any available pace directly
  if (isFinite(results.avg_pace_all)) return results.avg_pace_all;
  if (isFinite(results.avg_pace)) return results.avg_pace;
  if (isFinite(results.pace)) return results.pace;
  
  // No valid pace found
  return null;
};

// Helper function to calculate time from distance and pace
const calculateTimeFromPaceAndDistance = (pace, distance) => {
  if (!pace || !distance || pace === Infinity || isNaN(pace) || isNaN(distance)) {
    return 0;
  }
  return pace * distance; // This gives time in minutes
};

// Calculate total run time from segments
const calculateTotalRunTime = (results) => {
  if (!results) return 0;
  
  const fastSegments = results.fast_segments || [];
  const slowSegments = results.slow_segments || [];
  
  let totalTime = 0;
  
  // Add up time from fast segments
  for (const segment of fastSegments) {
    if (segment.time_diff) {
      totalTime += segment.time_diff;
    } else {
      totalTime += calculateTimeFromPaceAndDistance(segment.pace, segment.distance);
    }
  }
  
  // Add up time from slow segments
  for (const segment of slowSegments) {
    if (segment.time_diff) {
      totalTime += segment.time_diff;
    } else {
      totalTime += calculateTimeFromPaceAndDistance(segment.pace, segment.distance);
    }
  }
  
  return totalTime;
};

// Calculate time for fast segments
const calculateFastSegmentsTime = (results) => {
  if (!results || !results.fast_segments) return 0;
  
  let totalTime = 0;
  
  for (const segment of results.fast_segments) {
    if (segment.time_diff) {
      totalTime += segment.time_diff;
    } else {
      totalTime += calculateTimeFromPaceAndDistance(segment.pace, segment.distance);
    }
  }
  
  return totalTime;
};

// Calculate time for slow segments
const calculateSlowSegmentsTime = (results) => {
  if (!results || !results.slow_segments) return 0;
  
  let totalTime = 0;
  
  for (const segment of results.slow_segments) {
    if (segment.time_diff) {
      totalTime += segment.time_diff;
    } else {
      totalTime += calculateTimeFromPaceAndDistance(segment.pace, segment.distance);
    }
  }
  
  return totalTime;
};

function App() {
  const API_URL = 'http://localhost:5001';
  // Add the ref for the upload form
  const uploadFormRef = useRef(null);
  
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [runDate, setRunDate] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [saveStatus, setSaveStatus] = useState('');
  const [paceLimit, setPaceLimit] = useState(10);
  const [age, setAge] = useState('');
  const [restingHR, setRestingHR] = useState('');
  const [runHistory, setRunHistory] = useState([]);
  const [compareMode, setCompareMode] = useState(false);
  const [comparedRuns, setComparedRuns] = useState([]);
  const [userId, setUserId] = useState(null);
  const [username, setUsername] = useState('');
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [analysisVisible, setAnalysisVisible] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);

  // Define fetchRunHistory first
  const fetchRunHistory = useMemo(() => async () => {
    try {
      const response = await fetch(`${API_URL}/runs`, {
        credentials: 'include'
      });
      if (response.ok) {
        const text = await response.text();
        const data = safelyParseJSON(text);
        console.log('Run history data:', data);  // Debug log
        setRunHistory(data);
      }
    } catch (error) {
      console.error('Error loading run history:', error);
    }
  }, [API_URL]);

  // Now we can use fetchRunHistory in useEffect
  useEffect(() => {
    if (isAuthenticated) {
      fetchRunHistory();
    }
  }, [isAuthenticated, fetchRunHistory]);

  // Check authentication status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        console.log('Checking auth at:', `${API_URL}/auth/check`);
        const response = await fetch(`${API_URL}/auth/check`, {
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Auth check response:', data);
        if (data.authenticated) {
          setUserId(data.user_id);
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
          setUserId(null);
        }
      } catch (error) {
        console.error('Auth check error details:', error);
        console.log('Auth check failed:', error);
        setIsAuthenticated(false);
        setUserId(null);
      }
    };
    checkAuth();
  }, []);

  // Load profile on mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const response = await fetch(`${API_URL}/profile`, {
          credentials: 'include'
        });
        if (response.ok) {
      const data = await response.json();
          setAge(data.age?.toString() || '0');
          setRestingHR(data.resting_hr?.toString() || '0');
        } else {
          console.error('Failed to load profile');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
      }
    };

    if (userId) {
      loadProfile();
    }
  }, [userId]);

  const handleProfileSave = (newAge, newRestingHR) => {
    setAge(newAge.toString());
    setRestingHR(newRestingHR.toString());
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      setSelectedFile(null);
      setFileName('');
      setError('');
      return;
    }

    setSelectedFile(file);
    setFileName(file.name);
    setError('');

    // Read the file to extract date from GPX metadata
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      const timeMatch = content.match(/<time>(.*?)<\/time>/);
      
      if (timeMatch && timeMatch[1]) {
        // Extract the date part from ISO format (YYYY-MM-DDThh:mm:ssZ)
        const dateStr = timeMatch[1].split('T')[0];
        setRunDate(dateStr);
      } else {
        // Fallback to filename pattern or current date
        const dateMatch = file.name.match(/\d{4}-\d{2}-\d{2}/);
        if (dateMatch) {
          setRunDate(dateMatch[0]);
        } else {
          // If no date in filename, use current date
          const today = new Date();
          setRunDate(today.toISOString().split('T')[0]);
        }
      }
    };
    
    reader.readAsText(file);
  };

  const handleSaveRun = async (results) => {
    if (!runDate) {
      throw new Error('No run date available');
    }

    try {
      const response = await fetch(`${API_URL}/runs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          date: runDate,
          data: results
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to save run');
      }

      setSaveStatus('Run saved successfully!');
      await fetchRunHistory();
    } catch (error) {
      console.error('Error saving run:', error);
      throw error;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedFile) {
      setError('No file selected');
      return;
    }
    
    // Clear any previous results
    setResults(null);
    setAnalysisVisible(false);
    setError('');
    setSaveStatus('');
    setLoading(true);
    
    console.log('Uploading file:', selectedFile.name);
    console.log('File size:', selectedFile.size);
    console.log('File type:', selectedFile.type);
    
    // Create FormData
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('paceLimit', paceLimit);
    formData.append('age', age);
    formData.append('restingHR', restingHR);
    
    console.log('Form data:', Object.fromEntries(formData));
    
    try {
      console.log('Sending request to:', `${API_URL}/analyze`);
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        
        // Try to parse error with a reviver function that handles Infinity
        let errorData;
        try {
          errorData = JSON.parse(errorText, (key, value) => {
            if (value === "Infinity") return Infinity;
            if (value === "-Infinity") return -Infinity;
            if (value === "NaN") return NaN;
            return value;
          });
        } catch (parseError) {
          errorData = { error: 'Unknown error' };
        }
        
        throw new Error(errorData.error || 'Failed to analyze the run');
      }
      
      // Get response as text first
      const responseText = await response.text();
      
      // Try to parse directly with a reviver function that handles Infinity
      let data;
      try {
        data = JSON.parse(responseText, (key, value) => {
          if (value === "Infinity") return Infinity;
          if (value === "-Infinity") return -Infinity;
          if (value === "NaN") return NaN;
          return value;
        });
      } catch (parseError) {
        console.error("Direct JSON parsing failed, trying safelyParseJSON:", parseError);
        // Fall back to our custom parser if direct parsing fails
        data = safelyParseJSON(responseText);
        if (!data) {
          throw new Error('Failed to parse response from server');
        }
      }
      
      console.log('Analysis results received:', data);
      
      // Store the results
      setResults(data.data);
      setAnalysisVisible(true);  // Ensure analysis section is visible
      setSaveStatus(data.saved ? 'Run saved successfully!' : '');
      
      // Update run history after saving
      await fetchRunHistory();
      
    } catch (error) {
      console.error('Error during analysis:', error);
      setError(`Failed to analyze the run: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (userId, username) => {
    console.log('Login successful, setting state:', { userId, username });
    setUserId(userId);
    setUsername(username);
    setIsAuthenticated(true);
    // Wait a moment for session to be set before fetching data
    await new Promise(resolve => setTimeout(resolve, 100));
    fetchRunHistory();
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
      // Clear user authentication state
      setUserId(null);
      setUsername('');
      setIsAuthenticated(false);
      setUser(null);
      
      // Clear all analysis-related state
      setResults(null);
      setAnalysisVisible(false);
      setSelectedFile(null);
      setFileName('');
      setRunDate('');
      setSaveStatus('');
      setRunHistory([]);
      setCompareMode(false);
      setComparedRuns([]);
      
      // Reset any form data
      setPaceLimit(9.0);
      setShowUploadForm(false);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // Add a helper function for safe number formatting
  const formatNumber = (value, decimals = 2) => {
    return (value || 0).toFixed(decimals);
  };

  // Add this in your App.js component (after setting results)
  useEffect(() => {
    if (results) {
      console.log("Full results object:", results);
      
      // Analyze pace data structure
      const paceFields = Object.keys(results).filter(key => 
        key.toLowerCase().includes('pace') || 
        (Array.isArray(results[key]) && results[key][0] && 'pace' in results[key][0])
      );
      console.log("Pace-related fields:", paceFields);
      
      // Log segment structure if available
      if (results.fast_segments) {
        console.log("Fast segment example:", results.fast_segments[0]);
      }
      if (results.slow_segments) {
        console.log("Slow segment example:", results.slow_segments[0]);
      }
    }
  }, [results]);

  // Add useEffect for handling click outside
  useEffect(() => {
    // Function to handle clicks outside the upload form
    function handleClickOutside(event) {
      if (uploadFormRef.current && !uploadFormRef.current.contains(event.target) && showUploadForm) {
        setShowUploadForm(false);
      }
    }
    
    // Add event listener when the form is shown
    if (showUploadForm) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    // Clean up
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUploadForm]);

  // Update the viewAnalysis function to set the analysisVisible state
  const viewAnalysis = async (runId) => {
    try {
      // Set loading state
      setLoadingStates(prev => ({...prev, [`analysis_${runId}`]: true}));
      
      console.log(`Fetching analysis data for run: ${runId}`);
      
      // Fetch analysis data from the backend
      const response = await fetch(`${API_URL}/run/${runId}/analysis`, {
        credentials: 'include'
      });
      
      // Log full response details for debugging
      console.log(`Analysis response status: ${response.status}`);
      
      if (!response.ok) {
        // Try to parse error with a reviver function that handles Infinity
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText, (key, value) => {
            if (value === "Infinity") return Infinity;
            if (value === "-Infinity") return -Infinity;
            if (value === "NaN") return NaN;
            return value;
          });
        } catch (parseError) {
          console.error("Error parsing error response:", parseError);
          errorData = { error: 'Unknown error' };
        }
        
        console.error(`Error response from server:`, errorData);
        throw new Error(errorData.error || `Server returned ${response.status}`);
      }
      
      // Get response as text first
      const responseText = await response.text();
      
      // Try to parse directly with a reviver function that handles Infinity
      let analysisData;
      try {
        analysisData = JSON.parse(responseText, (key, value) => {
          if (value === "Infinity") return Infinity;
          if (value === "-Infinity") return -Infinity;
          if (value === "NaN") return NaN;
          return value;
        });
      } catch (parseError) {
        console.error("Direct JSON parsing failed, trying safelyParseJSON:", parseError);
        // Fall back to our custom parser if direct parsing fails
        analysisData = safelyParseJSON(responseText);
        if (!analysisData) {
          throw new Error('Failed to parse response from server');
        }
      }
      
      console.log(`Successfully retrieved analysis data for run ${runId}`, analysisData);
      
      // Ensure advanced metrics are copied to the top level from data if needed
      if (analysisData.data) {
        // Copy advanced metrics to top level if they exist in nested data
        if (analysisData.data.vo2max !== undefined && (analysisData.vo2max === undefined || analysisData.vo2max === null)) {
          console.log("Copying vo2max from nested data to top level");
          analysisData.vo2max = analysisData.data.vo2max;
        }
        
        if (analysisData.data.training_load !== undefined && (analysisData.training_load === undefined || analysisData.training_load === null)) {
          console.log("Copying training_load from nested data to top level");
          analysisData.training_load = analysisData.data.training_load;
        }
        
        if (analysisData.data.recovery_time !== undefined && (analysisData.recovery_time === undefined || analysisData.recovery_time === null)) {
          console.log("Copying recovery_time from nested data to top level");
          analysisData.recovery_time = analysisData.data.recovery_time;
        }
      }

      console.log("Final analysis data with metrics:", {
        vo2max: analysisData.vo2max,
        training_load: analysisData.training_load,
        recovery_time: analysisData.recovery_time
      });
      
      // Update the results state in the parent component to display the analysis
      setResults(analysisData);
      
      // Make sure the analysis section is visible
      setAnalysisVisible(true);
      
      // Scroll to analysis section
      const resultsElement = document.querySelector('.results');
      if (resultsElement) {
        resultsElement.scrollIntoView({ behavior: 'smooth' });
      } else {
        console.warn('Results section not found in DOM');
      }
      
    } catch (error) {
      console.error('Error loading analysis data:', error);
      alert('Failed to load analysis data. Please try again.');
    } finally {
      // Clear loading state
      setLoadingStates(prev => ({...prev, [`analysis_${runId}`]: false}));
    }
  };

  return (
    <ThemeProvider>
      <TableProvider>
        <div className="App">
          {loading && <LoadingSpinner />}
          {error && <ErrorMessage message={error} />}
          
          {!isAuthenticated ? (
            <LoginForm onLogin={handleLogin} />
          ) : (
            <>
              <header className="App-header">
                <div className="header-controls">
                  <ProfileMenu 
                    username={username}
                    age={age}
                    restingHR={restingHR}
                    onSave={handleProfileSave}
                    onLogout={handleLogout}
                    showUploadForm={showUploadForm}
                    setShowUploadForm={setShowUploadForm}
                  />
                </div>
                <h1>Running Analysis</h1>
              </header>
              
              <main className="App-main">
                {saveStatus && (
                  <div className="save-status">
                    {saveStatus}
                  </div>
                )}
                
                {showUploadForm && (
                  <>
                    <div className="modal-overlay" onClick={() => setShowUploadForm(false)}></div>
                    <div className="upload-form-container">
                      <form onSubmit={handleSubmit} className="upload-form" ref={uploadFormRef}>
                        <div className="upload-header">
                          <h2>Upload GPX File {runDate && `(${runDate})`}</h2>
                          <button 
                            type="button" 
                            className="close-upload-button"
                            onClick={() => setShowUploadForm(false)}
                          >
                            ×
                          </button>
                        </div>
                        
                        <div className="upload-container">
                          <label className="file-input-label" htmlFor="gpxFile">
                            <div className="file-input-text">
                              {fileName ? fileName : 'Choose GPX file'}
                            </div>
                            <div className="file-input-button">Browse</div>
                          </label>
                          <input
                            type="file"
                            id="gpxFile"
                            accept=".gpx"
                            onChange={handleFileChange}
                            className="file-input"
                            required
                          />
                        </div>
                        
                        <div className="form-group">
                          <label htmlFor="paceLimit">
                            Target Pace (min/mile)
                            <InfoTooltip text="Enter your target pace in minutes per mile. Segments below this pace will be considered 'fast'." />
                          </label>
                          <input
                            type="number"
                            id="paceLimit"
                            value={paceLimit}
                            onChange={(e) => setPaceLimit(e.target.value)}
                            step="0.01"
                            min="4"
                            max="20"
                            placeholder="Enter target pace"
                          />
                        </div>
                        
                        <button 
                          type="submit" 
                          className="submit-button"
                          disabled={loading}
                        >
                          {loading ? 'Analyzing...' : 'Analyze Run'}
                        </button>
                      </form>
                    </div>
                  </>
                )}

                {loading && <LoadingOverlay />}
                
                {results && analysisVisible && (
                  <div className="results">
                    <h2>Analysis Results for {(results.run_date || results.date) ? new Date(results.run_date || results.date).toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric'
                    }) : 'Current Run'}{results?.pace_limit ? ` (Target Pace of ${formatPace(results.pace_limit)} min/mile)` : ''}</h2>
                    
                    {/* Summary metrics section with cleaner grid layout */}
                    <div className="results-summary">
                      <div className="results-grid">
                        <div className="result-item">
                          <h3>Total Time</h3>
                          <p className="result-value">{formatRunTime(calculateTotalRunTime(results))}</p>
                          <p className="result-unit">h:mm:ss</p>
                          <div className="distance-item">
                            <p className="result-label">Total Distance</p>
                            <p className="result-value-secondary">{formatNumber(results?.total_distance || 0)}</p>
                            <p className="result-unit">miles</p>
                          </div>
                          <div className="avg-pace">
                            <p className="result-label">Average Pace</p>
                            <p className="result-value-secondary">
                              {formatPace(calculateTotalPace(results))}
                            </p>
                            <p className="result-unit">/mile</p>
                          </div>
                          <div className="hr-item">
                            <p className="result-label">Overall Heart Rate</p>
                            <p className="result-value-secondary">{formatNumber(results?.avg_hr_all || 0, 0)}</p>
                            <p className="result-unit">bpm</p>
                          </div>
                        </div>
                        
                        <div className="result-item">
                          <h3>Fast Time</h3>
                          <p className="result-value">{formatRunTime(calculateFastSegmentsTime(results))}</p>
                          <p className="result-unit">h:mm:ss</p>
                          <div className="distance-item">
                            <p className="result-label">Fast Distance</p>
                            <p className="result-value-secondary">{formatNumber(results?.fast_distance || 0)}</p>
                            <p className="result-unit">miles</p>
                          </div>
                          <p className="result-percentage">
                            ({formatNumber(results?.percentage_fast || 0, 1)}% of total)
                          </p>
                          <div className="avg-pace">
                            <p className="result-label">Average Pace</p>
                            <p className="result-value-secondary">
                              {formatPace(extractPaceValue(results, 'fast'))}
                            </p>
                            <p className="result-unit">/mile</p>
                          </div>
                          <div className="hr-item">
                            <p className="result-label">Heart Rate</p>
                            <p className="result-value-secondary">{formatNumber(results?.avg_hr_fast || 0, 0)}</p>
                            <p className="result-unit">bpm</p>
                          </div>
                        </div>

                        <div className="result-item">
                          <h3>Slow Time</h3>
                          <p className="result-value">{formatRunTime(calculateSlowSegmentsTime(results))}</p>
                          <p className="result-unit">h:mm:ss</p>
                          <div className="distance-item">
                            <p className="result-label">Slow Distance</p>
                            <p className="result-value-secondary">{formatNumber(results?.slow_distance || 0)}</p>
                            <p className="result-unit">miles</p>
                          </div>
                          <p className="result-percentage">
                            ({formatNumber(results?.percentage_slow || 0, 1)}% of total)
                          </p>
                          <div className="avg-pace">
                            <p className="result-label">Average Pace</p>
                            <p className="result-value-secondary">
                              {formatPace(extractPaceValue(results, 'slow'))}
                            </p>
                            <p className="result-unit">/mile</p>
                          </div>
                          <div className="hr-item">
                            <p className="result-label">Heart Rate</p>
                            <p className="result-value-secondary">{formatNumber(results?.avg_hr_slow || 0, 0)}</p>
                            <p className="result-unit">bpm</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Training zones section with clean card styling */}
                    <div className="analysis-section">
                      <h3 className="section-title">Training Zones</h3>
                      {results?.training_zones && (
                        <TrainingZones zones={results.training_zones} />
                      )}
                    </div>

                    {/* Route map with proper section styling */}
                    <div className="analysis-section">
                      <h3 className="section-title">Route Map</h3>
                      <RouteMap 
                        routeData={results?.route_data || []} 
                        fastSegments={results?.fast_segments || []} 
                        slowSegments={results?.slow_segments || []} 
                      />
                    </div>
                    
                    {/* Mile splits with consistent styling */}
                    <div className="analysis-section">
                      <h3 className="section-title">Mile Splits</h3>
                      {(() => {
                        // Find or generate mile splits data
                        const mileSplitsData = findMileSplits(results);
                        
                        if (mileSplitsData && mileSplitsData.length > 0) {
                          return (
                            <div className="table-container">
                              <table className="splits-table">
                                <thead>
                                  <tr>
                                    <th>Mile #</th>
                                    <th>Split Time</th>
                                    <th>Pace</th>
                                    <th>Heart Rate</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {mileSplitsData.map((split, index) => (
                                    <tr key={index}>
                                      <td>
                                        {split.mile || split.split_number || index + 1}
                                        {split.partial && ` (${split.distance.toFixed(2)} mi)`}
                                      </td>
                                      <td>{formatTime(split.split_time || split.time || 0)}</td>
                                      <td>{formatPace(split.pace || split.split_pace || 0)} min/mi</td>
                                      <td>{Math.round(split.avg_hr || split.hr || 0)} bpm</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          );
                        } else {
                          return (
                            <div className="no-splits-message">
                              Mile splits data not available for this run. 
                              <p className="no-splits-explanation">
                                Mile splits are generated during analysis and may not be available for all runs.
                              </p>
                            </div>
                          );
                        }
                      })()}
                    </div>
                    
                    {/* Segments section */}
                    <div className="analysis-section">
                      <h3 className="section-title">Segments Analysis</h3>
                      
                      <CollapsibleTable 
                        title={`Fast Segments (${results?.fast_segments?.length || 0})`}
                        id="fast-segments"
                      >
                        <table>
                          <thead>
                            <tr>
                              <th>Segment</th>
                              <th>Start Time</th>
                              <th>End Time</th>
                              <th>Distance</th>
                              <th>Pace</th>
                              <th>Best Pace</th>
                              <th>Heart Rate</th>
                            </tr>
                          </thead>
                          <tbody>
                            {results?.fast_segments?.map((segment, index) => (
                              <tr key={index}>
                                <td>{index + 1}</td>
                                <td>{new Date(segment.start_time).toLocaleTimeString()}</td>
                                <td>{new Date(segment.end_time).toLocaleTimeString()}</td>
                                <td>{formatNumber(segment.distance)} mi</td>
                                <td>{formatPace(segment.pace)} /mi</td>
                                <td>{segment.best_pace ? formatPace(segment.best_pace) : formatPace(segment.pace)} /mi</td>
                                <td>{formatNumber(segment.avg_hr)} bpm</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </CollapsibleTable>

                      <CollapsibleTable 
                        title={`Slow Segments (${results?.slow_segments?.length || 0})`}
                        id="slow-segments"
                      >
                        <table>
                          <thead>
                            <tr>
                              <th>Segment</th>
                              <th>Start Time</th>
                              <th>End Time</th>
                              <th>Distance</th>
                              <th>Pace</th>
                              <th>Best Pace</th>
                              <th>Heart Rate</th>
                            </tr>
                          </thead>
                          <tbody>
                            {results?.slow_segments?.map((segment, index) => (
                              <tr key={index}>
                                <td>{index + 1}</td>
                                <td>{new Date(segment.start_time).toLocaleTimeString()}</td>
                                <td>{new Date(segment.end_time).toLocaleTimeString()}</td>
                                <td>{formatNumber(segment.distance)} mi</td>
                                <td>{formatPace(segment.pace)} /mi</td>
                                <td>{segment.best_pace ? formatPace(segment.best_pace) : formatPace(segment.pace)} /mi</td>
                                <td>{formatNumber(segment.avg_hr)} bpm</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </CollapsibleTable>
                    </div>

                    {/* Advanced metrics section */}
                    <div className="analysis-section">
                      <h3 className="section-title">Advanced Metrics</h3>
                      {console.log('Advanced Metrics Data Raw:', results, {
                        vo2max: results.vo2max,
                        vo2maxType: results.vo2max ? typeof results.vo2max : 'undefined',
                        trainingLoad: results.training_load,
                        trainingLoadType: results.training_load ? typeof results.training_load : 'undefined',
                        recoveryTime: results.recovery_time,
                        recoveryTimeType: results.recovery_time ? typeof results.recovery_time : 'undefined',
                        dataStructure: results.data ? 'results contains data field' : 'no data field',
                        hasNestedData: results.data && results.data.vo2max ? true : false
                      })}
                      
                      {(() => {
                        // Extract metrics with fallbacks to handle different data structures
                        let vo2max = null;
                        let trainingLoad = null;
                        let recoveryTime = null;
                        
                        // Pretty print helper for debugging
                        const getDataLocation = () => {
                          // Figure out exactly where each piece of data is located
                          const locations = {
                            directVo2max: results?.vo2max !== undefined,
                            directTrainingLoad: results?.training_load !== undefined,
                            directRecoveryTime: results?.recovery_time !== undefined,
                            
                            nestedDataExists: results?.data !== undefined,
                            nestedVo2max: results?.data?.vo2max !== undefined,
                            nestedTrainingLoad: results?.data?.training_load !== undefined,
                            nestedRecoveryTime: results?.data?.recovery_time !== undefined
                          };
                          return locations;
                        };
                        
                        console.log('Advanced Metrics - Data Structure:', getDataLocation());
                        
                        // 1. Try direct access first (direct properties)
                        if (results?.vo2max !== undefined && results.vo2max !== null) {
                          vo2max = results.vo2max;
                          console.log('Found vo2max as direct property:', vo2max);
                        }
                        
                        if (results?.training_load !== undefined && results.training_load !== null) {
                          trainingLoad = results.training_load;
                          console.log('Found training_load as direct property:', trainingLoad);
                        }
                        
                        if (results?.recovery_time !== undefined && results.recovery_time !== null) {
                          recoveryTime = results.recovery_time;
                          console.log('Found recovery_time as direct property:', recoveryTime);
                        }
                        
                        // 2. Try data.* structure as fallback
                        if ((!vo2max || vo2max === null) && results?.data?.vo2max !== undefined) {
                          vo2max = results.data.vo2max;
                          console.log('Found vo2max in nested data property:', vo2max);
                        }
                        
                        if ((!trainingLoad || trainingLoad === null) && results?.data?.training_load !== undefined) {
                          trainingLoad = results.data.training_load;
                          console.log('Found training_load in nested data property:', trainingLoad);
                        }
                        
                        if ((!recoveryTime || recoveryTime === null) && results?.data?.recovery_time !== undefined) {
                          recoveryTime = results.data.recovery_time;
                          console.log('Found recovery_time in nested data property:', recoveryTime);
                        }
                        
                        // 3. Handle string values (parse if needed)
                        if (typeof vo2max === 'string') {
                          vo2max = parseFloat(vo2max);
                          console.log('Converted vo2max from string to number:', vo2max);
                        }
                        
                        if (typeof trainingLoad === 'string') {
                          trainingLoad = parseFloat(trainingLoad);
                          console.log('Converted training_load from string to number:', trainingLoad);
                        }
                        
                        if (typeof recoveryTime === 'string') {
                          recoveryTime = parseFloat(recoveryTime);
                          console.log('Converted recovery_time from string to number:', recoveryTime);
                        }
                        
                        // 4. Final result with all extracted metrics
                        console.log('Final extracted metrics:', { 
                          vo2max, 
                          trainingLoad, 
                          recoveryTime,
                          allPresent: vo2max && trainingLoad && recoveryTime ? 'YES' : 'NO' 
                        });
                        
                        return (
                          <AdvancedMetrics 
                            vo2max={vo2max}
                            trainingLoad={trainingLoad}
                            recoveryTime={recoveryTime}
                          />
                        );
                      })()}
                    </div>

                    {/* Race predictions section */}
                    {results?.race_predictions && (
                      <div className="analysis-section">
                        <h3 className="section-title">Race Predictions</h3>
                        <RacePredictions predictions={results.race_predictions} />
                      </div>
                    )}
                    
                    {/* Additional pace analysis if available */}
                    {results && results.pace_zones && (
                      <div className="analysis-section">
                        <h3 className="section-title">Pace Analysis</h3>
                        <PaceAnalysis 
                          results={results}
                          paceZones={results.pace_zones}
                          elevationImpact={results.elevation_impact}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Run History Section */}
                {!compareMode ? (
                  <>
                    <RunHistory 
                      runs={runHistory} 
                      onRunDeleted={handleRunDeleted}
                      onCompareRuns={(selectedRuns) => handleCompareRuns(selectedRuns)}
                      setResults={setResults}
                    />
                    
                    {/* Custom Segments Comparison */}
                    {runHistory && runHistory.length > 0 && (
                      <div className="custom-segments-container">
                        <h2>Custom Segment Comparison</h2>
                        <p className="segment-description">
                          Create and analyze custom segments across all your runs.
                          Define segments based on distance ranges and compare your performance.
                        </p>
                        <CustomSegments 
                          runs={runHistory}
                          currentRun={results}
                        />
                      </div>
                    )}
                  </>
                ) : (
                  <RunComparison 
                    runs={comparedRuns}
                    onClose={() => setCompareMode(false)}
                  />
                )}
              </main>
            </>
          )}
        </div>
      </TableProvider>
    </ThemeProvider>
  );
}

export default App;