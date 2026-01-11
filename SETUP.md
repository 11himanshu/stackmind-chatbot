# Quick Setup Guide

## Backend Setup

### macOS/Linux:
Open a terminal and run these commands:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Windows:
Open a command prompt and run these commands:

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Backend will run on:** `http://localhost:8000`

## Frontend Setup

Open a **NEW** terminal/command prompt and run these commands:

```bash
cd frontend
npm install
npm run dev
```

**Frontend will run on:** `http://localhost:3000`

## To Stop Servers

Press `Ctrl+C` in each terminal window.

## To Deactivate Virtual Environment (Backend)

- **macOS/Linux/Windows:** `deactivate`

## Notes

- Make sure Python 3.8+ is installed
- Make sure Node.js and npm are installed
- Keep both terminals open while developing
- Backend must be running before using the frontend

