# GlobeGenius

GlobeGenius is a flight deal finder application that helps users discover and track the best flight deals.

## Features

- User authentication (signup, login)
- Flight deal discovery
- Price tracking and alerts
- User profile management
- Responsive UI for all devices
- Admin console with real-time API KPI dashboard
  - API usage statistics
  - Route performance metrics
  - Response time monitoring

## Tech Stack

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- Pydantic for data validation
- JWT for authentication
- PostgreSQL database (with SQLite for development)

### Frontend
- React.js
- React Router for navigation
- Context API for state management
- Tailwind CSS for styling
- Framer Motion for animations
- React Hook Form for form validation

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/maous26/Globegenuis.git
cd globegenius
```

2. Start the development environment:
```bash
./start-dev.sh
```

This script will:
- Start the backend server on http://localhost:8000
- Start the frontend server on http://localhost:3001

## Project Structure

- `/backend`: FastAPI backend application
- `/frontend`: React frontend application
- `/docker`: Docker configuration files

## 🔐 Authentication & Admin Dashboard

### Authentication System
GlobeGenius features a robust authentication system with multiple login options:

- **Email/Password Authentication**: Traditional login with secure password hashing
- **Google OAuth Integration**: One-click login with Google accounts
- **Admin Authorization**: Role-based access control for administrative functions
- **JWT Token Management**: Secure token-based session management

### Admin Dashboard Features
The admin dashboard provides comprehensive system monitoring and management:

#### 📊 **Overview Tab**
- Real-time system statistics (users, routes, deals, alerts)
- API quota usage monitoring with progress indicators
- Quick action buttons for manual route scanning
- System health status indicators

#### 🗺️ **Route Monitoring Tab**
- Route performance metrics with filtering and sorting
- Tier-based route organization (Tier 1, 2, 3)
- Individual route scanning capabilities
- Efficiency and discount tracking

#### 🔄 **Route Expansion Tab**
- Intelligent network expansion tools
- Smart route suggestions based on performance data
- Preview expansion before implementation
- Multiple expansion strategies (balanced, domestic, international, vacation)

#### ⚡ **API KPIs Tab**
- Real-time API usage statistics
- Monthly quota tracking and projections
- Response time and error rate monitoring
- Cost analysis and budget planning
- Recent API calls log with status tracking

#### 📅 **Seasonal Strategy Tab**
- Seasonal route planning and optimization
- Monthly route activation calendars
- Performance-based recommendations
- Seasonal trend analysis

#### 👥 **User Analytics Tab**
- User growth and engagement metrics
- Registration trends and demographic data
- Tier-based user distribution analysis
- Retention and activity tracking

#### 🏥 **System Health Tab**
- Real-time system status monitoring
- Scanner activity and performance metrics
- Error tracking and alerting
- Uptime and reliability statistics

### Error Handling & Reliability
- **Graceful Degradation**: All tabs load with fallback data if APIs fail
- **Comprehensive Error Messages**: Clear, user-friendly error descriptions
- **Automatic Retry Logic**: Built-in retry mechanisms for transient failures
- **CORS Configuration**: Robust cross-origin configuration for development

### Quick Start
```bash
# Start all services
./deploy_auth_fixes.sh

# Quick status check
./quick_check.sh

# Run validation tests
python3 validate_fixes.py

# Run comprehensive E2E tests
python3 e2e_test.py
```

### Admin Access
- **URL**: http://localhost:3001/admin
- **Email**: admin@globegenius.app
- **Password**: admin123

All admin dashboard components are designed to handle network issues gracefully, ensuring the interface remains responsive even when individual API endpoints experience temporary failures.