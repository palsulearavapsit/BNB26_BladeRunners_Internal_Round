# SATYA backend

SATYA is a modular FastAPI MVP for multimodal authenticity analysis. It accepts
images, video, audio, text, and PDF/DOCX/XLSX/PPTX documents through
`POST /api/upload`, then exposes `GET /api/analysis/{id}` and `GET /api/history`.

The inference adapter is a deterministic development placeholder, **not genuine
ML**. It returns `insufficient_evidence` and every response identifies the
development inference boundary and its limitations.

## Run locally

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

In-memory persistence is opt-in only with
`SATYA_PERSISTENCE_MODE=local` and `SATYA_LOCAL_FALLBACK_ENABLED=true`. The
default Supabase mode requires both credentials and fails explicitly if missing.
The migration enables RLS and scopes rows to authenticated users.
