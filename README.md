# SentinelAI

AI-Powered Cybersecurity Threat Intelligence Platform

SentinelAI is a full-stack cybersecurity threat intelligence MVP built for a university final-year project and workshop demonstration. This foundation includes a runnable FastAPI backend, a React 18 + Vite frontend, Tailwind CSS styling, SQLite configuration, and a clean architecture folder layout ready for feature implementation.

## Tech Stack

- Frontend: React 18, Vite, Tailwind CSS, React Router, Axios, Chart.js, Lucide React
- Backend: Python 3.11, FastAPI, SQLAlchemy, SQLite, JWT-ready configuration, Passlib
- AI: Scikit-learn, Pandas, NumPy, Joblib

## Project Structure

```text
sentinel-ai/
  backend/
    app/
      api/v1/
      ai/
      config/
      db/
      models/
      repositories/
      schemas/
      services/
      utils/
    database/
    requirements.txt
  frontend/
    src/
      components/
      context/
      hooks/
      layouts/
      pages/
      services/
      utils/
    package.json
  database/
  logs/
  reports/
  uploads/
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The SQLite database is created automatically at `backend/database/sentinel.db` on first startup.

Health check:

```text
GET http://localhost:8000/api/v1/health
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

## Environment

Copy `.env.example` to `.env` in the project root or backend folder before production-style use. The default development settings are safe for local demonstration only.

## Current Status

This first milestone creates the complete runnable foundation. Business modules are intentionally not implemented yet. The next milestone is Authentication:

- Register
- Login
- JWT authentication
- Password hashing
- User profile
- Role support
- Protected frontend routes
