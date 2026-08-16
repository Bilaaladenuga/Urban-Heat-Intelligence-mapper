# Web — Next.js frontend

MapLibre-based Web GIS for the Urban Heat Intelligence project (Lagos, Nigeria).

## Stack

- Next.js 16 (App Router) · TypeScript · Tailwind CSS 4 · MapLibre GL JS

## Setup

```bash
npm install
npm run dev       # http://localhost:3000
npm run build     # production build
npm run lint
```

## API proxy

Requests to `/api/*` in the browser are proxied by Next.js rewrites to the
FastAPI backend (default `http://localhost:8000`). Override with:

```bash
API_URL=http://localhost:8000 npm run dev
```

The home page shows an API health indicator driven by `GET /api/v1/health`.
