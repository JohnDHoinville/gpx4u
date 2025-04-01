import React from 'react';
import './RacePredictions.css';

const formatTime = (timeInMinutes) => {
  const hours = Math.floor(timeInMinutes / 60);
  const minutes = Math.floor(timeInMinutes % 60);
  const seconds = Math.round((timeInMinutes % 1) * 60);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

const RacePredictions = ({ predictions }) => {
  if (!predictions) return null;

  const distances = {
    '5k': 'Park Run (5K)',
    '10k': '10K',
    '21.1k': 'Half Marathon',
    '42.2k': 'Marathon'
  };

  // Convert distances from km to miles for display
  const distancesInMiles = {
    '5k': 3.11,
    '10k': 6.21,
    '21.1k': 13.1,
    '42.2k': 26.2
  };

  return (
    <div className="race-predictions">
      <h3>Race Time Predictions</h3>
      <div className="predictions-grid">
        {Object.entries(predictions).map(([distance, time]) => {
          // Get distance in km (remove 'k' and parse)
          const distanceKm = parseFloat(distance.replace('k', ''));
          // Get equivalent distance in miles
          const distanceMiles = distancesInMiles[distance];
          
          return (
            <div key={distance} className="prediction-card">
              <h4>{distances[distance] || distance}</h4>
              <p className="predicted-time">{formatTime(time)}</p>
              <p className="predicted-pace">
                {formatTime(time / distanceMiles)} /mi
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RacePredictions; 