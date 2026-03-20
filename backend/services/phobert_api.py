import httpx

from backend.core.config import settings


_LABEL_MAP = {
    "LABEL_0": "positive",
    "LABEL_1": "neutral",
    "LABEL_2": "negative",
    "POSITIVE": "positive",
    "NEUTRAL": "neutral",
    "NEGATIVE": "negative",
}


def _normalize_label(label: str) -> str:
    return _LABEL_MAP.get(label.upper(), label.lower())


def analyze_with_huggingface(text: str) -> dict:
    if not settings.hf_api_token:
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "model": settings.hf_model_id,
            "raw_response": {"warning": "HF_API_TOKEN missing"},
        }

    url = f"https://api-inference.huggingface.co/models/{settings.hf_model_id}"
    headers = {"Authorization": f"Bearer {settings.hf_api_token}"}

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, headers=headers, json={"inputs": text})
        response.raise_for_status()
        payload = response.json()

    candidates = []
    if isinstance(payload, list) and payload and isinstance(payload[0], list):
        candidates = payload[0]
    elif isinstance(payload, list):
        candidates = payload

    if not candidates:
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "model": settings.hf_model_id,
            "raw_response": {"payload": payload},
        }

    best = max(candidates, key=lambda x: float(x.get("score", 0)))
    sentiment = _normalize_label(str(best.get("label", "neutral")))
    confidence = float(best.get("score", 0))

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "model": settings.hf_model_id,
        "raw_response": {"payload": payload},
    }
