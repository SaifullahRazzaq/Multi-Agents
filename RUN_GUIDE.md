# Running Frontend and Backend Together

## Quick Start

Run both frontend and backend with a single command:

```bash
npm run dev
```

This will start:
- **Backend** (FastAPI): http://localhost:8000
- **Frontend** (Vite/React): http://localhost:5173

## Available Scripts

### `npm run dev`
Runs both frontend and backend concurrently using the `concurrently` package.

### `npm run dev:backend`
Runs only the backend server (FastAPI with uvicorn).

### `npm run dev:frontend`
Runs only the frontend development server (Vite).

### `npm run install:all`
Installs all frontend dependencies.

## How It Works

The root `package.json` uses the `concurrently` package to run multiple npm scripts in parallel:

```json
{
  "scripts": {
    "dev": "concurrently \"npm run dev:backend\" \"npm run dev:frontend\"",
    "dev:backend": "cd backend && source venv/bin/activate && uvicorn server:app --reload --host 0.0.0.0 --port 8000",
    "dev:frontend": "cd frontend && npm run dev"
  }
}
```

## Troubleshooting

### Port Already in Use

If you get an error that port 8000 or 5173 is already in use:

```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

### Backend Not Starting

Make sure the Python virtual environment is set up:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Not Starting

Make sure frontend dependencies are installed:

```bash
cd frontend
npm install
```

## Stopping the Servers

Press `Ctrl+C` in the terminal to stop both servers.

## Current Status

✅ **Backend**: Running on http://localhost:8000
✅ **Frontend**: Running on http://localhost:5173

Both servers are configured with hot-reload, so changes will automatically restart the servers.
