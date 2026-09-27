# Mworks API

FastAPI backend for the Mworks marketplace. Local stack: Postgres, Redis, MinIO, RS256 JWT.

## Run

```bash
cp .env.example .env
chmod +x scripts/*.sh
./scripts/gen_jwt_keys.sh
docker compose up --build
```

API: http://localhost:8000/health  
Docs (local only): http://localhost:8000/docs

Demo login: `henry@mworks.ng` / `ChangeMe1a!`

Point the frontend at it:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Tests

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
APP_ENV=test pytest -q
```

## Settings

All env vars are declared on `Settings` (`extra=ignore`). `DB_SSLMODE` empty means `disable` only for `localhost` / `127.0.0.1` / `::1` / Docker hostname `db`, and `require` for every other host. `statement_timeout` is applied after connect, never as a libpq startup option.

Do not put secrets in git. `secrets/*.pem` is ignored.

## Vercel

The API is a Python function. Job ingest runs once a day via cron at `GET /v1/internal/cron/ingest` (Bearer `CRON_SECRET`).

Live uploads use the same S3 fields as MinIO. Point them at Cloudflare R2:

```
S3_ENDPOINT=https://<accountid>.r2.cloudflarestorage.com
S3_PUBLIC_ENDPOINT=https://<accountid>.r2.cloudflarestorage.com
S3_BUCKET=mworks
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_REGION=auto
```
