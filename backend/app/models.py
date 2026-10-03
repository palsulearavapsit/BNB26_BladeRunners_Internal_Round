from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


Modality = Literal["image", "video", "audio", "voice", "text", "document", "unknown"]


class UploadResponse(BaseModel):
    analysis_id: UUID
    filename: str
    modality: Modality
    status: str


class Evidence(BaseModel):
    signal: str
    description: str
    severity: Literal["low", "medium", "high"]
    source: str


class AnalysisResult(BaseModel):
    analysis_id: UUID
    filename: str
    modality: Modality
    label: Literal["authentic", "manipulated", "synthetic", "insufficient_evidence"]
    confidence: float = Field(ge=0, le=1)
    is_development_inference: bool = True
    summary: str
    evidence: list[Evidence]
    limitations: list[str]
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class HistoryItem(BaseModel):
    analysis_id: UUID
    filename: str
    modality: Modality
    label: str
    confidence: float
    created_at: datetime
