import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
# SQLite by default; for PostgreSQL use e.g. postgresql+psycopg2://user:pass@host/db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tasks.db")
