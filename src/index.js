import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import 'leaflet/dist/leaflet.css';

// Add a patch for JSON.parse to handle Infinity values
const originalJSONParse = JSON.parse;
JSON.parse = function(text, reviver) {
  // Add a pre-processor for Infinity values
  const processedText = text
    .replace(/:Infinity,/g, ':"Infinity",')
    .replace(/:-Infinity,/g, ':"-Infinity",')
    .replace(/:NaN,/g, ':null,')
    .replace(/: Infinity/g, ': "Infinity"')
    .replace(/: -Infinity/g, ': "-Infinity"')
    .replace(/: NaN/g, ': null')
    .replace(/,Infinity/g, ',"Infinity"')
    .replace(/,-Infinity/g, ',"-Infinity"')
    .replace(/,NaN/g, ',null');
  
  // Create a custom reviver that wraps the original if it exists
  const customReviver = (key, value) => {
    // Convert strings back to their special values
    if (value === "Infinity") return Infinity;
    if (value === "-Infinity") return -Infinity;
    
    // Apply the original reviver if provided
    return reviver ? reviver(key, value) : value;
  };
  
  // Call the original JSON.parse with our pre-processed text and reviver
  return originalJSONParse(processedText, customReviver);
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
