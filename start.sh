#!/bin/bash
# start.sh - Script de démarrage GlobeGenius
# Place this file in the root directory of your project

echo "🚀 Starting GlobeGenius..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Windows
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    IS_WINDOWS=true
else
    IS_WINDOWS=false
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python; then
    echo -e "${RED}❌ Python not found. Please install Python 3.9+${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js 16+${NC}"
    exit 1
fi

if ! command_exists psql; then
    echo -e "${RED}❌ PostgreSQL not found. Please install PostgreSQL 13+${NC}"
    exit 1
fi

if ! command_exists redis-cli; then
    echo -e "${RED}❌ Redis not found. Please install Redis 6+${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites found${NC}"

# Start services based on the argument
case "$1" in
    "backend")
        echo -e "${YELLOW}Starting backend services...${NC}"
        
        # Start PostgreSQL if not running
        if ! pg_isready -q; then
            echo "Starting PostgreSQL..."
            if [[ "$IS_WINDOWS" == true ]]; then
                net start postgresql-x64-13
            else
                sudo service postgresql start
            fi
        fi
        
        # Start Redis if not running
        if ! redis-cli ping > /dev/null 2>&1; then
            echo "Starting Redis..."
            if [[ "$IS_WINDOWS" == true ]]; then
                redis-server --daemonize yes
            else
                sudo service redis-server start
            fi
        fi
        
        cd backend
        
        # Activate virtual environment
        if [[ "$IS_WINDOWS" == true ]]; then
            source venv/Scripts/activate
        else
            source venv/bin/activate
        fi
        
        # Start backend services in background
        echo -e "${GREEN}Starting FastAPI...${NC}"
        uvicorn app.main:app --reload --port 8000 &
        FASTAPI_PID=$!
        
        sleep 3
        
        echo -e "${GREEN}Starting Celery Worker...${NC}"
        celery -A app.tasks.celery_app worker --loglevel=info &
        CELERY_WORKER_PID=$!
        
        sleep 2
        
        echo -e "${GREEN}Starting Celery Beat...${NC}"
        celery -A app.tasks.celery_app beat --loglevel=info &
        CELERY_BEAT_PID=$!
        
        echo -e "${GREEN}✅ Backend services started${NC}"
        echo "FastAPI PID: $FASTAPI_PID"
        echo "Celery Worker PID: $CELERY_WORKER_PID"
        echo "Celery Beat PID: $CELERY_BEAT_PID"
        
        # Wait for interrupt
        echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
        wait
        ;;
        
    "frontend")
        echo -e "${YELLOW}Starting frontend...${NC}"
        cd frontend
        npm start
        ;;
        
    "all")
        echo -e "${YELLOW}Starting all services...${NC}"
        
        # Start backend in background
        ./start.sh backend &
        BACKEND_PID=$!
        
        sleep 10
        
        # Start frontend
        cd frontend
        npm start
        ;;
        
    "stop")
        echo -e "${YELLOW}Stopping all services...${NC}"
        
        # Kill all Python processes (be careful with this)
        if [[ "$IS_WINDOWS" == true ]]; then
            taskkill //F //IM python.exe
        else
            pkill -f "uvicorn"
            pkill -f "celery"
        fi
        
        echo -e "${GREEN}✅ All services stopped${NC}"
        ;;
        
    "status")
        echo -e "${YELLOW}Checking service status...${NC}"
        
        # Check PostgreSQL
        if pg_isready -q; then
            echo -e "${GREEN}✅ PostgreSQL is running${NC}"
        else
            echo -e "${RED}❌ PostgreSQL is not running${NC}"
        fi
        
        # Check Redis
        if redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Redis is running${NC}"
        else
            echo -e "${RED}❌ Redis is not running${NC}"
        fi
        
        # Check FastAPI
        if curl -s http://localhost:8000/api/v1/health/ > /dev/null; then
            echo -e "${GREEN}✅ FastAPI is running${NC}"
        else
            echo -e "${RED}❌ FastAPI is not running${NC}"
        fi
        
        # Check Frontend
        if curl -s http://localhost:3000 > /dev/null; then
            echo -e "${GREEN}✅ Frontend is running${NC}"
        else
            echo -e "${RED}❌ Frontend is not running${NC}"
        fi
        ;;
        
    "init")
        echo -e "${YELLOW}Initializing project...${NC}"
        
        # Backend setup
        cd backend
        
        # Create virtual environment if it doesn't exist
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python -m venv venv
        fi
        
        # Activate virtual environment
        if [[ "$IS_WINDOWS" == true ]]; then
            source venv/Scripts/activate
        else
            source venv/bin/activate
        fi
        
        # Install dependencies
        echo "Installing backend dependencies..."
        pip install -r requirements.txt
        
        # Copy .env if it doesn't exist
        if [ ! -f ".env" ]; then
            echo "Creating .env file..."
            cp .env.example .env
            echo -e "${YELLOW}⚠️  Please edit backend/.env with your API keys${NC}"
        fi
        
        # Initialize database
        echo "Initializing database..."
        python init_db.py
        
        cd ..
        
        # Frontend setup
        cd frontend
        
        # Install dependencies
        echo "Installing frontend dependencies..."
        npm install
        
        # Create .env if it doesn't exist
        if [ ! -f ".env" ]; then
            echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env
        fi
        
        cd ..
        
        echo -e "${GREEN}✅ Project initialized successfully!${NC}"
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. Edit backend/.env with your API keys"
        echo "2. Run './start.sh all' to start all services"
        ;;
        
    *)
        echo "GlobeGenius Startup Script"
        echo ""
        echo "Usage: ./start.sh [command]"
        echo ""
        echo "Commands:"
        echo "  init      - Initialize the project (install dependencies, setup database)"
        echo "  backend   - Start backend services (API, Celery Worker, Celery Beat)"
        echo "  frontend  - Start frontend development server"
        echo "  all       - Start all services"
        echo "  stop      - Stop all services"
        echo "  status    - Check service status"
        echo ""
        echo "Example:"
        echo "  ./start.sh init     # First time setup"
        echo "  ./start.sh all      # Start everything"
        ;;
esac

# start.ps1 - PowerShell script for Windows users
# Create this as a separate file for Windows

<#
.SYNOPSIS
    GlobeGenius Startup Script for Windows

.DESCRIPTION
    Starts GlobeGenius services on Windows

.PARAMETER Command
    The command to execute (init, backend, frontend, all, stop, status)

.EXAMPLE
    .\start.ps1 init
    .\start.ps1 all
#>

param(
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Test-Prerequisites {
    Write-ColorOutput Yellow "Checking prerequisites..."
    
    $missing = @()
    
    if (!(Get-Command python -ErrorAction SilentlyContinue)) {
        $missing += "Python"
    }
    
    if (!(Get-Command node -ErrorAction SilentlyContinue)) {
        $missing += "Node.js"
    }
    
    if (!(Get-Command psql -ErrorAction SilentlyContinue)) {
        $missing += "PostgreSQL"
    }
    
    if (!(Get-Command redis-cli -ErrorAction SilentlyContinue)) {
        $missing += "Redis"
    }
    
    if ($missing.Count -gt 0) {
        Write-ColorOutput Red "❌ Missing prerequisites: $($missing -join ', ')"
        exit 1
    }
    
    Write-ColorOutput Green "✅ All prerequisites found"
}

switch ($Command) {
    "init" {
        Write-ColorOutput Yellow "Initializing project..."
        
        # Backend setup
        Set-Location backend
        
        if (!(Test-Path venv)) {
            Write-Host "Creating virtual environment..."
            python -m venv venv
        }
        
        # Activate virtual environment
        & .\venv\Scripts\Activate.ps1
        
        Write-Host "Installing backend dependencies..."
        pip install -r requirements.txt
        
        if (!(Test-Path .env)) {
            Write-Host "Creating .env file..."
            Copy-Item .env.example .env
            Write-ColorOutput Yellow "⚠️  Please edit backend\.env with your API keys"
        }
        
        Write-Host "Initializing database..."
        python init_db.py
        
        Set-Location ..
        
        # Frontend setup
        Set-Location frontend
        
        Write-Host "Installing frontend dependencies..."
        npm install
        
        if (!(Test-Path .env)) {
            "REACT_APP_API_URL=http://localhost:8000/api/v1" | Out-File .env
        }
        
        Set-Location ..
        
        Write-ColorOutput Green "✅ Project initialized successfully!"
    }
    
    "backend" {
        Test-Prerequisites
        Write-ColorOutput Yellow "Starting backend services..."
        
        Set-Location backend
        
        # Start services in separate PowerShell windows
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "& .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"
        Start-Sleep -Seconds 3
        
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "& .\venv\Scripts\Activate.ps1; celery -A app.tasks.celery_app worker --loglevel=info"
        Start-Sleep -Seconds 2
        
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "& .\venv\Scripts\Activate.ps1; celery -A app.tasks.celery_app beat --loglevel=info"
        
        Write-ColorOutput Green "✅ Backend services started in separate windows"
    }
    
    "frontend" {
        Write-ColorOutput Yellow "Starting frontend..."
        Set-Location frontend
        npm start
    }
    
    "all" {
        Test-Prerequisites
        
        # Start backend
        & $PSCommandPath backend
        
        Start-Sleep -Seconds 10
        
        # Start frontend in new window
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm start"
        
        Write-ColorOutput Green "✅ All services started"
    }
    
    "stop" {
        Write-ColorOutput Yellow "Stopping all services..."
        
        # Stop Python processes
        Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
        
        # Stop Node processes
        Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process -Force
        
        Write-ColorOutput Green "✅ All services stopped"
    }
    
    "status" {
        Write-ColorOutput Yellow "Checking service status..."
        
        # Check PostgreSQL
        try {
            psql -U postgres -c "SELECT 1" | Out-Null
            Write-ColorOutput Green "✅ PostgreSQL is running"
        } catch {
            Write-ColorOutput Red "❌ PostgreSQL is not running"
        }
        
        # Check Redis
        try {
            redis-cli ping | Out-Null
            Write-ColorOutput Green "✅ Redis is running"
        } catch {
            Write-ColorOutput Red "❌ Redis is not running"
        }
        
        # Check FastAPI
        try {
            Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health/" | Out-Null
            Write-ColorOutput Green "✅ FastAPI is running"
        } catch {
            Write-ColorOutput Red "❌ FastAPI is not running"
        }
        
        # Check Frontend
        try {
            Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing | Out-Null
            Write-ColorOutput Green "✅ Frontend is running"
        } catch {
            Write-ColorOutput Red "❌ Frontend is not running"
        }
    }
    
    default {
        Write-Host "GlobeGenius Startup Script for Windows"
        Write-Host ""
        Write-Host "Usage: .\start.ps1 [command]"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  init      - Initialize the project"
        Write-Host "  backend   - Start backend services"
        Write-Host "  frontend  - Start frontend server"
        Write-Host "  all       - Start all services"
        Write-Host "  stop      - Stop all services"
        Write-Host "  status    - Check service status"
    }
}