# Deploying Run Analysis to Render

This guide outlines the steps to deploy the Run Analysis application to Render.

## Prerequisites

- A [Render](https://render.com/) account
- Git repository with your code

## Deployment Steps

### 1. Database Setup

1. In your Render dashboard, create a new PostgreSQL database:
   - Go to "New +" > "PostgreSQL"
   - Give it a name like `run-analysis-db`
   - Choose an appropriate plan (even the free tier works for small projects)
   - Click "Create Database"
   
2. Once created, note the following details from the database info page:
   - Internal Database URL (starts with `postgres://`)
   - These will be used as environment variables in your web service

### 2. Backend Deployment

1. In your Render dashboard, create a new Web Service:
   - Go to "New +" > "Web Service"
   - Connect your Git repository or use Render's GitHub integration
   - Give your service a name (e.g., `run-analysis-api`)
   - Set the Root Directory to the project root
   - Set the Build Command: `pip install -r requirements.txt`
   - Set the Start Command to the command in the Procfile: `cd backend && gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:app`

2. Configure Environment Variables:
   - In the "Environment" section, add the following key-value pairs:
     - `FLASK_APP`: `server.py`  
     - `FLASK_ENV`: `production`
     - `SECRET_KEY`: (generate a secure random key)
     - `DATABASE_URL`: (copy from your PostgreSQL service - Internal Database URL)
     - `FRONTEND_URL`: (URL of your frontend, once deployed)

3. Set the instance type (Free tier works for testing)

4. Click "Create Web Service"

### 3. Frontend Deployment

1. In your Render dashboard, create another Web Service for the frontend:
   - Go to "New +" > "Web Service"
   - Connect your repository
   - Give your service a name (e.g., `run-analysis-frontend`)
   - Set the Root Directory to the project root
   - Set the Build Command: `npm install && npm run build`
   - Set the Start Command: `npx serve -s build`

2. Configure Environment Variables:
   - `REACT_APP_API_URL`: (URL of your backend service, e.g., `https://run-analysis-api.onrender.com`)

3. Click "Create Web Service"

### 4. Environment Configuration

For separate deployments (frontend and backend on different services):

1. Update CORS settings in the backend to allow requests from the frontend domain:
   - Add your frontend URL to the `FRONTEND_URL` environment variable

### 5. Testing the Deployment

1. Wait for both services to build and deploy
2. Access your frontend URL
3. Test functionality to ensure the frontend can communicate with the backend
4. Check logs in the Render dashboard if you encounter issues

## Alternative Approach: Single Service Deployment

If you prefer to deploy both frontend and backend as a single service:

1. Create a `build.sh` script at the root of your project:
   ```sh
   #!/bin/bash
   # Install backend dependencies
   pip install -r requirements.txt
   
   # Install frontend dependencies and build
   npm install
   npm run build
   
   # Move frontend build to backend/static
   mkdir -p backend/static
   cp -r build/* backend/static/
   ```

2. Update the backend to serve static files:
   ```python
   # In server.py
   @app.route('/', defaults={'path': ''})
   @app.route('/<path:path>')
   def serve(path):
       if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
           return send_from_directory(app.static_folder, path)
       return send_from_directory(app.static_folder, 'index.html')
   ```

3. In Render, create a single Web Service:
   - Set the Build Command: `chmod +x build.sh && ./build.sh`
   - Set the Start Command: `cd backend && gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:app`

## Environment Variables for Render

| Variable Name | Description | Example Value |
|---------------|-------------|--------------|
| FLASK_APP | Flask application entry point | server.py |
| FLASK_ENV | Application environment | production |
| SECRET_KEY | Secret key for Flask sessions | (random string) |
| DATABASE_URL | PostgreSQL connection string | postgres://user:pass@host:port/db_name |
| FRONTEND_URL | URL of the frontend application | https://run-analysis.onrender.com |
| PORT | Port the application listens on (set by Render) | 10000 |

## Troubleshooting

- **Database Connection Issues**: Ensure the `DATABASE_URL` format is correct and accessible from the service
- **CORS Errors**: Check that the `FRONTEND_URL` is correctly set and that CORS is properly configured
- **Build Failures**: Check Render logs for errors during the build process
- **Application Errors**: Examine application logs in the Render dashboard 