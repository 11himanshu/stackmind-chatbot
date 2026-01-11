# Backend - FastAPI Chatbot API

## Setup

### macOS/Linux:

1. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Server:**
   ```bash
   python main.py
   ```
   
   Or with auto-reload:
   ```bash
   uvicorn main:app --reload
   ```

### Windows:

1. **Create Virtual Environment:**
   ```cmd
   python -m venv venv
   ```

2. **Activate Virtual Environment:**
   ```cmd
   venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run the Server:**
   ```cmd
   python main.py
   ```
   
   Or with auto-reload:
   ```cmd
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## Project Structure

- `main.py` - FastAPI application entry point
- `router.py` - Chat endpoints
- `auth_router.py` - Authentication endpoints
- `schemas.py` - Pydantic models
- `functions.py` - Chat business logic
- `auth_functions.py` - Authentication business logic

