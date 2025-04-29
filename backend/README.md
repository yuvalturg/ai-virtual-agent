# AI Virtual Assistant Backend

This is the backend for the AI Virtual Assistant project, built with FastAPI, SQLAlchemy (async), and PostgreSQL.

## Features
- Modular CRUD REST API for users, servers, knowledge bases, virtual assistants, chat history, and guardrails
- Async database access with SQLAlchemy and asyncpg
- Environment variable support via `.env` file
- Auto-generated interactive API docs (Swagger UI)

## Requirements
- Python 3.9+
- PostgreSQL database

## Setup

1. **Clone the repository and enter the backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the database connection:**
   - Copy or edit the provided `.env` file:
     ```env
     DATABASE_URL=postgresql+asyncpg://myuser:mypassword@localhost:5432/ai_virtual_assistant
     ```
   - Make sure the PostgreSQL user and database exist and have the correct privileges.

4. **Run the FastAPI server:**
   ```bash
   uvicorn backend.main:app --reload
   ```
   - Run this command from the project root (not from inside `backend/`).

5. **Access the API docs:**
   - Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser for the interactive Swagger UI.

## Project Structure
```
backend/
├── main.py               # FastAPI app entrypoint, includes routers
├── database.py           # Database connection and session
├── models.py             # SQLAlchemy models
├── schemas.py            # Pydantic schemas
├── routes/               # API route modules (users, servers, etc)
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not committed)
└── README.md             
```

## Useful Commands
- **Create a user (psql):**
  ```sql
  CREATE ROLE myuser WITH LOGIN PASSWORD 'mypassword';
  GRANT ALL PRIVILEGES ON DATABASE ai_virtual_assistant TO myuser;
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO myuser;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO myuser;
  ```
- **Hash a password (Python):**
  ```python
  import bcrypt
  password = b"mypassword"
  hashed = bcrypt.hashpw(password, bcrypt.gensalt())
  print(hashed.decode())
  ```

## Testing
- Use the Swagger UI or tools like `curl`, Postman, or httpie to interact with the API.

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string, loaded from `.env` automatically at startup.

---

For questions or issues, please contact the maintainer.
