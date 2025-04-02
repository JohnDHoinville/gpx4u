# Run Analysis Application

## Overview

Run Analysis is a comprehensive web application for runners to analyze their GPX data, track performance over time, and gain insights into their training. The application processes run data to provide detailed metrics, visualizations, and personalized training recommendations.

## Application Sections

### 1. User Authentication & Profile

- **Login/Register:** Secure user authentication system
- **User Profile:** Manage age, weight, resting heart rate, and other personal metrics
- **Theme Toggle:** Switch between light and dark mode for comfortable viewing

### 2. Run Analysis Dashboard

- **GPX Upload:** Upload and analyze GPX files from any GPS device
- **Pace Analysis:** Breakdown of fast and slow segments based on target pace
- **Heart Rate Zones:** Time spent in different heart rate training zones
- **Mile Splits:** Detailed pace information for each mile
- **Elevation Analysis:** Impact of elevation changes on pace
- **Route Map:** Interactive map showing the run route with color-coded pace segments
- **Advanced Metrics:** VO2max estimation, training load, and recovery time recommendations

### 3. Run History

- **History Table:** View all past runs with key metrics
- **Expandable Details:** Click to see fast segments and additional information
- **Run Comparison:** Select and compare two runs side-by-side
- **Run Deletion:** Remove unwanted entries from your history

### 4. Advanced Analysis Tools

- **Custom Segments:** Define and track specific portions of your routes over time
- **Pace Consistency:** Analyze how steady your pace is throughout your runs
- **Fatigue Analysis:** Track how your pace changes over the course of a run
- **Heart Rate vs. Pace Correlation:** Understand the relationship between effort and pace
- **Pace Progress Chart:** Track improvement in similar runs over time
- **Race Predictions:** Estimate race times for standard distances based on your data

## Technology Stack

### Frontend

- **React 18:** Component-based UI architecture
- **Chart.js 4:** Data visualization for pace, heart rate, and other metrics
- **Leaflet.js:** Interactive maps for route visualization
- **React-Chartjs-2:** React wrapper for Chart.js
- **React-Leaflet:** React components for Leaflet maps
- **CSS3:** Custom styling with responsive design
- **Context API:** State management for theme and table collapsing

### Backend

- **Flask 3.0:** Python web framework
- **SQLite:** Database for local development
- **PostgreSQL:** Database for production deployment
- **SQLAlchemy:** Database ORM for multi-database support
- **Flask-CORS:** Cross-origin resource sharing support
- **Python GPX Parser:** Custom GPX file processing
- **Werkzeug:** Security and authentication utilities
- **Gunicorn:** WSGI HTTP Server for production deployment
- **pytz/tzlocal:** Timezone handling

## Setup Instructions

### Prerequisites

- Python 3.8+ installed
- Node.js 14+ installed
- npm or yarn package manager
- Git (optional, for cloning the repository)

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:

   ```bash
   # For Windows
   python -m venv venv
   venv\Scripts\activate

   # For macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```
3. Install required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup

1. From the project root, install Node.js dependencies:
   ```bash
   npm install
   ```

## Running the Application

### Development Environment

#### Start the Backend Server

From the backend directory with the virtual environment activated:

```bash
python server.py
```

The backend will run on http://localhost:5001

#### Start the Frontend Development Server

From the project root:

```bash
npm start
```

The frontend will run on http://localhost:3000

### Production Environment

The application is configured for deployment on Render.com or similar platforms.

1. Set the following environment variables in your production environment:

   - `FLASK_ENV=production`
   - `SECRET_KEY=your-secret-key-here`
   - `DATABASE_URL=your-database-url` (for PostgreSQL)
   - `FRONTEND_URL=your-production-url`
2. The application uses the following build process:

   ```bash
   chmod +x build.sh && ./build.sh
   ```
3. For production, the backend serves the frontend static files, so you only need to run:

   ```bash
   cd backend && gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:app
   ```

## Authentication

The application uses session-based authentication. For development and testing, the following accounts are available:

- Admin Account:
  - Username: admin
  - Password: admin123

To reset a password for any account, you can use the provided script:

```bash
python update_password.py username password
```

## Troubleshooting

### Common Issues

#### Local Development

- **Backend Connection Error:** Ensure the Flask server is running on port 5001
- **Authentication Issues:** If you encounter login problems, try updating the password hash using the update_password.py script
- **Database Issues:** For schema changes, the backend will attempt to update tables automatically

#### Production Deployment

- **Static File 404 Errors:** Check the server.py file's static folder configuration
- **Database Connection Issues:** Verify the DATABASE_URL environment variable is set correctly
- **CORS Errors:** Ensure FRONTEND_URL is configured properly and Flask-CORS is installed
- **Persist data:** Persistant runs.db is set to /var/render/data

### Support

For additional help or to report issues, please open an issue on the repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
