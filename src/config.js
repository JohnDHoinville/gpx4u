// Determine the API URL based on the environment
let API_URL;

// Check if we're in production based on hostname
const isProduction = 
  window.location.hostname !== 'localhost' && 
  window.location.hostname !== '127.0.0.1';

if (isProduction) {
  // In production, we use relative URLs (empty string)
  // This ensures all API calls go to the same server that serves the frontend
  API_URL = '';
  console.log('Production environment detected - using relative API URLs');
} else {
  // For local development
  API_URL = 'http://localhost:5001';
  console.log('Development environment detected - using localhost:5001 API URL');
}

console.log('API URL configured as:', API_URL);

export { API_URL }; 