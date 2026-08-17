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

### On this Windows machine: use the helper script

The npm registry is very slow from this network and npm's postinstall scripts
crash on Windows here, so a plain `npm install` may fail or take forever. Use:

```bash
bash scripts/npm-install-win.sh apps/web
```

This installs **offline from the local npm cache**, skips postinstall scripts
(nothing in the tree needs them), kills stale processes holding file locks, and
retries until the install completes. See the script header for details.

## API proxy

Requests to `/api/*` in the browser are proxied by Next.js rewrites to the
FastAPI backend (default `http://localhost:8000`). Override with:

```bash
API_URL=http://localhost:8000 npm run dev
```

The home page shows an API health indicator driven by `GET /api/v1/health`.

## Map layers (Phase 2)

The map fetches the study-area layers through the proxy and renders them:

| Layer | Endpoint | Style |
|-------|----------|-------|
| Lagos State boundary | `/api/v1/boundaries/city` | amber fill + outline |
| LGA boundaries (20) | `/api/v1/boundaries/lgas` | indigo outlines |
| Neighborhoods (81) | `/api/v1/boundaries/neighborhoods` | teal points (+ polygon outlines) |

Counts are shown in the study-area legend once the layers load; the map fits
to the state boundary automatically.
