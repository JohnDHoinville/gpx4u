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
    // In production, the backend serves the frontend from the same origin
    // So we use relative URLs which will be handled by the server
    API_URL = '';
  } else {
    // For local development
    API_URL = 'http://localhost:5001';
  }
}

console.log('API URL configured as:', API_URL);

export { API_URL }; 