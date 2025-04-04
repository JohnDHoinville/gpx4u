import React, { useState, useEffect, useMemo } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  Polyline,
  Tooltip as MapTooltip
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const RunMap = ({ routeData }) => {
  // Set a default center (we'll update it when we have data)
  const [center, setCenter] = useState([42.5, -83.2]); // Default to Michigan area
  
  useEffect(() => {
    // Calculate center from first valid segment
    if (routeData && routeData.length > 0) {
      const firstSegment = routeData[0];
      if (firstSegment.coordinates && firstSegment.coordinates.length > 0) {
        // Use the first coordinate of the first segment
        setCenter(firstSegment.coordinates[0]);
      }
    }
  }, [routeData]);

  // Process segments for display
  const processedSegments = useMemo(() => {
    if (!routeData || !routeData.length) return { line_types: [], sample_positions: [], total_lines: 0 };

    return {
      line_types: routeData.map(segment => ({
        type: segment.type,
        coordinates: segment.coordinates
      })),
      sample_positions: routeData.map(segment => segment.coordinates),
      total_lines: routeData.length
    };
  }, [routeData]);

  return (
    <div className="route-map">
      <MapContainer 
        center={center} 
        zoom={15} 
        style={{ height: '400px', width: '100%' }}
        key={`${center[0]}-${center[1]}`} // Force re-render when center changes
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {processedSegments.line_types.map((segment, index) => (
          <Polyline
            key={index}
            positions={segment.coordinates}
            pathOptions={{
              color: segment.type === 'fast' ? '#4CAF50' : '#FF5252',
              weight: 3
            }}
          >
            <MapTooltip>
              {`${segment.type.charAt(0).toUpperCase() + segment.type.slice(1)} Segment`}
            </MapTooltip>
          </Polyline>
        ))}
      </MapContainer>
    </div>
  );
};

export default RunMap; 