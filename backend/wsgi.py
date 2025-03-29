from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import the Flask app
from server import app

if __name__ == '__main__':
    # Determine port from environment variable or use default
    port = int(os.environ.get('PORT', 5001))
    
    # In development, use localhost
    # In production, bind to all interfaces (0.0.0.0) for Render
    host = 'localhost' if os.environ.get('FLASK_ENV') == 'development' else '0.0.0.0'
    
    # Debug mode should only be enabled in development
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )