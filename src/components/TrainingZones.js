import React from 'react';
import './TrainingZones.css';

// Enhanced InfoTooltip component with content directly embedded
const InfoTooltip = ({ content }) => (
  <span className="info-tooltip">
    ⓘ
    <div className="info-tooltip-content">
      {content}
    </div>
  </span>
);

const TrainingZones = ({ zones }) => {
  console.log("TrainingZones component received zones:", zones);
  if (!zones) return null;

  // Helper function to safely display HR ranges
  const formatHRRange = (zoneData) => {
    if (!zoneData.hr_range || !Array.isArray(zoneData.hr_range)) {
      return null;
    }
    return `${zoneData.hr_range[0]}-${zoneData.hr_range[1]} bpm`;
  };

  // Training zone benefits information for the tooltip
  const zoneBenefitsContent = (
    <div>
      <p><strong>Benefits of Each Training Zone:</strong></p>
      <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
        <li><strong>Zone 1:</strong> Recovery, improves fat metabolism</li>
        <li><strong>Zone 2:</strong> Builds aerobic endurance, improves fat burning</li>
        <li><strong>Zone 3:</strong> Improves aerobic capacity and efficiency</li>
        <li><strong>Zone 4:</strong> Improves lactate threshold and speed endurance</li>
        <li><strong>Zone 5:</strong> Improves anaerobic capacity, maximum performance</li>
      </ul>
    </div>
  );

  return (
    <div className="training-zones">
      <div className="section-title-with-info">
        <h3>Heart Rate Training Zones</h3>
        <InfoTooltip content={zoneBenefitsContent} />
      </div>
      <div className="zones-grid">
        {Object.entries(zones).map(([zoneName, zoneData]) => (
          <div 
            key={zoneName} 
            className="zone-card"
            style={{ borderLeft: `4px solid ${zoneData.color}` }}
          >
            <div className="zone-header">
              <h4>{zoneName} - {zoneData.name}</h4>
              <span className="zone-ranges">
                <div className="zone-range hrr">
                  {Math.round(zoneData.range[0] * 100)}-{Math.round(zoneData.range[1] * 100)}% HRR
                </div>
                {formatHRRange(zoneData) && (
                  <div className="zone-range bpm">
                    {formatHRRange(zoneData)}
                  </div>
                )}
              </span>
            </div>
            <div className="zone-stats">
              <div className="zone-percentage">
                {Math.round(zoneData.percentage)}%
                <div 
                  className="percentage-bar" 
                  style={{ 
                    width: `${zoneData.percentage}%`,
                    backgroundColor: zoneData.color 
                  }} 
                />
              </div>
              <div className="zone-time">
                {Math.floor(zoneData.time_spent)}:{((zoneData.time_spent % 1) * 60).toFixed(0).padStart(2, '0')}
              </div>
            </div>
            <p className="zone-description">{zoneData.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TrainingZones; 