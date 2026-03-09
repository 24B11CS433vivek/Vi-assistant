# Vi — Personal AI Assistant

A fast, free-tier personal AI assistant powered by Hugging Face Inference API.
Runs entirely on cloud infrastructure — no local machine required.

---

## Quick Start (Local)

### 1. Get a Hugging Face API key

1. Create a free account at https://huggingface.co
2. Go to **Settings → Access Tokens**
3. Click **New token** → choose *Read* access → copy the token

### 2. Set up the project

```bash
git clone <your-repo-url>
cd vi-assistant

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and paste your HUGGINGFACE_API_KEY
```

### 3. Run locally

```bash
# Load env vars and start server
export $(cat .env | grep -v '#' | xargs)
python app.py
```

Open **http://localhost:5000** in your browser.

---

## Deployment — Render (Recommended Free Option)

Render gives you a free web service that stays online 24/7 (with spin-down
after 15 min inactivity on the free tier — first request after idle takes ~30s).

### Steps

1. Push your project to a GitHub repository.

2. Go to https://render.com → **New → Web Service**

3. Connect your GitHub repo.

4. Render auto-detects `render.yaml` — just confirm the settings.

5. Under **Environment Variables**, add:
   - `HUGGINGFACE_API_KEY` = your HF token
   - `MODEL_NAME` = `mistralai/Mistral-7B-Instruct-v0.3`

6. Click **Deploy**. Your URL will be `https://vi-assistant.onrender.com` (or similar).

---

## Deployment — Railway

1. Push to GitHub.
2. Go to https://railway.app → **New Project → Deploy from GitHub repo**
3. Add environment variables in the Railway dashboard.
4. Railway uses the `Procfile` automatically.

---

## Deployment — Replit

1. Create a new Replit from the **Import from GitHub** option.
2. Add your secrets in **Secrets** (the lock icon):
   - `HUGGINGFACE_API_KEY`
   - `MODEL_NAME`
3. Click **Run**.

---

## Switching Models

Just change the `MODEL_NAME` environment variable — no code changes needed.

| Model | Speed | Quality | Notes |
|---|---|---|---|
| `mistralai/Mistral-7B-Instruct-v0.3` | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Best overall (default) |
| `HuggingFaceH4/zephyr-7b-beta` | ⭐⭐⭐ | ⭐⭐⭐⭐ | Great for chat |
| `microsoft/Phi-3-mini-4k-instruct` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Fastest 3.8B model |
| `google/gemma-2-2b-it` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Ultra-fast 2B |

---

## API Reference

### `POST /chat`

**Request body:**
```json
{
  "messages": [
    { "role": "user", "content": "Hello, Vi!" }
  ]
}
```

**Response:**
```json
{
  "response": "Hello! How can I help you today?",
  "status": 200
}
```

### `GET /health`

Returns `{ "status": "ok", "model": "<model_name>" }`

---

## Architecture

```
Browser (mobile/desktop)
       │
       │  HTTPS
       ▼
  Flask Backend (Render/Railway/Replit)
       │
       │  HTTPS + HF Bearer Token
       ▼
  Hugging Face Inference API
       │
       ▼
  Open LLM (Mistral-7B / Zephyr / Phi-3)
```

The API key **never** leaves the backend server — the browser only talks to
your `/chat` endpoint.

---

## Performance Tips

- **Lower `MAX_NEW_TOKENS`** (e.g., 256) for faster responses on free tier.
- **Use a smaller model** like Phi-3-mini for near-instant replies.
- Repeated identical prompts are served from the **in-memory cache** (5 min TTL).
- The backend uses `wait_for_model: true` so cold-start models load automatically.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `HUGGINGFACE_API_KEY` | ✅ | — | Your HF access token |
| `MODEL_NAME` | ❌ | `mistralai/Mistral-7B-Instruct-v0.3` | HF model ID |
| `MAX_NEW_TOKENS` | ❌ | `512` | Max tokens to generate |
| `PORT` | ❌ | `5000` | Server port (set by host) |
| `SYSTEM_PROMPT` | ❌ | Built-in Vi prompt | Custom system prompt |
