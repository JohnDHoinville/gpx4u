import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2, isnan
import traceback
import os
import glob
import json
from tzlocal import get_localzone
import pytz
import math

# Add these constants at the top
TRAINING_ZONES = {
    'Zone 1': {
        'name': 'Recovery',
        'range': (0.30, 0.40),  # 30-40% of HRR
        'description': 'Very light intensity, active recovery, improves basic endurance',
        'color': '#7FB3D5'  # Light blue
    },
    'Zone 2': {
        'name': 'Aerobic',
        'range': (0.40, 0.60),  # 40-60% of HRR
        'description': 'Light aerobic, fat burning, builds endurance',
        'color': '#2ECC71'  # Green
    },
    'Zone 3': {
        'name': 'Tempo',
        'range': (0.60, 0.70),  # 60-70% of HRR
        'description': 'Moderate intensity, improves efficiency and aerobic capacity',
        'color': '#F4D03F'  # Yellow
    },
    'Zone 4': {
        'name': 'Threshold',
        'range': (0.70, 0.85),  # 70-85% of HRR
        'description': 'Hard intensity, increases lactate threshold and speed',
        'color': '#E67E22'  # Orange
    },
    'Zone 5': {
        'name': 'VO2 Max',
        'range': (0.85, 1.00),  # 85-100% of HRR
        'description': 'Maximum effort, improves speed and power',
        'color': '#E74C3C'  # Red
    }
}

# Function to calculate distance using Haversine formula
def haversine(lat1, lon1, lat2, lon2):    
    R = 3956  # Radius of Earth in miles   
    dlat = radians(lat2 - lat1)    
    dlon = radians(lon2 - lon1)    
    a = (sin(dlat / 2) ** 2 +         
         cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2)    
    c = 2 * atan2(sqrt(a), sqrt(1 - a))    
    return R * c

# Parse datetime from ISO format
def parse_time(time_str):
    # Parse UTC time from GPX
    utc_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = pytz.utc.localize(utc_time)
    # Convert to local time
    local_tz = get_localzone()
    return utc_time.astimezone(local_tz)

# Add new downsampling functions
def needs_downsampling(gpx_file, threshold_points_per_minute=20, sample_minutes=2):
    """
    Determines if a GPX file needs downsampling by analyzing point frequency
    in the first few minutes of activity.
    
    Returns: (bool) True if downsampling is recommended
    """
    try:
        tree = ET.parse(gpx_file)
        root = tree.getroot()
        
        namespaces = {
            'gpx': 'http://www.topografix.com/GPX/1/1'
        }
        
        # Get all trackpoints
        track_points = root.findall('.//gpx:trkpt', namespaces)
        
        # Not enough points to worry about
        if len(track_points) < 50:
            return False
            
        # Get the timestamps from points
        times = []
        for point in track_points:
            time_elem = point.find('./gpx:time', namespaces)
            if time_elem is not None:
                try:
                    timestamp = datetime.strptime(time_elem.text, "%Y-%m-%dT%H:%M:%SZ")
                    times.append(timestamp)
                except (ValueError, TypeError):
                    continue
        
        # Not enough timestamped points
        if len(times) < 2:
            return False
            
        # Sort times (they should already be sorted, but just to be safe)
        times.sort()
        
        # Calculate the activity start time
        start_time = times[0]
        
        # Calculate the cutoff time (start_time + sample_minutes)
        cutoff_time = start_time + timedelta(minutes=sample_minutes)
        
        # Count points in the sample window
        points_in_window = sum(1 for t in times if t <= cutoff_time)
        
        # Calculate actual sample duration (in case activity is shorter than sample_minutes)
        actual_minutes = min(
            sample_minutes,
            (times[-1] - times[0]).total_seconds() / 60
        )
        
        # Calculate points per minute
        if actual_minutes > 0:
            points_per_minute = points_in_window / actual_minutes
            print(f"GPX file has {points_per_minute:.1f} points per minute")
            
            # Return True if points per minute exceeds threshold
            return points_per_minute > threshold_points_per_minute
        
        return False
    except Exception as e:
        print(f"Error checking if file needs downsampling: {str(e)}")
        return False

def downsample_gpx_smart(input_gpx_file, output_gpx_file, min_time_gap=3, pace_limit=None):
    """
    Smart downsampling that preserves heart rate trends and pace transition points.
    
    Args:
        input_gpx_file: Original GPX file path
        output_gpx_file: Path to save downsampled GPX
        min_time_gap: Minimum seconds between points (default 3)
        pace_limit: Target pace threshold to preserve transition points around
    """
    try:
        tree = ET.parse(input_gpx_file)
        root = tree.getroot()
        
        namespaces = {
            'gpx': 'http://www.topografix.com/GPX/1/1',
            'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1',
            'gpxx': 'http://www.garmin.com/xmlschemas/GpxExtensions/v3'
        }
        
        # Find all trackpoints
        track_points = []
        for trk in root.findall('.//gpx:trk', namespaces):
            for trkseg in trk.findall('.//gpx:trkseg', namespaces):
                for trkpt in trkseg.findall('.//gpx:trkpt', namespaces):
                    track_points.append(trkpt)
        
        if len(track_points) < 100:  # Only downsample files with lots of points
            print(f"Not enough trackpoints ({len(track_points)}) to downsample")
            return False
        
        print(f"Original file has {len(track_points)} trackpoints")
        
        # Adjust min_time_gap based on file frequency
        # If extremely high frequency (more than 1 point per second), be more aggressive
        points_per_minute = len(track_points) / 30  # Estimate for first 30 minutes
        if points_per_minute > 60:  # More than 1 point per second
            min_time_gap = max(min_time_gap, 5)  # Increase minimum time gap
            print(f"High frequency file detected, increasing minimum time gap to {min_time_gap} seconds")
        
        # Extract data for all points with pace calculation
        point_data = []
        previous_point = None
        
        for i, point in enumerate(track_points):
            # Extract lat/lon
            lat = float(point.get('lat'))
            lon = float(point.get('lon'))
            
            # Extract time
            time_elem = point.find('./gpx:time', namespaces)
            if time_elem is None:
                continue
            current_time = datetime.strptime(time_elem.text, "%Y-%m-%dT%H:%M:%SZ")
            
            # Extract heart rate
            hr_elem = None
            for path in ['.//gpxtpx:TrackPointExtension/gpxtpx:hr', './/gpx:extensions//hr', './/extensions//hr', './/hr']:
                try:
                    hr_elem = point.find(path, namespaces)
                    if hr_elem is not None:
                        break
                except:
                    continue
                    
            current_hr = int(hr_elem.text) if hr_elem is not None else None
            
            # Calculate time difference, distance, and pace if not first point
            time_diff = 0
            distance = 0
            pace = 0
            is_pace_transition = False
            current_pace_status = None
            
            if previous_point:
                time_diff = (current_time - previous_point['time']).total_seconds()
                
                # Calculate distance using Haversine
                if time_diff > 0:
                    distance = haversine(
                        previous_point['lat'], previous_point['lon'], 
                        lat, lon
                    )
                    
                    # Calculate pace (min/mile)
                    if distance > 0:
                        pace = (time_diff / 60) / distance
                        
                        # Check if this point represents a pace transition
                        if pace_limit:
                            current_pace_status = pace <= float(pace_limit)
                            
                            if previous_point.get('pace_status') is not None:
                                previous_pace_status = previous_point['pace_status']
                                
                                # Detect crossing the pace threshold
                                if current_pace_status != previous_pace_status:
                                    is_pace_transition = True
            
            # Calculate heart rate change if possible
            hr_change = 0
            if previous_point and previous_point['hr'] and current_hr:
                hr_change = abs(current_hr - previous_point['hr'])
                
            # Create point data entry
            point_item = {
                'index': i,
                'lat': lat,
                'lon': lon,
                'time': current_time,
                'time_diff': time_diff,
                'hr': current_hr,
                'hr_change': hr_change,
                'distance': distance, 
                'pace': pace,
                'is_pace_transition': is_pace_transition,
                'pace_status': current_pace_status
            }
            
            point_data.append(point_item)
            previous_point = point_item
        
        # Always keep first and last points
        points_to_keep = [0]
        if len(track_points) > 1:
            points_to_keep.append(len(track_points) - 1)
        
        # First pass: keep points based on time interval
        current_index = 0
        while current_index < len(point_data) - 1:  # Skip last point as we always keep it
            next_index = current_index + 1
            while next_index < len(point_data) - 1:
                if point_data[next_index]['time_diff'] >= min_time_gap:
                    points_to_keep.append(point_data[next_index]['index'])
                    current_index = next_index
                    break
                next_index += 1
            
            if next_index >= len(point_data) - 1:
                break
        
        # Second pass: add points with significant heart rate changes
        significant_hr_change = 5
        current_kept_point = 0
        
        for i in range(1, len(point_data) - 1):  # Skip first and last points
            if point_data[i]['index'] in points_to_keep:
                current_kept_point = i
                continue
                
            # Check if significant HR change from last kept point
            if (point_data[i]['hr'] is not None and 
                point_data[current_kept_point]['hr'] is not None and
                abs(point_data[i]['hr'] - point_data[current_kept_point]['hr']) > significant_hr_change):
                points_to_keep.append(point_data[i]['index'])
                current_kept_point = i
        
        # Third pass: add points that mark pace transitions
        if pace_limit:
            print(f"Looking for pace transitions around {pace_limit} min/mile")
            transition_points_added = 0
            
            for i in range(1, len(point_data) - 1):
                if point_data[i]['is_pace_transition']:
                    # Keep transition point and one point before and after
                    if i > 0 and point_data[i-1]['index'] not in points_to_keep:
                        points_to_keep.append(point_data[i-1]['index'])
                        transition_points_added += 1
                    
                    if point_data[i]['index'] not in points_to_keep:
                        points_to_keep.append(point_data[i]['index'])
                        transition_points_added += 1
                    
                    if i < len(point_data)-1 and point_data[i+1]['index'] not in points_to_keep:
                        points_to_keep.append(point_data[i+1]['index'])
                        transition_points_added += 1
            
            print(f"Added {transition_points_added} points to preserve pace transitions")
        
        # Sort indices to keep original order
        points_to_keep = sorted(set(points_to_keep))
        
        # For extremely high-frequency files, add further filtering 
        # if we're still keeping too many points
        if len(points_to_keep) > len(track_points) * 0.5:  # If keeping more than 50% of points
            print("Still keeping too many points, applying additional filtering")
            filtered_points = [points_to_keep[0]]  # Always keep first point
            
            # Keep only every Nth point except for pace transitions
            keep_every_n = 2
            transition_points = set()
            
            # Identify transition points
            for i in range(1, len(point_data) - 1):
                if point_data[i]['is_pace_transition']:
                    transition_points.add(point_data[i]['index'])
                    if i > 0:
                        transition_points.add(point_data[i-1]['index'])
                    if i < len(point_data)-1:
                        transition_points.add(point_data[i+1]['index'])
            
            # Filter points, keeping important ones
            for i in range(1, len(points_to_keep)-1):  # Skip first and last
                idx = points_to_keep[i]
                if idx in transition_points or i % keep_every_n == 0:
                    filtered_points.append(idx)
            
            # Always keep last point
            filtered_points.append(points_to_keep[-1])
            points_to_keep = filtered_points
        
        # Create a new GPX tree with only the kept points
        new_root = ET.Element(root.tag, root.attrib)
        
        # Copy all direct children except track
        for child in root:
            if child.tag.endswith('trk'):
                continue
            new_root.append(ET.Element(child.tag, child.attrib))
            for subchild in child:
                new_child = ET.SubElement(new_root.find(child.tag), subchild.tag, subchild.attrib)
                new_child.text = subchild.text
        
        # Create new track element
        for trk in root.findall('.//gpx:trk', namespaces):
            new_trk = ET.SubElement(new_root, trk.tag, trk.attrib)
            
            # Copy track name and other track metadata
            for child in trk:
                if child.tag.endswith('trkseg'):
                    continue
                new_trk_child = ET.SubElement(new_trk, child.tag, child.attrib)
                new_trk_child.text = child.text
            
            # Create new track segment
            for trkseg in trk.findall('.//gpx:trkseg', namespaces):
                new_trkseg = ET.SubElement(new_trk, trkseg.tag, trkseg.attrib)
                
                # Only add the track points we want to keep
                track_points_in_segment = trkseg.findall('.//gpx:trkpt', namespaces)
                segment_indices = range(len(track_points_in_segment))
                
                for i, trkpt in zip(segment_indices, track_points_in_segment):
                    if i in points_to_keep:
                        # Deep copy the track point with all its children
                        new_trkpt = ET.SubElement(new_trkseg, trkpt.tag, trkpt.attrib)
                        
                        # Copy all children of the track point
                        for child in trkpt:
                            new_child = ET.SubElement(new_trkpt, child.tag, child.attrib)
                            new_child.text = child.text
                            
                            # If this is an extensions element, copy all its children
                            if child.tag.endswith('extensions'):
                                for ext_child in child:
                                    new_ext_child = ET.SubElement(new_child, ext_child.tag, ext_child.attrib)
                                    new_ext_child.text = ext_child.text
                                    
                                    # Handle TrackPointExtension specifically
                                    if ext_child.tag.endswith('TrackPointExtension'):
                                        for tpx_child in ext_child:
                                            new_tpx_child = ET.SubElement(new_ext_child, tpx_child.tag, tpx_child.attrib)
                                            new_tpx_child.text = tpx_child.text
        
        # Write the new tree to file
        tree = ET.ElementTree(new_root)
        tree.write(output_gpx_file)
        
        # Count points in the new file
        new_tree = ET.parse(output_gpx_file)
        new_root = new_tree.getroot()
        new_points = new_root.findall('.//gpx:trkpt', namespaces)
        print(f"Downsampled file has {len(new_points)} trackpoints (reduced by {(1 - len(new_points)/len(track_points))*100:.1f}%)")
        
        return True
    except Exception as e:
        print(f"Error downsampling GPX file: {str(e)}")
        traceback.print_exc()
        return False

# Function to parse GPX data and calculate distance under specified pace
def analyze_run_file(file_path, pace_limit, user_age=None, resting_hr=None, weight=None, gender=None):
    try:
        print(f"\n=== Starting Run Analysis ===")
        print(f"File path: {file_path}")
        print(f"Pace limit: {pace_limit} min/mile")
        print(f"User metrics - Age: {user_age}, Resting HR: {resting_hr}")
        print(f"Additional metrics - Weight: {weight} (entered in lbs), Gender: {gender}")
        
        # Check if file needs downsampling
        is_high_frequency = needs_downsampling(file_path, threshold_points_per_minute=20, sample_minutes=2)
        print(f"High-frequency detection result: {is_high_frequency}")
        
        if is_high_frequency:
            print("High-frequency file detected, downsampling...")
            downsampled_path = f"{file_path}_downsampled.gpx"
            
            # Pass the pace_limit to the downsampling function
            success = downsample_gpx_smart(
                file_path, 
                downsampled_path, 
                min_time_gap=3,
                pace_limit=pace_limit
            )
            
            if success:
                print(f"Using downsampled file: {downsampled_path}")
                file_path = downsampled_path
            else:
                print("Downsampling failed, using original file")
        
        # Convert from lbs to kg
        weight_in_kg = weight * 0.453592
        
        # Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"GPX file not found at {file_path}")
        
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        print("Successfully parsed GPX file")
        
        ns = {
            'gpx': 'http://www.topografix.com/GPX/1/1',
            'ns3': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
        }
        
        # Add creator information from GPX metadata
        creator = root.get('creator')
        print(f"GPX creator: {creator}")
        
        # Initialize variables
        total_distance_all = 0
        total_hr = 0
        total_hr_count = 0
        point_segments = []
        fast_segments = []
        slow_segments = []
        total_fast_distance = 0
        total_slow_distance = 0
        elevation_data = []
        
        # Mile split tracking
        current_mile = 0
        mile_splits = []
        accumulated_distance = 0
        mile_start_time = None
        mile_hr_values = []   # Separate list for mile splits
        
        # Get local timezone
        local_tz = get_localzone()
        
        # Extract trackpoints
        trkpt_list = root.findall('.//gpx:trkpt', ns)
        print(f"Found {len(trkpt_list)} trackpoints")
        
        if not trkpt_list:
            print("No trackpoints found in GPX file")
            raise Exception("No trackpoints found in GPX file")
        
        # Add this to track all heart rates
        all_heart_rates = []  # Track all heart rates for the entire run
        
        # First pass: Process all points and create basic segments
        prev_point = None
        for trkpt in trkpt_list:
            try:
                lat = float(trkpt.get('lat'))
                lon = float(trkpt.get('lon'))
                time_elem = trkpt.find('.//gpx:time', ns)
                
                # Get elevation
                ele_elem = trkpt.find('.//gpx:ele', ns)
                elevation = float(ele_elem.text) if ele_elem is not None else 0
                
                # Get heart rate
                hr = None
                for path in ['.//ns3:TrackPointExtension/ns3:hr', './/gpx:extensions//hr', './/extensions//hr', './/hr']:
                    try:
                        hr_elem = trkpt.find(path, ns)
                        if hr_elem is not None:
                            hr = int(hr_elem.text)
                            all_heart_rates.append(hr)
                            break
                    except:
                        continue
                
                if time_elem is not None:
                    utc_time = datetime.strptime(time_elem.text, '%Y-%m-%dT%H:%M:%SZ')
                    utc_time = pytz.utc.localize(utc_time)
                    time = utc_time.astimezone(local_tz)
                    
                    if prev_point:
                        distance = haversine(prev_point['lat'], prev_point['lon'], lat, lon)
                        time_diff = (time - prev_point['time']).total_seconds() / 60
                        total_distance_all += distance
                        
                        if time_diff > 0:
                            # Calculate pace with safeguards for high-frequency files
                            if is_high_frequency and distance < 0.001:
                                # For very small distances in high-frequency files,
                                # use a moving average or skip individual pace calculations
                                pace = float('inf')  # We'll calculate this later in aggregation
                            else:
                                pace = time_diff / distance if distance > 0 else float('inf')
                            
                            point_segment = {
                                'lat': lat,
                                'lon': lon,
                                'elevation': elevation,
                                'time': time,
                                'hr': hr,
                                'distance': distance,
                                'pace': pace,
                                'is_fast': pace <= pace_limit if pace != float('inf') else False,
                                'prev_point': prev_point
                            }
                            point_segments.append(point_segment)
                    
                    prev_point = {
                        'lat': lat,
                        'lon': lon,
                        'time': time,
                        'hr': hr,
                        'elevation': elevation
                    }
                
            except Exception as e:
                print(f"Error processing point: {str(e)}")
                continue
        
        # Create continuous segments
        segments = []
        current_segment = None
        
        for i, point in enumerate(point_segments):
            if not current_segment:
                # Start new segment with proper coordinate format
                current_segment = {
                    'points': [point['prev_point']],
                    'is_fast': point['is_fast'],
                    'start_time': point['prev_point']['time'],
                    'distance': 0,
                    'total_hr': 0,
                    'hr_count': 0,
                    'coordinates': []  # Initialize empty coordinates array
                }
                # Add first coordinate
                current_segment['coordinates'].append([
                    float(point['prev_point']['lat']),
                    float(point['prev_point']['lon'])
                ])
            
            # Add current point to segment with proper coordinate format
            current_segment['points'].append(point)
            current_segment['coordinates'].append([
                float(point['lat']),
                float(point['lon'])
            ])
            current_segment['distance'] += point['distance']
            if point['hr']:
                current_segment['total_hr'] += point['hr']
                current_segment['hr_count'] += 1
            
            # Check if we need to end current segment
            next_point = point_segments[i + 1] if i < len(point_segments) - 1 else None
            if next_point and next_point['is_fast'] != current_segment['is_fast']:
                # Ensure the segment has valid coordinates
                if len(current_segment['coordinates']) >= 2:
                    finalized_segment = finalize_segment(current_segment)
                    if finalized_segment:  # Only add if finalize_segment returns a valid result
                        segments.append(finalized_segment)
                current_segment = None
        
        # Add final segment if it has enough points
        if current_segment and len(current_segment['coordinates']) >= 2:
            finalized_segment = finalize_segment(current_segment)
            if finalized_segment:  # Only add if finalize_segment returns a valid result
                segments.append(finalized_segment)
        
        # Split into fast and slow segments, ensuring each has valid coordinates
        fast_segments = [s for s in segments if s['is_fast'] and len(s['coordinates']) >= 2]
        slow_segments = [s for s in segments if not s['is_fast'] and len(s['coordinates']) >= 2]
        
        # Aggregating segments for high-frequency files
        if is_high_frequency:
            print("High-frequency file confirmed, aggregating short segments...")
            try:
                fast_segments = aggregate_short_segments(fast_segments, min_distance_threshold=0.01, min_time_threshold=5)
                slow_segments = aggregate_short_segments(slow_segments, min_distance_threshold=0.01, min_time_threshold=5)
                print(f"After aggregation: {len(fast_segments)} fast segments, {len(slow_segments)} slow segments")
            except Exception as agg_error:
                print(f"Error during segment aggregation: {str(agg_error)}")
                print(f"Continuing with original segments")
                traceback.print_exc()
        
        # Calculate totals
        total_fast_distance = sum(s['distance'] for s in fast_segments)
        total_slow_distance = sum(s['distance'] for s in slow_segments)
        
        # Calculate heart rate averages
        fast_hr_values = [s['avg_hr'] for s in fast_segments if s['avg_hr'] > 0]
        slow_hr_values = [s['avg_hr'] for s in slow_segments if s['avg_hr'] > 0]
        
        avg_hr_fast = sum(fast_hr_values) / len(fast_hr_values) if fast_hr_values else 0
        avg_hr_slow = sum(slow_hr_values) / len(slow_hr_values) if slow_hr_values else 0
        avg_hr_all = sum(all_heart_rates) / len(all_heart_rates) if all_heart_rates else 0
        
        # Debug output
        print(f"\nAnalysis complete:")
        print(f"Total distance: {total_distance_all:.2f} miles")
        print(f"Fast distance: {total_fast_distance:.2f} miles")
        print(f"Slow distance: {total_slow_distance:.2f} miles")
        print(f"Average HR (All): {avg_hr_all:.0f} bpm")
        print(f"Average HR (Fast): {avg_hr_fast:.0f} bpm")
        print(f"Average HR (Slow): {avg_hr_slow:.0f} bpm")
        
        # Format route data for mapping with proper coordinate format
        route_data = []
        for segment in segments:
            if segment and segment['coordinates'] and len(segment['coordinates']) >= 2:
                segment_data = {
                    'type': 'fast' if segment['is_fast'] else 'slow',
                    'coordinates': segment['coordinates'],
                    'pace': segment['pace'],
                    'distance': segment['distance'],
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time']
                }
                route_data.append(segment_data)

        # Debug output for route data
        print("\nRoute Data Check:")
        print(f"Number of route segments: {len(route_data)}")
        for i, seg in enumerate(route_data):
            print(f"Segment {i}: {seg['type']}, {len(seg['coordinates'])} points")
            print(f"First coordinate: {seg['coordinates'][0]}")
            print(f"Last coordinate: {seg['coordinates'][-1]}")

        # Calculate training zones
        # Calculate the average time between heart rate samples in seconds
        if len(point_segments) >= 2:
            total_time_seconds = (point_segments[-1]['time'] - point_segments[0]['time']).total_seconds()
            hr_sample_interval = total_time_seconds / len(all_heart_rates)
            print(f"Heart rate sampling interval: {hr_sample_interval:.2f} seconds")
        else:
            hr_sample_interval = 1.0  # Default to 1 second if we can't calculate
            
        training_zones = calculate_training_zones(all_heart_rates, user_age, resting_hr, hr_sample_interval)
        print("\nTraining Zones Result:")
        print(json.dumps(training_zones, indent=2))

        # Calculate additional metrics
        max_hr = max(all_heart_rates) if all_heart_rates else None
        duration_minutes = (point_segments[-1]['time'] - point_segments[0]['time']).total_seconds() / 60
        avg_hr = sum(all_heart_rates) / len(all_heart_rates) if all_heart_rates else None
        
        print("\nCalculating advanced metrics:")
        print(f"Max HR: {max_hr}")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Average HR: {avg_hr}")
        
        # Calculate VO2 Max
        vo2max = estimate_vo2max(
            age=user_age,
            weight=weight_in_kg,
            gender=gender,
            time_minutes=duration_minutes,
            distance_km=total_distance_all * 1.60934,  # Convert miles to km
            max_hr=max_hr
        )
        print(f"Calculated VO2 Max: {vo2max}")
        
        # Calculate training load
        training_load = calculate_training_load(
            duration_minutes=duration_minutes,
            avg_hr=avg_hr,
            max_hr=max_hr,
            resting_hr=resting_hr
        )
        print(f"Calculated Training Load: {training_load}")
        
        # Calculate recovery time
        recovery_time = recommend_recovery_time(
            training_load=training_load,
            resting_hr=resting_hr,
            age=user_age
        )
        print(f"Calculated Recovery Time: {recovery_time}")
        
        # Predict race times
        race_predictions = predict_race_times(
            [s['pace'] for s in fast_segments if s['pace'] != float('inf')]
        )
        print(f"Calculated Race Predictions: {race_predictions}")

        return {
            'total_distance': total_distance_all,
            'fast_distance': total_fast_distance,
            'slow_distance': total_slow_distance,
            'percentage_fast': (total_fast_distance/total_distance_all)*100 if total_distance_all > 0 else 0,
            'percentage_slow': (total_slow_distance/total_distance_all)*100 if total_distance_all > 0 else 0,
            'avg_hr_all': avg_hr_all,
            'avg_hr_fast': avg_hr_fast,
            'avg_hr_slow': avg_hr_slow,
            'fast_segments': fast_segments,
            'slow_segments': slow_segments,
            'route_data': route_data,
            'elevation_data': elevation_data,
            'mile_splits': mile_splits,
            'training_zones': training_zones,
            'pace_recommendations': get_pace_recommendations([s['pace'] for s in fast_segments if s['pace'] != float('inf')]),
            'pace_limit': float(pace_limit),
            'vo2max': vo2max,
            'training_load': training_load,
            'recovery_time': recovery_time,
            'race_predictions': race_predictions,
            'max_hr': max_hr,
            'creator': creator,
            'is_high_frequency': is_high_frequency
        }
        
    except Exception as e:
        print(f"\nError in analyze_run_file:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        traceback.print_exc()
        raise Exception(f"Failed to analyze run: {str(e)}")

def finalize_segment(segment):
    """Helper function to calculate segment statistics"""
    points = segment['points']
    time_diff = (points[-1]['time'] - segment['start_time']).total_seconds() / 60
    
    # Ensure coordinates are valid
    if not segment['coordinates'] or len(segment['coordinates']) < 2:
        print(f"Warning: Invalid coordinates in segment")
        return None
    
    # Calculate pace with safeguards against tiny distances
    if segment['distance'] > 0.005:  # Only trust distance if it's large enough
        pace = time_diff / segment['distance']
    else:
        # For very small distances, calculate speed from raw coordinates instead
        # and smooth over the entire segment
        total_dist = 0
        for i in range(1, len(points)):
            if 'lat' in points[i] and 'lon' in points[i] and 'lat' in points[i-1] and 'lon' in points[i-1]:
                point_dist = haversine(points[i-1]['lat'], points[i-1]['lon'], 
                                      points[i]['lat'], points[i]['lon'])
                total_dist += point_dist
        
        # Recalculate with the aggregated distance if it's more reliable
        if total_dist > segment['distance']:
            pace = time_diff / total_dist
        else:
            pace = time_diff / max(segment['distance'], 0.001)  # Prevent division by zero or tiny values
    
    # Handle heart rate data safely
    avg_hr = 0
    if segment.get('hr_count', 0) > 0 and segment.get('total_hr', 0) > 0:
        avg_hr = segment['total_hr'] / segment['hr_count']
    elif 'avg_hr' in segment:
        avg_hr = segment['avg_hr']
    
    # Create the segment with properly handling Infinity values
    result = {
        'is_fast': segment['is_fast'],
        'start_time': segment['start_time'],
        'end_time': points[-1]['time'],
        'distance': segment['distance'],
        'avg_hr': avg_hr,
        'total_hr': segment.get('total_hr', 0),
        'hr_count': segment.get('hr_count', 0),
        'coordinates': segment['coordinates'],
        'time_diff': time_diff,
        'pace': pace,
        'elevation_points': [float(p.get('elevation', 0)) for p in points if isinstance(p, dict)],
        'start_point': segment['coordinates'][0],
        'end_point': segment['coordinates'][-1]
    }
    
    # Add best_pace field (needed for compatibility with existing code)
    result['best_pace'] = pace
    
    return result

def aggregate_short_segments(segments, min_distance_threshold=0.01, min_time_threshold=5):
    """
    Aggregate short segments into more meaningful chunks.
    
    Args:
        segments: List of segment dictionaries
        min_distance_threshold: Minimum distance in miles for a segment (default 0.01 mile)
        min_time_threshold: Minimum time in seconds for a segment (default 5 seconds)
    
    Returns:
        List of aggregated segments
    """
    if not segments:
        return []
    
    print(f"Aggregating segments. Input: {len(segments)} segments")
    
    # Initialize with the first segment
    aggregated = []
    current = segments[0].copy()
    
    # Ensure required fields exist in the current segment
    if 'total_hr' not in current:
        current['total_hr'] = current.get('avg_hr', 0) * current.get('hr_count', 1)
    if 'hr_count' not in current:
        current['hr_count'] = 1 if current.get('avg_hr', 0) > 0 else 0
    
    # Track cumulative data for pace calculation
    cumulative_distance = current['distance']
    cumulative_time_seconds = (current['end_time'] - current['start_time']).total_seconds()
    
    for i in range(1, len(segments)):
        next_segment = segments[i]
        
        # Check if current segment is too short
        current_distance = current['distance']
        current_time_diff = (current['end_time'] - current['start_time']).total_seconds()
        
        if current_distance < min_distance_threshold or current_time_diff < min_time_threshold:
            # Merge the next segment into the current one
            current['end_time'] = next_segment['end_time']
            current['distance'] += next_segment['distance']
            current['coordinates'].extend(next_segment['coordinates'][1:])  # Avoid duplicating the connecting point
            
            # Update cumulative data for pace calculation
            cumulative_distance += next_segment['distance']
            segment_time = (next_segment['end_time'] - next_segment['start_time']).total_seconds()
            cumulative_time_seconds += segment_time
            
            # Safely merge HR data
            next_total_hr = 0
            next_hr_count = 0
            
            # Calculate next segment's total HR if needed
            if 'total_hr' in next_segment:
                next_total_hr = next_segment['total_hr']
            elif 'avg_hr' in next_segment and next_segment['avg_hr'] > 0:
                next_hr_count = next_segment.get('hr_count', 1)
                next_total_hr = next_segment['avg_hr'] * next_hr_count
            
            # Update current segment's HR data
            current['total_hr'] += next_total_hr
            current['hr_count'] += next_segment.get('hr_count', next_hr_count)
            
            # Update time difference
            current['time_diff'] = cumulative_time_seconds / 60  # Convert seconds to minutes
            
            # Recalculate pace from cumulative data
            if cumulative_distance > 0:
                current['pace'] = (cumulative_time_seconds / 60) / cumulative_distance
                current['best_pace'] = current['pace']
            
            # Update end point
            current['end_point'] = next_segment['end_point']
        else:
            # Current segment is large enough, save it and start a new one
            aggregated.append(current)
            current = next_segment.copy()
            
            # Reset cumulative tracking for new segment
            cumulative_distance = current['distance']
            cumulative_time_seconds = (current['end_time'] - current['start_time']).total_seconds()
            
            # Ensure required fields exist in the new current segment
            if 'total_hr' not in current:
                current['total_hr'] = current.get('avg_hr', 0) * current.get('hr_count', 1)
            if 'hr_count' not in current:
                current['hr_count'] = 1 if current.get('avg_hr', 0) > 0 else 0
    
    # Add the last segment
    if current:
        current_distance = current['distance']
        current_time_diff = (current['end_time'] - current['start_time']).total_seconds()
        
        # Only add if it meets the thresholds
        if current_distance >= min_distance_threshold and current_time_diff >= min_time_threshold:
            aggregated.append(current)
    
    # Final pass: calculate avg_hr for all segments and validate paces
    for segment in aggregated:
        if segment['hr_count'] > 0:
            segment['avg_hr'] = segment['total_hr'] / segment['hr_count']
        
        # Validate pace - ensure it's not unreasonably fast
        if segment['pace'] < 3.0:  # Faster than 3:00/mile is likely an error
            # Recalculate from time and distance
            time_minutes = (segment['end_time'] - segment['start_time']).total_seconds() / 60
            if segment['distance'] > 0 and time_minutes > 0:
                segment['pace'] = time_minutes / segment['distance']
                segment['best_pace'] = segment['pace']
    
    print(f"Aggregation complete. Output: {len(aggregated)} segments")
    return aggregated

def list_gpx_files(directory="~/Downloads"):
    # Expand the ~ to full home directory path
    directory = os.path.expanduser(directory)
    
    # Get all .gpx files in the directory
    gpx_files = glob.glob(os.path.join(directory, "*.gpx"))
    
    if not gpx_files:
        print(f"No GPX files found in {directory}")
        return None
        
    # Print the list of files
    print("\nAvailable GPX files:")
    for i, file_path in enumerate(gpx_files, 1):
        print(f"{i}. {os.path.basename(file_path)}")
    
    # Let user select a file
    while True:
        try:
            choice = int(input("\nEnter the number of the file you want to analyze (0 to quit): "))
            if choice == 0:
                return None
            if 1 <= choice <= len(gpx_files):
                return gpx_files[choice - 1]
            print("Please enter a valid number from the list.")
        except ValueError:
            print("Please enter a valid number.")

def save_run_results(file_path, pace_limit, results):
    log_file = "running_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_fast_distance, total_slow_distance, total_distance_all, 
    fast_segments, slow_segments, avg_hr_all, avg_hr_fast, avg_hr_slow,
    elevation_data, mile_splits, training_zones, pace_recommendations, route_data = results
    
    def format_time(iso_time_str):
        # Parse ISO format string and format for display
        try:
            dt = datetime.fromisoformat(iso_time_str)
            return dt.strftime('%I:%M:%S %p')  # Format as '11:23:45 AM'
        except:
            return iso_time_str
    
    # Format the results
    run_data = {
        "timestamp": timestamp,
        "gpx_file": os.path.basename(file_path),
        "pace_limit": pace_limit,
        "total_distance": round(total_distance_all, 2),
        "fast_distance": round(total_fast_distance, 2),
        "slow_distance": round(total_slow_distance, 2),
        "percentage_fast": round((total_fast_distance/total_distance_all)*100 if total_distance_all > 0 else 0, 1),
        "percentage_slow": round((total_slow_distance/total_distance_all)*100 if total_distance_all > 0 else 0, 1),
        "avg_hr_all": round(avg_hr_all, 0),
        "avg_hr_fast": round(avg_hr_fast, 0),
        "avg_hr_slow": round(avg_hr_slow, 0),
        "fast_segments": fast_segments,
        "slow_segments": slow_segments,
        "elevation_data": elevation_data,
        "mile_splits": mile_splits,
        "training_zones": training_zones,
        "pace_recommendations": pace_recommendations,
        "route_data": route_data
    }
    
    # Write to log file
    with open(log_file, "a") as f:
        f.write("\n" + "="*80 + "\n")
        f.write(f"Run Analysis - {timestamp}\n")
        f.write(f"File: {run_data['gpx_file']}\n")
        f.write(f"Pace Limit: {pace_limit} min/mile\n")
        f.write(f"Total Distance: {run_data['total_distance']} miles\n")
        f.write(f"Distance under {pace_limit} min/mile: {run_data['fast_distance']} miles ({run_data['percentage_fast']}%)\n")
        f.write(f"Distance over {pace_limit} min/mile: {run_data['slow_distance']} miles ({run_data['percentage_slow']}%)\n")
        f.write(f"Average Heart Rate (Overall): {run_data['avg_hr_all']} bpm\n")
        f.write(f"Average Heart Rate (Fast Segments): {run_data['avg_hr_fast']} bpm\n")
        f.write(f"Average Heart Rate (Slow Segments): {run_data['avg_hr_slow']} bpm\n")
        
        if fast_segments:
            f.write("\nFast Segments:\n")
            for i, segment in enumerate(fast_segments, 1):
                f.write(f"Segment {i}: {segment['distance']:.2f} miles at {segment['pace']:.1f} min/mile pace "
                       f"(Best: {segment['best_pace']:.1f}, Avg HR: {round(segment['avg_hr'])} bpm)\n")
                f.write(f"  Time: {format_time(segment['start_time'])} to {format_time(segment['end_time'])}\n")
        else:
            f.write("\nNo segments under target pace\n")
        
        if slow_segments:
            f.write("\nSlow Segments:\n")
            for i, segment in enumerate(slow_segments, 1):
                f.write(f"Segment {i}: {segment['distance']:.2f} miles at {segment['pace']:.1f} min/mile pace "
                       f"(Best: {segment['best_pace']:.1f}, Avg HR: {round(segment['avg_hr'])} bpm)\n")
                f.write(f"  Time: {format_time(segment['start_time'])} to {format_time(segment['end_time'])}\n")
        else:
            f.write("\nNo segments over target pace\n")
        
        f.write("\n")
    
    return run_data

def calculate_training_zones(heart_rates, user_age, resting_hr, hr_sample_interval=1.0):
    print("\nCalculating training zones:")
    print(f"Heart rates: {len(heart_rates)} values")
    print(f"User age: {user_age}")
    print(f"Resting HR: {resting_hr}")
    print(f"HR sample interval: {hr_sample_interval:.2f} seconds")
    
    if not heart_rates or not user_age or not resting_hr:
        print("Missing required data for training zones")
        return None
        
    # Calculate max HR using common formula
    max_hr = 220 - user_age
    heart_rate_reserve = max_hr - resting_hr
    
    print(f"Max HR: {max_hr}")
    print(f"Heart Rate Reserve: {heart_rate_reserve}")
    
    # Initialize zones with time spent
    zones = TRAINING_ZONES.copy()
    for zone in zones.values():
        zone['time_spent'] = 0
        zone['count'] = 0
        # Calculate actual heart rate ranges
        zone['hr_range'] = (
            int(resting_hr + (zone['range'][0] * heart_rate_reserve)),
            int(resting_hr + (zone['range'][1] * heart_rate_reserve))
        )
        print(f"Calculated HR range: {zone['hr_range']} for zone with HRR range {zone['range']}")
    
    # Count time spent in each zone
    for hr in heart_rates:
        hrr_percentage = (hr - resting_hr) / heart_rate_reserve
        
        for zone_name, zone_data in zones.items():
            if zone_data['range'][0] <= hrr_percentage <= zone_data['range'][1]:
                zone_data['time_spent'] += hr_sample_interval  # Use actual time interval between samples
                zone_data['count'] += 1
                break
    
    # Convert seconds to minutes and calculate percentages
    total_time = sum(zone['time_spent'] for zone in zones.values())
    print(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    
    for zone in zones.values():
        zone['time_spent'] = zone['time_spent'] / 60  # Convert to minutes
        zone['percentage'] = (zone['count'] / len(heart_rates) * 100) if heart_rates else 0
        zone.pop('count', None)  # Remove the count field
    
    # Add total duration for reference
    total_minutes = total_time / 60
    print(f"Total duration in all zones: {total_minutes:.2f} minutes")
    
    print("Calculated zones:", zones)
    return zones

def get_pace_recommendations(recent_paces):
    """Calculate pace zones based on recent performance"""
    # Filter out any invalid paces
    valid_paces = [p for p in recent_paces if p != float('inf') and p > 0]
    
    if not valid_paces:
        return None

    avg_pace = sum(valid_paces) / len(valid_paces)
    best_pace = min(valid_paces)

    return {
        'Recovery': {
            'range': (avg_pace * 1.4, avg_pace * 1.5),
            'description': 'Very easy running, for recovery days'
        },
        'Easy': {
            'range': (avg_pace * 1.2, avg_pace * 1.3),
            'description': 'Comfortable pace for building endurance'
        },
        'Long Run': {
            'range': (avg_pace * 1.1, avg_pace * 1.2),
            'description': 'Slightly faster than easy pace'
        },
        'Tempo': {
            'range': (best_pace * 1.05, best_pace * 1.1),
            'description': 'Comfortably hard, sustainable for 20-40 minutes'
        },
        'Interval': {
            'range': (best_pace * 0.9, best_pace * 0.95),
            'description': 'Fast pace for short intervals'
        }
    }

def calculate_pace_zones(recent_runs):
    """Calculate recommended pace zones based on recent performance"""
    if not recent_runs:
        return None

    # Get average and best paces from recent runs
    paces = []
    for run in recent_runs:
        # Use the data field from the dictionary
        run_data = json.loads(run['data']) if isinstance(run['data'], str) else run['data']
        fast_segments = run_data.get('fast_segments', [])
        if fast_segments:
            paces.extend([segment['pace'] for segment in fast_segments])

    if not paces:
        return None

    avg_pace = sum(paces) / len(paces)
    best_pace = min(paces)

    return {
        'Recovery': {
            'range': (avg_pace * 1.4, avg_pace * 1.5),
            'description': 'Very easy running, for recovery days'
        },
        'Easy': {
            'range': (avg_pace * 1.2, avg_pace * 1.3),
            'description': 'Comfortable pace for building endurance'
        },
        'Long Run': {
            'range': (avg_pace * 1.1, avg_pace * 1.2),
            'description': 'Slightly faster than easy pace'
        },
        'Tempo': {
            'range': (best_pace * 1.05, best_pace * 1.1),
            'description': 'Comfortably hard, sustainable for 20-40 minutes'
        },
        'Interval': {
            'range': (best_pace * 0.9, best_pace * 0.95),
            'description': 'Fast pace for short intervals'
        }
    }

def analyze_elevation_impact(point_segments):
    """Analyze how elevation affects pace"""
    elevation_pace_data = []
    for i in range(len(point_segments) - 1):
        current = point_segments[i]
        next_point = point_segments[i + 1]
        
        # Get elevation from start_point and end_point
        current_elevation = float(current.get('elevation', 0))
        next_elevation = float(next_point.get('elevation', 0))
        
        elevation_change = next_elevation - current_elevation
        pace = float(current.get('pace', 0))
        
        if not isnan(pace) and not isnan(elevation_change):
            elevation_pace_data.append({
                'elevation_change': elevation_change,
                'pace': pace,
                'distance': float(current.get('distance', 0))
            })
    
    return elevation_pace_data

def estimate_vo2max(age, weight, gender, time_minutes, distance_km, max_hr):
    """Estimate VO2 Max using heart rate and pace data"""
    if not all([age, weight, time_minutes, distance_km, max_hr]):
        print("VO2 Max calculation missing required data:", {
            'age': age, 'weight': weight, 'time': time_minutes,
            'distance': distance_km, 'max_hr': max_hr
        })
        return None
        
    speed_kmh = distance_km / (time_minutes / 60)
    print(f"VO2 Max calculation - Speed: {speed_kmh} km/h")
    # Use a standard formula: Modified Uth-Sörensen-Overgaard formula
    resting_hr = 60  # Fallback if not available
    vo2max = 15.3 * (max_hr / resting_hr)
    
    # Convert speed to min per km pace for adjustment
    pace_km = (time_minutes / distance_km)
    
    # Adjust based on speed - faster runners have higher VO2max
    if pace_km < 4.5:  # Faster than 4:30 min/km
        vo2max *= 1.15
    elif pace_km < 5.5:  # Faster than 5:30 min/km
        vo2max *= 1.05
    
    return round(vo2max, 1)

def calculate_training_load(duration_minutes, avg_hr, max_hr, resting_hr):
    """Calculate Training Load using Banister TRIMP"""
    if not all([duration_minutes, avg_hr, max_hr, resting_hr]):
        print("Training Load calculation missing required data:", {
            'duration': duration_minutes, 'avg_hr': avg_hr,
            'max_hr': max_hr, 'resting_hr': resting_hr
        })
        return None
        
    hrr_ratio = (avg_hr - resting_hr) / (max_hr - resting_hr)
    intensity = 0.64 * math.exp(1.92 * hrr_ratio)
    return duration_minutes * avg_hr * intensity

def recommend_recovery_time(training_load, resting_hr, age):
    """Recommend recovery time based on training load and personal metrics"""
    if not all([training_load, resting_hr, age]):
        return None
        
    base_recovery = training_load * 0.2  # Hours
    age_factor = 1 + max(0, (age - 30) * 0.02)
    hr_factor = 1 + max(0, (resting_hr - 60) * 0.01)
    return base_recovery * age_factor * hr_factor

def predict_race_times(recent_paces, distances=[5, 10, 21.1, 42.2]):
    """Predict race times using Riegel formula"""
    if not recent_paces:
        return None
        
    best_pace = min(recent_paces)
    base_time = best_pace * 5  # Use 5k as base
    
    predictions = {}
    for distance in distances:
        # Riegel formula: T2 = T1 * (D2/D1)^1.06
        predicted_time = base_time * (distance/5) ** 1.06
        predictions[f"{distance}k"] = predicted_time
        
    return predictions

def calculate_vo2max(avg_hr, max_hr, avg_pace, user_age, gender):
    """Calculate estimated VO2max using heart rate and pace data"""
    if not avg_hr or not avg_pace or not user_age:
        return None
    
    # Use Firstbeat formula (simplified version)
    # VO2max = 15.3 × HRmax/HRrest
    hrr = max_hr / avg_hr  # Heart rate ratio
    pace_factor = 60 / avg_pace  # Convert pace to speed factor
    
    # Adjust for age and gender
    age_factor = 1 - (user_age - 20) * 0.01 if user_age > 20 else 1
    gender_factor = 1.0 if gender == 1 else 0.85  # Male=1, Female=0
    
    vo2max = 15.3 * hrr * pace_factor * age_factor * gender_factor
    return round(vo2max, 1) if vo2max > 20 else None  # Only return reasonable values

def calculate_training_load(duration_minutes, avg_hr, resting_hr, max_hr=None):
    """Calculate training load using TRIMP (Training Impulse)"""
    if not duration_minutes or not avg_hr or not resting_hr:
        return None
    
    if not max_hr:
        max_hr = 220  # Default max HR if not provided
    
    # Calculate heart rate reserve (HRR) percentage
    hrr_percent = (avg_hr - resting_hr) / (max_hr - resting_hr)
    
    # Use Banister TRIMP formula
    gender_factor = 1.92  # Male factor (use 1.67 for female)
    trimp = duration_minutes * hrr_percent * 0.64 * math.exp(gender_factor * hrr_percent)
    
    return round(trimp) if trimp > 0 else None

def calculate_recovery_time(training_load, fitness_level=None):
    """Estimate recovery time based on training load"""
    if not training_load:
        return None
    
    # Basic formula: higher training load = longer recovery
    if not fitness_level:
        fitness_level = 1.0  # Default average fitness
        
    # Higher fitness = faster recovery
    base_recovery = training_load * 0.2  # Each TRIMP unit = 0.2 hours recovery
    adjusted_recovery = base_recovery / fitness_level
    
    return round(adjusted_recovery * 10) / 10  # Round to 1 decimal place

def main():
    # List and select GPX file
    file_path = list_gpx_files()
    
    if not file_path:
        print("No file selected. Exiting...")
        return
        
    # Get pace limit from user
    while True:
        try:
            pace_limit = float(input("Enter the pace limit (minutes per mile): "))
            if pace_limit > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
    
    result = analyze_run_file(file_path, pace_limit)
    
    # Save results to log file
    run_data = save_run_results(file_path, pace_limit, result)
    
    # Display results
    total_fast_distance, total_slow_distance, total_distance_all, 
    fast_segments, slow_segments, avg_hr_all, avg_hr_fast, avg_hr_slow,
    elevation_data, mile_splits, training_zones, pace_recommendations, route_data = result
    
    print(f"\nAnalyzing file: {file_path}")
    print(f"Total run distance: {total_distance_all:.2f} miles")
    print(f"Distance under {pace_limit} minute pace: {total_fast_distance:.2f} miles ({round((total_fast_distance/total_distance_all)*100, 1)}%)")
    print(f"Distance over {pace_limit} minute pace: {total_slow_distance:.2f} miles ({round((total_slow_distance/total_distance_all)*100, 1)}%)")
    print(f"Average Heart Rate (Overall): {round(avg_hr_all)} bpm")
    if total_distance_all > 0:
        print(f"Average Heart Rate (Fast Segments): {round(avg_hr_fast)} bpm")
        print(f"Average Heart Rate (Slow Segments): {round(avg_hr_slow)} bpm")
        
        if fast_segments:
            print("\nFast segment breakdown:")
            for i, segment in enumerate(fast_segments, 1):
                print(f"Segment {i}: {segment['distance']:.2f} miles at {segment['pace']:.1f} min/mile pace "
                      f"(Avg HR: {round(segment['avg_hr'])} bpm)")
                print(f"  Time: {segment['start_time']} to {segment['end_time']}")
        else:
            print("\nNo segments found under the target pace.")
            
    print(f"\nResults have been saved to {os.path.abspath('running_log.txt')}")

if __name__ == "__main__":
    main()