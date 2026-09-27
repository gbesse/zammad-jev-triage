"""Small pinned Jev choice client. Decision thresholds are examples, not calibrated."""
import hashlib
import json
import math
from urllib.request import Request, urlopen

API_URL = "https://api.typesafe.ai/v1/systemone"

class DecisionError(Exception):
    pass

def decide(text, policy, api_key, *, opener=urlopen, timeout=20):
    if not isinstance(text, str) or not text.strip() or len(text) > 16000:
        raise DecisionError("text must be 1..16000 characters")
    if not isinstance(api_key, str) or not api_key:
        raise DecisionError("TYPESAFE_API_KEY is required")
    model = policy["model"]
    question = policy["question"]
    criteria = policy["criteria"]
    threshold = policy["threshold"]
    if not (isinstance(threshold, (int, float)) and not isinstance(threshold, bool) and 0 < threshold <= 1):
        raise DecisionError("invalid threshold")
    body = {"model": model, "questions": {question: {"type": "choice", "instructions": policy["instructions"], "criteria": criteria}}, "state": {"text": text}}
    request = Request(API_URL, data=json.dumps(body).encode(), headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}, method="POST")
    try:
        with opener(request, timeout=timeout) as response:
            result = json.load(response)
    except Exception as exc:
        raise DecisionError("Jev request failed") from exc
    if result.get("model") != model:
        raise DecisionError("Jev model mismatch")
    answer = result.get("answers", {}).get(question, {})
    choice = answer.get("choice")
    probabilities = answer.get("probabilities", {})
    probability = probabilities.get(choice) if isinstance(probabilities, dict) else None
    if choice not in criteria or not isinstance(probability, (int, float)) or isinstance(probability, bool) or not math.isfinite(probability) or not 0 <= probability <= 1:
        raise DecisionError("invalid Jev choice response")
    outcome = choice if choice != "other" and probability >= threshold else "review"
    return {"schemaVersion": 1, "outcome": outcome, "choice": choice, "probability": probability, "threshold": threshold, "model": model, "policyVersion": policy["version"], "inputSha256": hashlib.sha256(text.encode()).hexdigest()}
