#!/bin/bash
set -e

echo "Starting build process..."

# Install backend dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install frontend dependencies
echo "Installing Node.js dependencies..."
npm install

# Build frontend with CI=false to prevent warnings being treated as errors
echo "Building React application..."
CI=false npm run build

# Create static directory in backend
echo "Setting up static files..."
mkdir -p backend/static

# Copy frontend build to backend/static
echo "Copying frontend build files to backend..."
cp -r build/* backend/static/

echo "Build completed successfully!" 