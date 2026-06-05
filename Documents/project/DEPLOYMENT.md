# Deployment Guide

This project consists of a FastAPI backend and a React frontend.

## Backend Deployment (FastAPI)

### Prerequisites
- Python 3.11+
- A Groq API Key (or other supported provider)

### Steps
1. **Environment Configuration**:
   Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Update `GROQ_API_KEY` and `CORS_ORIGIN` (set this to your deployed frontend URL).

2. **Installation**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Execution**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Frontend Deployment (React + Vite)

### Prerequisites
- Node.js 18+
- npm

### Steps
1. **Environment Configuration**:
   Create a `.env` file in the frontend root (or set via CI/CD):
   ```env
   VITE_WS_URL=wss://your-backend-api.azurewebsites.net/ws/research
   ```

2. **Build**:
   ```bash
   npm install
   npm run build
   ```

3. **Deployment**:
   Upload the `dist` folder to your hosting provider (e.g., Netlify, Vercel, Azure Static Web Apps).

## Security Considerations
- **API Keys**: Never commit the `.env` file. Use environment variables in your hosting platform.
- **CORS**: Restrict `CORS_ORIGIN` in the backend `.env` to only your official frontend domain.
- **WebSocket**: The `/ws/research` endpoint is public in this demo; for production, implement JWT authentication.
