# GlobeGenius

GlobeGenius is a flight deal finder application that helps users discover and track the best flight deals.

## Features

- User authentication (signup, login)
- Flight deal discovery
- Price tracking and alerts
- User profile management
- Responsive UI for all devices

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
- Start the frontend server on http://localhost:3003

## Project Structure

- `/backend`: FastAPI backend application
- `/frontend`: React frontend application
- `/docker`: Docker configuration files