# Task Manager API (FastAPI + SQLite)

REST API with JWT authentication, task CRUD, filtering (all / completed / pending), search and pagination.

## Project structure
```
app/
  main.py        # app setup, CORS, global error handlers
  config.py      # env-based settings
  database.py    # SQLAlchemy engine/session
  models.py      # User, Task tables
  schemas.py     # Pydantic request/response models + validation
  security.py    # password hashing, JWT
  deps.py        # get_current_user dependency
  routers/auth.py, routers/tasks.py
tests/test_api.py
```

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # optional; defaults work for dev
uvicorn app.main:app --reload
```
Open **http://127.0.0.1:8000/docs** for interactive Swagger UI (use the *Authorize* button after logging in).

## Endpoints
| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Form (`username`, `password`) → JWT |
| GET | `/auth/me` | Current user |
| POST | `/tasks` | Create task |
| GET | `/tasks?status=all\|completed\|pending&search=&skip=0&limit=50` | List (filter, search, paginate) |
| GET | `/tasks/{id}` | Get one |
| PUT/PATCH | `/tasks/{id}` | Edit title / description / completed |
| PATCH | `/tasks/{id}/toggle` | Flip completed |
| DELETE | `/tasks/{id}` | Delete (204) |

All `/tasks` routes need `Authorization: Bearer <token>`; users only see their own tasks.

## Error format
```json
{"error": {"status": 422, "message": "Validation failed", "details": [{"field": "title", "message": "..."}]}}
```
Codes used: 201, 204, 401 (bad/missing token), 404 (not found / not yours), 409 (duplicate user), 422 (validation), 500 (DB error).

## Tests
```bash
pytest -q
```

## PostgreSQL
Set `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname` and `pip install psycopg2-binary`.

## Deploy (Render)
Build: `pip install -r requirements.txt` · Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
Set env vars `SECRET_KEY` and (recommended) a Postgres `DATABASE_URL`, since SQLite files are wiped on free tiers.
