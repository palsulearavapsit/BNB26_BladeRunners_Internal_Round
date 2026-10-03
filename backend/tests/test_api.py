from fastapi.testclient import TestClient
from app.main import app
from app.services.extraction import extract_text

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_and_analysis():
    response = client.post("/api/upload", files={"file": ("sample.txt", b"hello", "text/plain")})
    assert response.status_code == 200
    analysis_id = response.json()["analysis_id"]
    result = client.get(f"/api/analysis/{analysis_id}")
    assert result.status_code == 200
    assert result.json()["is_development_inference"] is True
    assert result.json()["label"] == "insufficient_evidence"
    history = client.get("/api/history")
    assert history.status_code == 200
    assert any(item["analysis_id"] == analysis_id for item in history.json())


def test_rejects_unknown_extension():
    response = client.post("/api/upload", files={"file": ("sample.exe", b"no", "application/octet-stream")})
    assert response.status_code == 415


def test_plain_text_extraction():
    text, notes = extract_text("notes.txt", b"SATYA")
    assert text == "SATYA"
    assert notes == []
