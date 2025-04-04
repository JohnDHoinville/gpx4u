/**
 * Safely parses JSON with basic error handling
 * 
 * @param {string} jsonString - The JSON string to parse
 * @returns {object|null} The parsed object or null if parsing fails
 */
export const safelyParseJSON = (jsonString) => {
  try {
    if (!jsonString) {
      console.error("Empty JSON string");
      return null;
    }

    // If it's already an object, just return it
    if (typeof jsonString !== 'string') {
      return jsonString;
    }

    return JSON.parse(jsonString);
  } catch (error) {
    console.error("JSON parsing error:", error.message);
    return null;
  }
};

/**
 * Format a pace value from decimal minutes to mm:ss display
 * @param {number} pace - Pace in decimal minutes per mile
 * @returns {string} Formatted pace as mm:ss
 */
export const formatPace = (pace) => {
  if (pace === null || pace === undefined || !isFinite(pace)) {
    return 'N/A';
  }
  
  // Convert to minutes and seconds
  const minutes = Math.floor(pace);
  let seconds = Math.round((pace - minutes) * 60);
  
  // Handle case where seconds round up to 60
  if (seconds === 60) {
    seconds = 0;
    return `${minutes + 1}:00`;
  }
  
  // Pad seconds with leading zero if needed
  return `${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
}; 