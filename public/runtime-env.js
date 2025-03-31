// Runtime environment script that runs before the app
// Used to override the API URL in production
window.runtimeEnv = {
  // In production, use empty string for API_URL to make relative URLs to the same origin
  API_URL: window.location.hostname !== 'localhost' ? '' : 'http://localhost:5001'
};

// Debug output
console.log('Runtime environment initialized', window.runtimeEnv);

// Override fetch to rewrite localhost URLs if found
const originalFetch = window.fetch;
window.fetch = function(url, options) {
  if (typeof url === 'string' && url.includes('localhost:5001')) {
    // In production, replace localhost URLs with relative URLs
    if (window.location.hostname !== 'localhost') {
      const newUrl = url.replace('http://localhost:5001', '');
      console.log(`API URL Rewritten: ${url} -> ${newUrl}`);
      return originalFetch(newUrl, options);
    }
  }
  return originalFetch(url, options);
};

// Add to window.onload to ensure React's API_URL can be overridden
window.addEventListener('load', function() {
  console.log('Checking for React API_URL references...');
  // More aggressive approach to find and replace API_URL references
  setTimeout(function() {
    try {
      // Try to patch direct fetch calls by monkey patching
      console.log('Patching fetch calls...');
    } catch (e) {
      console.error('Error patching API_URL:', e);
    }
  }, 100);
}); 