import os
import json
import hashlib
import time
import traceback
from typing import Optional, Tuple, Dict, List
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
HF_API_KEY     = os.environ.get("HUGGINGFACE_API_KEY", "")
MODEL_NAME     = os.environ.get("MODEL_NAME", "Qwen/Qwen3-32B")
API_URL        = "https://router.huggingface.co/v1/chat/completions"
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "512"))
SYSTEM_PROMPT  = (
    "You are Vi, a concise and helpful personal AI assistant. "
    "Give clear, direct answers. Be friendly but not verbose."
)

print(f"[startup] model  = {MODEL_NAME}")
print(f"[startup] key    = {'SET ✅' if HF_API_KEY else 'MISSING ❌'}")
print(f"[startup] url    = {API_URL}")

# ── Cache ────────────────────────────────────────────────────────────────────
_cache: Dict[str, Tuple[str, float]] = {}
CACHE_TTL = 300

def _cache_key(messages: List) -> str:
    return hashlib.md5(json.dumps(messages, sort_keys=True).encode()).hexdigest()

def _cache_get(key: str) -> Optional[str]:
    entry = _cache.get(key)
    if entry and (time.time() - entry[1]) < CACHE_TTL:
        return entry[0]
    return None

def _cache_set(key: str, value: str):
    _cache[key] = (value, time.time())
    if len(_cache) > 200:
        oldest = sorted(_cache.items(), key=lambda x: x[1][1])[:50]
        for k, _ in oldest:
            del _cache[k]

# ── HF OpenAI-compatible call ─────────────────────────────────────────────────
def query_hf(messages: List[Dict]) -> Tuple[str, int]:
    cache_key = _cache_key(messages)
    cached = _cache_get(cache_key)
    if cached:
        print("[hf] cache hit")
        return cached, 200

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": full_messages,
        "max_tokens": MAX_NEW_TOKENS,
        "temperature": 0.7,
        "top_p": 0.9,
    }

    print(f"[hf] sending {len(messages)} message(s) to {MODEL_NAME}")
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=90)
    except requests.exceptions.Timeout:
        return "Request timed out. Please try again.", 504
    except requests.exceptions.ConnectionError as e:
        return f"Connection error: {e}", 503

    print(f"[hf] status={resp.status_code} body={resp.text[:200]}")

    if resp.status_code == 429:
        return "Rate limited — please wait a moment and retry.", 429
    if resp.status_code == 503:
        return "Model is loading, please retry in ~20 seconds.", 503
    if resp.status_code != 200:
        return f"API error {resp.status_code}: {resp.text[:200]}", 500

    try:
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Parse error: {e} | raw: {resp.text[:200]}", 500

    _cache_set(cache_key, text)
    return text, 200

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html", model_name=MODEL_NAME)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data     = request.get_json(silent=True) or {}
        messages = data.get("messages", [])

        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        if not HF_API_KEY:
            return jsonify({"error": "HUGGINGFACE_API_KEY is not set on the server."}), 500

        print(f"[chat] user: {messages[-1].get('content','')[:80]}")
        text, status = query_hf(messages)
        print(f"[chat] vi: {text[:80]}")
        return jsonify({"response": text, "status": status}), (200 if status == 200 else status)

    except Exception:
        print("[chat] EXCEPTION:\n", traceback.format_exc())
        return jsonify({"error": "Internal server error - check terminal"}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME, "key_set": bool(HF_API_KEY)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
