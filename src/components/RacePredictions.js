import React from 'react';
import './RacePredictions.css';

// Enhanced InfoTooltip component with content directly embedded
const InfoTooltip = ({ content }) => (
  <span className="info-tooltip">
    ⓘ
    <div className="info-tooltip-content">
      {content}
    </div>
  </span>
);

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
  
  // Race predictions explanation for the tooltip
  const racePredictionsContent = (
    <div>
      <p><strong>About Race Predictions:</strong></p>
      <p>These predictions use the Riegel formula, a well-established method used by runners to estimate race times across different distances based on current performance.</p>
      <p><strong>How it works:</strong></p>
      <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
        <li>The system analyzes your fastest segments from this run</li>
        <li>It uses the formula: T2 = T1 × (D2/D1)<sup>1.06</sup></li>
        <li>Where T1 is your current performance time, D1 is the distance of that performance, T2 is the predicted time, and D2 is the race distance</li>
      </ul>
      <p>These times represent potential performance when properly trained for each specific distance.</p>
    </div>
  );

  return (
    <div className="race-predictions">
      <div className="section-title-with-info">
        <h3>Race Time Predictions</h3>
        <InfoTooltip content={racePredictionsContent} />
      </div>
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