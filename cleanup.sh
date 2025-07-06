#!/bin/bash
# Script to clean up the repository and fix source control issues

echo "Cleaning up the repository..."

# Remove node_modules and recreate it
echo "Removing node_modules..."
rm -rf ./frontend/node_modules

# Remove Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete

# Remove virtual environment
echo "Removing virtual environment..."
rm -rf ./backend/venv

# Remove any .DS_Store files
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -delete

# Reset git
echo "Resetting git repository..."
git reset

# Reinstall dependencies
echo "To reinstall dependencies, run:"
echo "cd ./frontend && npm install"
echo "cd ./backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

echo "Cleanup complete!"
