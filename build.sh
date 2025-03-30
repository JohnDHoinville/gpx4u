#!/bin/bash
set -e

echo "Starting build process..."

# Check working directory
echo "Current directory: $(pwd)"
echo "Directory contents: $(ls -la)"

# Install backend dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Explicitly install Flask-CORS to ensure it's available
echo "Explicitly installing Flask-CORS..."
pip install Flask-CORS==4.0.0

# Install frontend dependencies
echo "Installing Node.js dependencies..."
npm install

# Build frontend with CI=false to prevent warnings being treated as errors
echo "Building React application..."
CI=false npm run build

# Verify that the build directory exists and contains files
echo "Checking build directory..."
if [ -d "build" ]; then
  echo "Build directory exists"
  echo "Build directory contents:"
  ls -la build/
  
  # Check for index.html specifically
  if [ -f "build/index.html" ]; then
    echo "build/index.html exists"
  else
    echo "ERROR: build/index.html does not exist!"
    exit 1
  fi
else
  echo "ERROR: Build directory does not exist!"
  exit 1
fi

# Create static directory in backend
echo "Setting up static files..."
mkdir -p backend/static

# Copy frontend build to backend/static with verbose output
echo "Copying frontend build files to backend..."
cp -rv build/* backend/static/

# Verify that files were copied
echo "Checking backend/static directory..."
if [ -d "backend/static" ]; then
  echo "backend/static directory exists"
  echo "backend/static directory contents:"
  ls -la backend/static/
  
  # Check for index.html specifically
  if [ -f "backend/static/index.html" ]; then
    echo "backend/static/index.html exists"
  else
    echo "ERROR: backend/static/index.html does not exist!"
    exit 1
  fi
else
  echo "ERROR: backend/static directory does not exist!"
  exit 1
fi

echo "Build completed successfully!" 