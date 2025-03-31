from flask import Blueprint, request, jsonify, session
import traceback
from functools import wraps
from app.database import RunDatabase

profile_bp = Blueprint('profile_bp', __name__)
db = RunDatabase()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@profile_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        print(f"GET /profile - User ID: {session['user_id']}")
        profile = db.get_profile(session['user_id'])
        print(f"Profile retrieved: {profile}")
        return jsonify(profile)
    except Exception as e:
        print(f"Error getting profile: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/profile', methods=['POST'])
@login_required
def save_profile():
    try:
        print(f"POST /profile - User ID: {session['user_id']}")
        data = request.json
        print(f"Profile data received: {data}")
        
        age = data.get('age', 0)
        resting_hr = data.get('resting_hr', 0)
        weight = data.get('weight', 70)
        gender = data.get('gender', 1)
        
        print(f"Saving profile - Age: {age}, Resting HR: {resting_hr}, Weight: {weight}, Gender: {gender}")
        
        db.save_profile(
            user_id=session['user_id'],
            age=age,
            resting_hr=resting_hr,
            weight=weight,
            gender=gender
        )
        
        return jsonify({
            'message': 'Profile saved successfully',
            'age': age,
            'resting_hr': resting_hr,
            'weight': weight,
            'gender': gender
        })
    except Exception as e:
        print(f"Error saving profile: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500 