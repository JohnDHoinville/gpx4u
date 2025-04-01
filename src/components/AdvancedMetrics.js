import React from 'react';
import './AdvancedMetrics.css';

// Enhanced InfoTooltip component with content directly embedded
const InfoTooltip = ({ content }) => (
  <span className="info-tooltip">
    ⓘ
    <div className="info-tooltip-content">
      {content}
    </div>
  </span>
);

const AdvancedMetrics = ({ vo2max, trainingLoad, recoveryTime }) => {
  // VO2 Max explanation content
  const vo2maxContent = (
    <div>
      <p><strong>About VO2 Max:</strong></p>
      <p>VO2 Max is the maximum amount of oxygen your body can utilize during intense exercise. It's a key indicator of aerobic fitness and endurance capacity.</p>
      <p><strong>How it's calculated:</strong></p>
      <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
        <li>Uses your heart rate data, pace, and personal metrics</li>
        <li>Higher values indicate better cardiovascular fitness</li>
        <li>Typical range: 30-60 ml/kg/min for recreational runners</li>
        <li>Elite endurance athletes: 70-85+ ml/kg/min</li>
      </ul>
      <p>Improve your VO2 Max with high-intensity interval training and consistent endurance workouts.</p>
    </div>
  );

  // Training Load explanation content
  const trainingLoadContent = (
    <div>
      <p><strong>About Training Load:</strong></p>
      <p>Training Load measures the total stress placed on your body during a workout. It combines intensity and duration into a single value.</p>
      <p><strong>How it's calculated:</strong></p>
      <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
        <li>Uses the Banister TRIMP (Training Impulse) formula</li>
        <li>Accounts for duration, average heart rate, and heart rate zones</li>
        <li>Higher values indicate more demanding workouts</li>
      </ul>
      <p>Training Load helps you balance harder and easier training days to optimize performance and prevent overtraining.</p>
    </div>
  );

  // Recovery Time explanation content
  const recoveryTimeContent = (
    <div>
      <p><strong>About Recovery Time:</strong></p>
      <p>Recovery Time is an estimate of how long your body needs to fully recover from this workout.</p>
      <p><strong>How it's calculated:</strong></p>
      <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
        <li>Based on your Training Load, resting heart rate, and age</li>
        <li>Accounts for workout intensity and your fitness level</li>
        <li>Older athletes typically need more recovery time</li>
      </ul>
      <p>This is a suggestion only - listen to your body and adjust training accordingly. Light activity during recovery periods can promote faster recovery.</p>
    </div>
  );

  return (
    <div className="advanced-metrics">
      <h3>Advanced Metrics</h3>
      <div className="metrics-grid">
        <div className="metric-item">
          <div className="metric-header">
            <h4>Estimated VO2 Max</h4>
            <InfoTooltip content={vo2maxContent} />
          </div>
          <p className="metric-value">{vo2max ? (vo2max + " ml/kg/min") : "Available with heart rate data"}</p>
          {vo2max && <p className="metric-unit">ml/kg/min</p>}
        </div>
        <div className="metric-item">
          <div className="metric-header">
            <h4>Training Load</h4>
            <InfoTooltip content={trainingLoadContent} />
          </div>
          <p className="metric-value">{trainingLoad ? trainingLoad : "Available with heart rate data"}</p>
          {trainingLoad && <p className="metric-unit">TRIMP</p>}
        </div>
        <div className="metric-item">
          <div className="metric-header">
            <h4>Recovery Time</h4>
            <InfoTooltip content={recoveryTimeContent} />
          </div>
          <p className="metric-value">
            {recoveryTime 
              ? (Math.floor(recoveryTime) + "h " + Math.round((recoveryTime % 1) * 60) + "m")
              : "Available with heart rate data"}
          </p>
          {recoveryTime && <p className="metric-unit">hours</p>}
        </div>
      </div>
    </div>
  );
};

export default AdvancedMetrics; 