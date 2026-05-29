# IntegrationOps Dashboard

A minimal **Next.js (App Router) + TypeScript** dashboard for the IntegrationOps
backend. It is a thin client over the existing REST API — no business logic is
duplicated here.

## Pages

| Route | Purpose |
|---|---|
| `/login` | Obtain a JWT via the API and store it locally |
| `/` | Overview metrics (uploads, jobs, exports) |
| `/uploads` | List of upload batches |
| `/uploads/[id]` | Validation errors for a batch |
| `/jobs` | Async job status and results |
| `/exports` | Export jobs with authenticated downloads |
| `/audit` | Operational audit log (admin only) |

## Stack

- Next.js 14 (App Router) + React 18 + TypeScript
- Plain CSS (no UI framework) for a small, dependency-light footprint
- Native `fetch` with a tiny client in [`lib/api.ts`](lib/api.ts); JWT kept in `localStorage`

## Getting started

```bash
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL (default :8000)
npm install
npm run dev                        # http://localhost:3000
```

Make sure the IntegrationOps API is running and that its `CORS_ORIGINS`
includes the dashboard origin (default `http://localhost:3000`).

## Build

```bash
npm run build
npm start
```
