from threading import Lock
from uuid import UUID

from app.config.settings import Settings
from app.models import AnalysisResult, HistoryItem


class AnalysisRepository:
    def __init__(self, settings: Settings):
        if settings.persistence_mode == "local" and not settings.local_fallback_enabled:
            raise RuntimeError("Local persistence requires SATYA_LOCAL_FALLBACK_ENABLED=true")
        if settings.persistence_mode == "supabase" and not settings.supabase_configured:
            raise RuntimeError("Supabase is not configured; set SATYA_SUPABASE_URL and SATYA_SUPABASE_KEY")
        self._items: dict[UUID, AnalysisResult] = {}
        self._lock = Lock()

    def save(self, result: AnalysisResult) -> None:
        with self._lock:
            self._items[result.analysis_id] = result

    def get(self, analysis_id: UUID) -> AnalysisResult | None:
        return self._items.get(analysis_id)

    def history(self) -> list[HistoryItem]:
        return [HistoryItem(analysis_id=item.analysis_id, filename=item.filename, modality=item.modality,
                            label=item.label, confidence=item.confidence, created_at=item.created_at)
                for item in sorted(self._items.values(), key=lambda value: value.created_at, reverse=True)]


class SupabaseRepository:
    def __init__(self, settings: Settings):
        if not settings.supabase_configured:
            raise RuntimeError("Supabase requires SATYA_SUPABASE_URL and SATYA_SUPABASE_KEY")
        try:
            from supabase import create_client
        except ImportError as exc:
            raise RuntimeError("Install the supabase package to use Supabase persistence") from exc
        self.client = create_client(settings.supabase_url, settings.supabase_key)

    def set_access_token(self, access_token: str | None) -> None:
        if access_token:
            self.client.postgrest.auth(access_token)

    def save(self, result: AnalysisResult) -> None:
        response = self.client.table("analyses").insert({
            "id": str(result.analysis_id), "filename": result.filename,
            "modality": result.modality, "label": result.label,
            "confidence": result.confidence, "result": result.model_dump(mode="json"),
        }).execute()
        if getattr(response, "error", None):
            raise RuntimeError(f"Supabase insert failed: {response.error}")

    def get(self, analysis_id: UUID) -> AnalysisResult | None:
        response = self.client.table("analyses").select("result").eq("id", str(analysis_id)).limit(1).execute()
        if not response.data:
            return None
        return AnalysisResult.model_validate(response.data[0]["result"])

    def history(self) -> list[HistoryItem]:
        response = self.client.table("analyses").select("result").order("created_at", desc=True).execute()
        return [HistoryItem(
            analysis_id=item["result"]["analysis_id"], filename=item["result"]["filename"],
            modality=item["result"]["modality"], label=item["result"]["label"],
            confidence=item["result"]["confidence"], created_at=item["result"]["created_at"],
        ) for item in response.data]


_repositories: dict[str, AnalysisRepository | SupabaseRepository] = {}
_repository_lock = Lock()


def get_repository(settings: Settings, access_token: str | None = None) -> AnalysisRepository | SupabaseRepository:
    key = f"{settings.persistence_mode}:{settings.supabase_url or 'local'}"
    with _repository_lock:
        if key not in _repositories:
            if settings.persistence_mode == "local":
                _repositories[key] = AnalysisRepository(settings)
            elif settings.persistence_mode == "supabase":
                _repositories[key] = SupabaseRepository(settings)
            else:
                raise RuntimeError("SATYA_PERSISTENCE_MODE must be 'supabase' or 'local'")
        repository = _repositories[key]
        if isinstance(repository, SupabaseRepository):
            repository.set_access_token(access_token)
        return repository
