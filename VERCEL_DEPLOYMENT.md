# QAgent — Vercel Frontend Deployment Guide

Vercel hosts **only the React client**. The FastAPI service runs on Render and
the database on Neon; see `PRODUCTION_DEPLOYMENT.md` and `render.yaml` for those.

> **Why this changed.** This project previously shipped a `vercel.json` that
> built `api/index.py` with `@vercel/python` and routed `/(.*)` to it, so the
> Vercel project answered every request — including `/` — with FastAPI JSON, or
> with `500 FUNCTION_INVOCATION_FAILED` when the import failed. That is the
> behaviour still visible on the abandoned `qagent-131s.vercel.app` deployment.
> The Python entrypoints have been removed and `vercel.json` now builds the Vite
> bundle, so the browser receives the React app.

---

## 1. Deployment topology

```
        Browser
           |
           v
  Vercel  (static Vite bundle, SPA fallback)
    https://qagent-frontend-jxvh.vercel.app
           |
           |  HTTPS  ->  https://qagent-production.onrender.com/api/...
           v
  Render  (FastAPI + uvicorn)
           |
     +-----+------------------+
     v                        v
  Neon PostgreSQL       OpenRouter
  (asyncpg)             (NVIDIA Nemotron 3.5 Lightning)
```

Vercel serves static assets only. It runs no serverless functions, holds no
database credentials and holds no AI keys.

---

## 2. Project settings

The repository ships a root `vercel.json`, which overrides the dashboard's build
settings. It works with **Root Directory = repository root**:

| Setting | Value | Source |
|---|---|---|
| Framework Preset | Vite | `vercel.json` |
| Install Command | `npm --prefix frontend ci` | `vercel.json` |
| Build Command | `npm --prefix frontend run build` | `vercel.json` |
| Output Directory | `frontend/dist` | `vercel.json` |
| Node.js Version | 22.x (or the project default) | dashboard |

If the Vercel project instead has **Root Directory = `frontend`**, Vercel reads
`frontend/vercel.json`, which carries the same SPA rewrite and cache headers.
Either configuration produces a working deployment.

`npm ci` is deliberate: it installs exactly what `frontend/package-lock.json`
pins, so a production build cannot silently pick up a different dependency tree
than the one that was tested.

---

## 3. Environment variables (Vercel project settings)

Only one variable is required, and it must carry the `VITE_` prefix for Vite to
expose it to client code:

```ini
VITE_API_BASE_URL=https://qagent-production.onrender.com
```

`frontend/src/api/client.ts` appends `/api` itself, producing
`https://qagent-production.onrender.com/api/...`. Do **not** include the `/api`
suffix in the variable, and do not add a trailing slash.

`frontend/.env.production` carries the same value, so a build still targets the
Render backend even if the dashboard variable is missing.

> **Never put a backend secret in a `VITE_` variable.** Everything prefixed with
> `VITE_` is inlined into the JavaScript bundle and is readable by anyone who
> opens the site. `DATABASE_URL`, `SECRET_KEY`, `OPENROUTER_API_KEY` and the
> `S3_*` credentials belong on Render only.

---

## 4. SPA routing

The client routes in React state rather than through the URL, so the application
lives at `/`. The rewrite in `vercel.json` sends any non-asset path to
`index.html`, which means a refresh or a typed-in deep link renders the app
instead of Vercel's 404 page:

```json
{ "source": "/((?!assets/).*)", "destination": "/index.html" }
```

Hashed files under `/assets/` are excluded so they keep their immutable
`Cache-Control` header and are never shadowed by the HTML fallback.

---

## 5. Deploying

### Git integration (recommended)

Pushing to the production branch triggers a build. Preview branches build to
`qagent-*.vercel.app` hostnames, which the backend's `CORS_ORIGIN_REGEX`
already admits.

### Vercel CLI

```bash
npm i -g vercel
vercel link
vercel --prod
```

### Local reproduction of the production build

```bash
npm --prefix frontend ci
npm --prefix frontend run build
npx --prefix frontend vite preview --outDir dist
```

---

## 6. Post-deployment verification

```bash
# 1. The root must return the React shell, not FastAPI JSON.
curl -s https://qagent-frontend-jxvh.vercel.app/ | head -20
#    Expect <!doctype html> ... <div id="root"></div>
#    A JSON body such as {"status":"healthy",...} means a Python function is
#    still attached to the project.

# 2. A deep link must also return the shell (SPA fallback).
curl -s -o /dev/null -w '%{http_code}\n' https://qagent-frontend-jxvh.vercel.app/dashboard

# 3. The bundle must target Render and nothing else.
curl -s https://qagent-frontend-jxvh.vercel.app/ \
  | grep -o '/assets/[^"]*\.js' | head -1
# then fetch that asset and confirm it contains qagent-production.onrender.com
# and no localhost / qagent-131s reference.

# 4. The backend must answer the browser's preflight for this origin.
curl -si -X OPTIONS https://qagent-production.onrender.com/api/auth/login \
  -H 'Origin: https://qagent-frontend-jxvh.vercel.app' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: authorization,content-type' \
  | grep -i access-control-allow-origin
```

---

## 7. Retiring `qagent-131s.vercel.app`

That project was the FastAPI-on-Vercel experiment. It is no longer referenced by
the frontend, and it has been removed from the backend's CORS allow-list, so it
cannot exchange credentialed requests with the API. Deleting the Vercel project
itself is a dashboard action and is left to the project owner.
