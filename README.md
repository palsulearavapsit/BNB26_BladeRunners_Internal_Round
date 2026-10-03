# SATYA

SATYA is a modular multimedia authenticity verification MVP. It accepts images,
video, audio, text, and documents, routes each upload through a modality-specific
pipeline, normalizes model output into the three SATYA classes
(`AUTHENTIC`, `MANIPULATED`, and `SYNTHETIC`), and stores the result for the
authenticated user.

The current inference adapters are explicitly development adapters. They return
deterministic, explainable placeholder scores and mark the response as demo
inference; no placeholder output is presented as a genuine forensic detection.
The adapter boundary is ready for local models or external inference endpoints.

Uploads accept any file extension. SATYA detects `image`, `video`, `audio`,
`voice`, `text`, `document`, or `unknown` using the MIME type first and the
filename extension as a fallback. Unknown files are retained and analyzed by
the generic document pipeline instead of being rejected.

## Repository layout

- [`backend/`](./backend) — FastAPI API, pipelines, adapters, Supabase repository, migrations, and tests.
- [`frontend/`](./frontend) — React/TypeScript/Vite responsive application.
- [`problem-understanding-short.md`](./problem-understanding-short.md) — original problem brief.

## Quick start

### Run everything

From the repository root:

```powershell
python run.py
```

The launcher creates `backend/.env` and `frontend/.env` from their example
files if they do not exist, installs missing dependencies, and starts both
services. Use `python run.py --skip-install` after dependencies are installed.
Open `http://localhost:5173` for the frontend and `http://localhost:8000/docs`
for the backend API. Press `Ctrl+C` to stop both processes.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Set the Supabase URL and anonymous key in both environments when using a
Supabase project. The backend service-role key is server-only and must never be
placed in the frontend environment.

### Environment values explained

- `SATYA_ENVIRONMENT=development` selects development behavior and logging. It
  is not an API key and should be `production` only when deploying.
- `SATYA_PERSISTENCE_MODE=local` uses an in-memory development repository. Data
  disappears when the backend stops. For real persistent user data, use
  `supabase`.
- `SATYA_LOCAL_FALLBACK_ENABLED=true` explicitly permits that local repository.
  It prevents accidentally running a production-like app without a database.
- `SATYA_MAX_UPLOAD_BYTES=26214400` is the server upload limit in bytes
  (25 MiB). Increase it only if you also consider storage and processing costs.
- `SATYA_LLM_PROVIDER` is the provider name, such as `gemini` or `openai`.
- `SATYA_LLM_API_KEY` is the secret API key issued by that provider. Keep it in
  `backend/.env`; never put it in `frontend/.env` or commit it.
- `SATYA_WHISPER_API_KEY` is the server-side key used for optional audio
  transcription. The default endpoint is the OpenAI Whisper transcription API;
  add the key to `backend/.env` and use “Transcribe with Whisper” for audio.

The current MVP does not call an LLM yet: its explanation service is grounded
in the development adapter output and explicitly labels the result as demo
inference. Adding a provider/key alone will not turn placeholder inference
into a real detector.

## Supabase setup

Run the SQL migration in [`backend/supabase/migrations/001_initial.sql`](./backend/supabase/migrations/001_initial.sql)
against the project database. Create the private storage bucket named by
`SUPABASE_STORAGE_BUCKET` (default `satya-uploads`). Authenticated users are
restricted to their own profiles, analyses, metadata, and storage objects by
RLS policies.

For local UI development without Supabase credentials, the frontend shows a
configuration message rather than silently pretending authentication works.
The backend can run its health and pure pipeline tests without external
services; upload and persistence require configured Supabase credentials.

## API

- `GET /api/health`
- `POST /api/upload`
- `GET /api/analysis/{analysis_id}`
- `GET /api/history`

Upload requests use `multipart/form-data` with a `file` field. The frontend
calls the stable API contract and does not know which model adapter handles a
modality.

## Model integration

Add model artifacts under the relevant `backend/Models/<modality>/` directory,
configure the model provider/name/path/endpoint in `.env`, and implement the
`ModelAdapter` contract in `backend/app/adapters/`. Adapters must return
validated raw scores for all three classes. The confidence service normalizes
scores, while the explanation service only receives the normalized result and
evidence; it cannot change the predicted class.

## Limitations

Scanned-PDF OCR, asynchronous workers, calibrated probabilities, and real
pretrained detectors are intentionally extension points. The application
reports demo inference status and never fabricates forensic evidence when those
capabilities are unavailable.
