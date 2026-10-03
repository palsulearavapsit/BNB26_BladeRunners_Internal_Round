# SATYA frontend

SATYA is a React + TypeScript + Vite interface for multimodal authenticity analysis. It is intentionally independent of model code: the browser sends content to the backend API and renders the returned assessment.

## Run locally

```bash
npm install
copy .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` to the backend origin. Supabase is optional for local UI work; when either Supabase value is missing, the app uses a clearly labelled demo session and demo inference data. Run `npm run typecheck` for TypeScript validation or `npm run build` for the production bundle.

## Backend contract

- `POST /api/upload` — multipart form upload with `file` and optional `context`; returns an analysis object or `{ analysis_id }`.
- `GET /api/history` — returns `{ items: Analysis[] }` or an array.
- `GET /api/analysis/:id` — returns an `Analysis`.

Requests include `Authorization: Bearer <supabase access token>` when a signed-in session exists. The frontend does not assume, import, or bundle any model implementation.
