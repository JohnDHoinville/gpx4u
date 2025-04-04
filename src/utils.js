/**
 * Safely parses JSON that may contain Infinity, -Infinity, or NaN values
 * which are not natively supported in the JSON specification.
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

    // Make sure we're working with a string
    if (typeof jsonString !== 'string') {
      console.error("Expected string input for JSON parsing");
      return jsonString; // Return as-is if it's already an object
    }

    // First approach - handle quoted Infinity values
    try {
      // Find unquoted Infinity values and quote them
      let sanitized = jsonString
        .replace(/:\s*Infinity/g, ':"Infinity"')
        .replace(/:\s*-Infinity/g, ':"Infinity"')
        .replace(/:\s*NaN/g, ':null')
        // Handle case where Infinity is the value in an array
        .replace(/,\s*Infinity/g, ',"Infinity"')
        .replace(/,\s*-Infinity/g, ',"-Infinity"')
        .replace(/,\s*NaN/g, ',null')
        // Handle case where Infinity is the first value in an array
        .replace(/\[\s*Infinity/g, '["Infinity"')
        .replace(/\[\s*-Infinity/g, '["Infinity"')
        .replace(/\[\s*NaN/g, '[null');
      
      return JSON.parse(sanitized, (key, value) => {
        if (value === "Infinity") return Infinity;
        if (value === "-Infinity") return -Infinity;
        return value;
      });
    } catch (firstError) {
      // If first approach fails, try more aggressive replacement
      console.warn("First JSON parse approach failed:", firstError.message);
      
      try {
        // More aggressive replacements
        const sanitized = jsonString
          .replace(/Infinity/g, '"Infinity"')
          .replace(/-Infinity/g, '"-Infinity"')
          .replace(/NaN/g, 'null')
          // Fix double quotes
          .replace(/""/g, '"')
          // Fix invalid JSON that might be created
          .replace(/":"/g, '":"')
          .replace(/"[:,]/g, '":');
        
        return JSON.parse(sanitized, (key, value) => {
          if (value === "Infinity") return Infinity;
          if (value === "-Infinity") return -Infinity;
          return value;
        });
      } catch (secondError) {
        // If all else fails, log error details and return null
        console.error("JSON parsing failed:", secondError);
        console.error("Problematic JSON:", jsonString.substring(0, 200) + "...");
        return null;
      }
    }
  } catch (e) {
    console.error("Error in safelyParseJSON:", e);
    return null;
  }
};

/**
 * Format a pace value from decimal minutes to mm:ss display
 * @param {number} pace - Pace in decimal minutes per mile
 * @returns {string} Formatted pace as mm:ss
 */
export const formatPace = (pace) => {
  if (pace === null || pace === undefined || isNaN(pace)) {
    return 'N/A';
  }
  
  if (pace === Infinity || pace === -Infinity) {
    return pace === Infinity ? '∞' : '-∞';
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