# EASM

## Quick start

1. Copy env file

```bash
cp .env.example .env
```

2. Start services

```bash
docker compose up --build
```

3. Run migrations (Docker)

```bash
docker compose exec api python -m alembic -c server/alembic.ini upgrade head
```

4. Health check

```bash
curl http://localhost:8000/health
```

## Environment variables

- `EASM_APP_ENV`: environment name (default: dev)
- `EASM_DATABASE_URL`: SQLAlchemy database URL
- `EASM_REDIS_URL`: Redis URL (default: `redis://redis:6379/0` in docker network)
- `EASM_AUTH_ENABLED`: enable API key auth (default: `true`)
- `EASM_API_KEYS`: comma-separated API keys for API access
- `EASM_API_KEY_PROJECT_MAP`: optional JSON ACL map for project-level authorization
- `EASM_SCAN_VERIFY_TLS`: verify TLS certificates for scanning (default: `true`)

## Common commands

```bash
# run api locally
uvicorn server.app.main:app --host 0.0.0.0 --port 8000

# run worker locally
celery -A worker.app.celery_app:celery_app worker -Q default -l info

# run alembic migrations (local venv)
EASM_DATABASE_URL=postgresql+psycopg://easm:easm@localhost:5432/easm \
  alembic -c server/alembic.ini upgrade head

# db connectivity check
python server/app/scripts/db_check.py
```
