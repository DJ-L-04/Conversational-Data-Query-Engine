# Conversational Data Query Engine

A REST API that lets users upload CSV/Excel files and query them in natural language using LangChain agents and OpenAI models. Includes Redis caching, PostgreSQL query history, JWT auth, and Docker support.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI |
| Database | PostgreSQL + SQLAlchemy |
| Caching | Redis |
| LLM Integration | LangChain + OpenAI API |
| Auth | JWT |
| Containerization | Docker + Docker Compose |
| CI | GitHub Actions |

## Features

- Upload CSV/Excel files via REST API
- Query uploaded files in natural language (GPT-3.5 or GPT-4)
- Redis caching — repeated queries return instantly without hitting the LLM
- PostgreSQL query history — full audit trail per file per user
- JWT authentication — each user can only access their own files
- File validation — type checking, size limits, parse validation

## Quick Start

```bash
git clone <repo-url>
cd chatbot
cp .env.example .env   # add your OPENAI_API_KEY

docker-compose up --build
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Running Locally

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start Postgres and Redis
docker-compose up db redis -d

uvicorn app.main:app --reload
```

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Create account |
| POST | /auth/login | Get access token |

### Files
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /files/upload | Upload CSV or Excel file |
| GET | /files/ | List my uploaded files |
| DELETE | /files/{file_id} | Delete a file |

### Query
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /query/ | Ask a question about a file |
| GET | /query/history/{file_id} | Query history for a file |
| GET | /query/history | All query history |

## Example Usage

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'

# 3. Upload file
curl -X POST http://localhost:8000/files/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@data.csv"

# 4. Query it
curl -X POST http://localhost:8000/query/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "<file_id>", "question": "What is the average sales value?", "model": "gpt-3.5-turbo"}'
```

## Running Tests

```bash
pytest tests/ -v
```
