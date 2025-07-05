#!/bin/bash
# Start script for GlobeGenius development environment

echo "Starting GlobeGenius development environment..."

# Kill any running processes on the ports we need
echo "Cleaning up any existing processes..."
kill -9 $(lsof -ti:8000) 2>/dev/null || true
kill -9 $(lsof -ti:3003) 2>/dev/null || true

# Start the backend server
echo "Starting backend server..."
cd /Users/moussa/globegenius/backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend server started with PID: $BACKEND_PID"

# Give the backend server a moment to start
sleep 2

# Start the frontend server
echo "Starting frontend server..."
cd /Users/moussa/globegenius/frontend
PORT=3003 npm start &
FRONTEND_PID=$!
echo "Frontend server started with PID: $FRONTEND_PID"

echo "Development environment is now running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3003"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to clean up child processes when the script exits
cleanup() {
  echo "Shutting down services..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  exit 0
}

# Register the cleanup function for when the script is terminated
trap cleanup INT TERM

# Wait for user to stop the services
wait
