# Chatbot Application

A full-stack chatbot application with FastAPI backend and React frontend.

## Project Structure

```
chatbot/
├── backend/           # FastAPI backend
│   ├── main.py
│   ├── router.py
│   ├── auth_router.py
│   ├── schemas.py
│   ├── functions.py
│   ├── auth_functions.py
│   └── requirements.txt
├── frontend/          # React frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Setup Instructions

### Backend Setup

#### macOS/Linux:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

#### Windows:
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Or using uvicorn directly:
- **macOS/Linux:** `uvicorn main:app --reload`
- **Windows:** `uvicorn main:app --reload`

The backend will run on `http://localhost:8000`

### Frontend Setup

#### macOS/Linux/Windows:
```bash
cd frontend
npm install
npm run dev
```

The frontend will run on `http://localhost:3000`

## API Endpoints

- `GET /health` - Health check
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /chat` - Send chat message
- `GET /conversations/{conversation_id}` - Get conversation history
- `DELETE /conversations/{conversation_id}` - Delete conversation

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Notes

- Backend uses in-memory storage (data is lost on restart)
- No password hashing implemented (for development only)
- CORS is enabled for all origins (change in production)

