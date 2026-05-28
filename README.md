# Running Stats Dashboard Backend

Backend for a running analytics platform: GPS processing, pace/splits, and personalized training recommendations.

## Tech stack

- **API:** FastAPI (Python 3.12+)
- **Database:** PostgreSQL (async via asyncpg)
- **Cache / broker:** Redis
- **Background jobs:** Celery
- **GPS:** gpxpy, geopy, Shapely

## Setup

### Local (no Docker)

1. Create a virtualenv and install dependencies:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set `DATABASE_URL` (and optionally `REDIS_URL`, `SECRET_KEY`).

3. Start PostgreSQL and Redis (or use Docker for just these):

   ```bash
   docker compose up -d db redis
   ```

4. Run migrations:

   ```bash
   alembic upgrade head
   ```

5. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

6. (Optional) Start Celery worker for async GPX processing:

   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

### Docker

One-command startup from the repo root:

```bash
make up
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

Helpful commands:

```bash
make logs      # stream service logs
make down      # stop everything
make api-shell # shell inside API container
```

## Frontend

A React dashboard runs in the `frontend/` folder. It uses Vite and proxies API requests to the backend.

1. Ensure the API is running (e.g. `make up` or `uvicorn app.main:app --reload`).
2. From the project root:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open **http://localhost:5173** in your browser. Sign up or log in, then use Dashboard, Runs, Upload GPX, and Recommendations.

## Render (Docker) deployment

The container now starts via `scripts/start-api.sh`, which:

1. runs `alembic upgrade head` (unless `RUN_MIGRATIONS=0`)
2. starts Uvicorn on `$PORT` (Render sets this automatically)

Set these environment variables in Render:

- `DATABASE_EXTERNAL_URL` = Postgres **External Database URL** (recommended on Render)
- `DATABASE_URL` can stay linked, but `DATABASE_EXTERNAL_URL` takes priority
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `SECRET_KEY`
- optional: `RUN_MIGRATIONS=1` (default)

If deploy logs show `socket.gaierror` or host like `dpg-xxxx-a` (no `.render.com`),
Render is using an incomplete linked DB URL. Either:
- set `DATABASE_EXTERNAL_URL` to the full external URL, or
- unlink the old Postgres resource from the web service and set `DATABASE_URL` only.

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register (email, password, full_name) |
| POST | `/api/auth/login` | Login → JWT (use in `Authorization: Bearer <token>`) |
| GET | `/api/runs` | List current user's runs |
| GET | `/api/runs/dashboard` | Dashboard stats (totals, this week/month) |
| GET | `/api/runs/{id}` | Run detail with points and splits |
| POST | `/api/runs/upload-gpx` | Upload GPX file (form field `file`) |
| DELETE | `/api/runs/{id}` | Delete a run |
| GET | `/api/recommendations` | Personalized training recommendations |

## Environment variables

See `.env.example`. Main ones:

- `DATABASE_URL` – PostgreSQL URL with `+asyncpg` for the API.
- `REDIS_URL` / `CELERY_BROKER_URL` – Redis for cache and Celery.
- `SECRET_KEY` – Used for JWT signing; set a strong value in production.

## License

MIT
