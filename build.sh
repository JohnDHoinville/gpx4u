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

# Build frontend with CI=false and DISABLE_ESLINT_PLUGIN=true to prevent warnings being treated as errors
echo "Building React application..."
CI=false DISABLE_ESLINT_PLUGIN=true npm run build

# Create static directory in backend
echo "Setting up static files..."
mkdir -p backend/static

# Copy frontend build to backend/static
echo "Copying frontend build files to backend..."
cp -r build/* backend/static/

echo "Build completed successfully!" 