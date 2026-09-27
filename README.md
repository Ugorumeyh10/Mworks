# Mworks

Nigeria-first RPA/AI marketplace.

- `mworks-backend` — FastAPI API (Postgres, Redis, MinIO locally)
- `mworks-frontend` — React + Vite app

## Local backend

```bash
cd mworks-backend
cp .env.example .env
chmod +x scripts/*.sh
./scripts/gen_jwt_keys.sh
docker compose up --build
```

API: http://localhost:8000/health

## Local frontend

```bash
cd mworks-frontend
cp .env.example .env.development
npm install
npm run dev
```

App: http://localhost:5173
