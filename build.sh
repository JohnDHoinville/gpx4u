#!/bin/bash
set -e

echo "Starting build process..."

# Check working directory
echo "Current directory: $(pwd)"
echo "Directory contents: $(ls -la)"

# Install backend dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Explicitly install Flask-CORS and tzlocal to ensure they're available
echo "Explicitly installing Flask-CORS and tzlocal..."
pip install Flask-CORS==4.0.0 tzlocal==5.2.0

# Install frontend dependencies
echo "Installing Node.js dependencies..."
npm install

# Create .env.development.local to override any ESLint settings
echo "Creating .env.development.local..."
echo "DISABLE_ESLINT_PLUGIN=true" > .env.development.local
echo "SKIP_PREFLIGHT_CHECK=true" >> .env.development.local
echo "CI=false" >> .env.development.local

# Build frontend with CI=false and DISABLE_ESLINT_PLUGIN=true to prevent warnings being treated as errors
echo "Building React application..."
export CI=false
export DISABLE_ESLINT_PLUGIN=true
export SKIP_PREFLIGHT_CHECK=true
npm run build

# Create static directory in backend
echo "Setting up static files..."
mkdir -p backend/static

# Copy frontend build to backend/static
echo "Copying frontend build files to backend..."
cp -rv build/* backend/static/

# Debug information to verify file locations
echo "Listing backend/static directory:"
ls -la backend/static/
if [ -d "backend/static/static" ]; then
  echo "Listing backend/static/static directory:"
  ls -la backend/static/static/
  
  if [ -d "backend/static/static/js" ]; then
    echo "Listing JS files:"
    ls -la backend/static/static/js/
  fi
  
  if [ -d "backend/static/static/css" ]; then
    echo "Listing CSS files:"
    ls -la backend/static/static/css/
  fi
fi

echo "Build completed successfully!" 