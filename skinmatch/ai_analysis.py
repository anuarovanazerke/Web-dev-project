import base64
import json
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .services import INGREDIENT_RECOMMENDATIONS, normalize_concern


ALLOWED_SKIN_TYPES = {"dry", "oily", "combo", "normal"}
ALLOWED_FACE_SHAPES = {"oval", "round", "square", "heart", "oblong"}
ALLOWED_CONCERNS = {
    "acne",
    "rosacea",
    "wrinkles",
    "pigmentation",
    "dehydration",
    "sensitivity",
    "dullness",
    "pores",
    "dark_circles",
}


class FaceAnalysisProviderError(RuntimeError):
    pass


def analyze_face_with_ai(uploaded_file, concern_hint=""):
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    if not api_key:
        raise FaceAnalysisProviderError("OPENAI_API_KEY is not configured.")

    uploaded_file.seek(0)
    image_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    if not image_bytes:
        raise FaceAnalysisProviderError("Uploaded image is empty.")

    mime_type = getattr(uploaded_file, "content_type", "") or "image/png"
    data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    concern_hint = normalize_concern(concern_hint)

    prompt = (
        "Analyze this face photo for a skincare recommendation workflow. "
        "Do not diagnose medical conditions. Use only visible cosmetic cues. "
        "Return JSON with keys skin_type, face_shape, concern, confidence, notes, ingredient_hints. "
        "skin_type must be one of: dry, oily, combo, normal. "
        "face_shape must be one of: oval, round, square, heart, oblong. "
        "concern must be one of: acne, rosacea, wrinkles, pigmentation, dehydration, sensitivity, "
        "dullness, pores, dark_circles. "
        "confidence must be a number between 0 and 1. "
        "notes must be one concise sentence. "
        "ingredient_hints must be an array of 2 to 4 short active ingredients or skincare ingredients. "
        f"Prefer the user supplied concern hint if it is plausible: {concern_hint or 'none'}."
    )

    payload = {
        "model": settings.OPENAI_MODEL,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url, "detail": "high"},
                ],
            }
        ],
    }

    request = Request(
        settings.OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise FaceAnalysisProviderError(f"AI provider rejected the request: {details}") from exc
    except URLError as exc:
        raise FaceAnalysisProviderError(f"AI provider is unreachable: {exc.reason}") from exc
    except TimeoutError as exc:
        raise FaceAnalysisProviderError("AI provider timed out.") from exc

    content = _extract_response_text(response_payload)
    if not content:
        raise FaceAnalysisProviderError("AI provider returned an empty response.")

    try:
        parsed = json.loads(content)
    except JSONDecodeError as exc:
        raise FaceAnalysisProviderError("AI provider did not return valid JSON.") from exc

    skin_type = parsed.get("skin_type", "").strip().lower()
    face_shape = parsed.get("face_shape", "").strip().lower()
    concern = normalize_concern(parsed.get("concern", "").strip().lower())
    confidence = parsed.get("confidence", 0.0)
    notes = str(parsed.get("notes", "")).strip()
    ingredient_hints = [str(item).strip() for item in parsed.get("ingredient_hints", []) if str(item).strip()]

    if skin_type not in ALLOWED_SKIN_TYPES:
        raise FaceAnalysisProviderError(f"Unsupported skin_type from AI provider: {skin_type}")
    if face_shape not in ALLOWED_FACE_SHAPES:
        raise FaceAnalysisProviderError(f"Unsupported face_shape from AI provider: {face_shape}")
    if concern not in ALLOWED_CONCERNS:
        concern = concern_hint or "dullness"

    if not ingredient_hints:
        ingredient_hints = INGREDIENT_RECOMMENDATIONS.get(concern, [])

    safe_confidence = 0.0
    try:
        safe_confidence = max(0.0, min(float(confidence), 1.0))
    except (TypeError, ValueError):
        safe_confidence = 0.0

    return {
        "provider": "openai",
        "skin_type": skin_type,
        "face_shape": face_shape,
        "concern": concern,
        "notes": (
            f"AI vision analysis used with model {settings.OPENAI_MODEL}. "
            f"Confidence={safe_confidence:.2f}. {notes or 'Cosmetic, non-medical assessment.'}"
        ),
        "metrics": {
            "confidence": round(safe_confidence, 2),
        },
        "ingredient_hints": ingredient_hints[:4],
    }


def _extract_response_text(payload):
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            text_value = content.get("text")
            if isinstance(text_value, str) and text_value.strip():
                return text_value.strip()
    return ""
