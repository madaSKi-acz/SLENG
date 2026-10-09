"""
Purpose:  HTTP API contract: status codes, error shape, headers, bodies (fake voices).
Layer:    engine tests
Depends:  fastapi.testclient, sleng.adapters.http
"""

from __future__ import annotations

from fastapi.testclient import TestClient

API = "/api/v1"
RAW = {"voice": "mms", "cleanup": "off"}


def test_health(client: TestClient) -> None:
    body = client.get(f"{API}/health").json()
    assert body["status"] == "ok"
    assert body["fake"] is True


def test_options_lists_pickers(client: TestClient) -> None:
    body = client.get(f"{API}/options").json()
    assert "pop" in body["themes"]
    assert {"width": 1280, "height": 720} in body["sizes"]
    assert {"name": "candy", "group": "pop"} in body["palettes"]


def test_split(client: TestClient) -> None:
    body = client.post(f"{API}/text/split", json={"text": "ក។ ខ១។", "max_chars": 110}).json()
    assert [line["text"] for line in body] == ["ក។", "ខ១។"]
    assert body[1]["pause"] == "paragraph"
    assert "មួយ" in body[1]["spoken"]


def test_speak_line_returns_wav_and_gap(client: TestClient) -> None:
    payload = {"text": "សួស្តី", "speech": RAW, "pause": "paragraph", "pauses": {"paragraph": 0.9}}
    response = client.post(f"{API}/speech/line", json=payload)
    assert response.status_code == 200
    assert response.content[:4] == b"RIFF"
    assert response.headers["X-Gap-After"] == "0.900"


def test_unreadable_line_is_400_with_error_shape(client: TestClient) -> None:
    response = client.post(f"{API}/speech/line", json={"text": "()", "speech": RAW})
    assert response.status_code == 400
    assert response.json()["type"] == "InvalidInputError"


def test_unknown_voice_is_404(client: TestClient) -> None:
    payload = {"text": "ក", "speech": {"voice": "clone:0000000000", "cleanup": "off"}}
    assert client.post(f"{API}/speech/line", json=payload).status_code == 404


def test_validation_error_shape(client: TestClient) -> None:
    response = client.post(f"{API}/speech/line", json={"text": "ក", "speech": {"speed": 9}})
    assert response.status_code == 422
    assert response.json()["type"] == "ValidationError"


def test_zip_export_download(client: TestClient) -> None:
    payload = {"script": {"text": "ក។ ខ។"}, "speech": RAW}
    response = client.post(f"{API}/exports/zip", json=payload)
    assert response.status_code == 200
    assert "attachment" in response.headers["Content-Disposition"]


def test_bad_video_size_is_rejected(client: TestClient) -> None:
    payload = {"script": {"text": "ក"}, "video": {"width": 10, "height": 10}}
    assert client.post(f"{API}/jobs/video", json=payload).status_code == 422


def test_unknown_job_is_404(client: TestClient) -> None:
    assert client.get(f"{API}/jobs/nope").status_code == 404
