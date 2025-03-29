// Determine the API URL based on the environment
let API_URL;

// Check for environment variables (when built)
if (process.env.REACT_APP_API_URL) {
  API_URL = process.env.REACT_APP_API_URL;
} else {
  // Check if we're in production based on hostname
  const isProduction = window.location.hostname !== 'localhost';
  
  if (isProduction) {
    // For production deployment on Render
    // This assumes backend and frontend are deployed to the same domain
    // with backend at the /api path
    API_URL = window.location.origin + '/api';
  } else {
    // For local development
    API_URL = 'http://localhost:5001';
  }
}

export { API_URL }; 