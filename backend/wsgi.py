from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import the Flask app
from server import app

if __name__ == '__main__':
    port = 5001  # Match React configuration
    app.run(
        host='localhost',
        port=port,
        debug=True
    )