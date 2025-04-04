import os
import tempfile
import shutil
import traceback
import math
from datetime import datetime
from flask import jsonify, request, send_from_directory
from app import app
from app.running import analyze_run_file, needs_downsampling, downsample_gpx_smart
from app.auth import authenticate_user, register_user, check_auth
from app.database import get_db

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Check if file is provided in the request
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        # Check if file has a name
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        print(f"Received file: {file.filename}")
        
        # Save the uploaded file to a temporary location
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        print(f"Saved file to: {file_path}")
        
        # Get pace limit from form data
        pace_limit = request.form.get('paceLimit', '10')
        age = request.form.get('age', None)
        resting_hr = request.form.get('restingHR', None)
        weight = request.form.get('weight', None)
        gender = request.form.get('gender', None)
        
        # Convert to correct types
        pace_limit = float(pace_limit)
        
        if age and age.strip():
            age = int(age)
        else:
            age = None
            
        if resting_hr and resting_hr.strip():
            resting_hr = int(resting_hr)
        else:
            resting_hr = None
            
        if weight and weight.strip():
            weight = float(weight)
        else:
            weight = None
            
        print(f"Analysis parameters: pace_limit={pace_limit}, age={age}, resting_hr={resting_hr}")
        
        # Check if this is a high-frequency file
        is_high_frequency = needs_downsampling(file_path)
        print(f"File detection: is_high_frequency={is_high_frequency}")
        
        if is_high_frequency:
            print("Detected high-frequency file, downsampling...")
            downsampled_path = os.path.join(temp_dir, "downsampled_" + file.filename)
            downsample_gpx_smart(file_path, downsampled_path)
            file_path = downsampled_path
            print(f"Downsampling complete, using {file_path}")
        
        # Analyze the run
        results = analyze_run_file(file_path, pace_limit, age, resting_hr, weight, gender)
        
        # Clean up the temp file
        shutil.rmtree(temp_dir)
        
        # Handle non-JSON-serializable values (like Infinity)
        def handle_non_serializable(obj):
            if isinstance(obj, dict):
                return {key: handle_non_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [handle_non_serializable(item) for item in obj]
            elif isinstance(obj, (int, float)) and not math.isfinite(obj):
                # Replace Infinity, -Infinity, or NaN with null
                return None
            elif isinstance(obj, datetime):
                # Handle datetime objects
                return obj.isoformat()
            return obj
        
        # Clean the results before sending
        cleaned_results = handle_non_serializable(results)
        
        print("Analysis completed successfully")
        return jsonify(cleaned_results)
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500 