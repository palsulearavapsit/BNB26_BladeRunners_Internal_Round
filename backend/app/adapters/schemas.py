from pydantic import BaseModel, Field


class NormalizedPrediction(BaseModel):
    label: str
    score: float = Field(ge=0, le=1)
    signals: list[str] = Field(default_factory=list)
    model_name: str
    is_development_inference: bool = True
    metadata: dict[str, object] = Field(default_factory=dict)
