# 🛡️ AI Safety & Governance Dashboard

A **real-time AI governance platform** that acts as a security gateway between your applications and LLMs. Every LLM call passes through this system, where it is scanned for prompt injections, checked for toxicity, and the response is validated for hallucinations — all logged to an immutable audit trail and visualized on a premium React dashboard.

## 🚀 Features

- **OpenAI-Compatible Proxy:** Drop-in replacement for any app using the OpenAI SDK.
- **Real-Time Guardrails:** Scans inputs and outputs in parallel with minimal latency overhead.
- **5 Built-in Scanners:**
  - **Prompt Injection:** Heuristic + ML-based detection
  - **Hallucination:** Claim-level semantic verification
  - **Toxicity:** Multi-category scoring
  - **PII:** Enterprise-grade entity detection & masking
  - **Bias:** Stereotypical pattern matching
- **Policy Engine:** Configure custom rules (e.g., "Block if injection score > 0.85").
- **Live Monitor:** WebSocket-powered real-time dashboard of all LLM traffic.
- **Analytics & Audit:** Full historical search, cost tracking, and model A/B testing.

## 🏗️ Architecture

- **Backend:** FastAPI, Python 3.11, PostgreSQL 16, Redis 7
- **Frontend:** React 18, TypeScript, Vite, Recharts, Framer Motion
- **Deployment:** Docker Compose

## ⚡ Quick Start

1. **Clone & Configure:**
   ```bash
   cp .env.example .env
   # Add your OpenAI / Anthropic keys to .env (optional, works with mock data without keys)
   ```

2. **Run with Docker:**
   ```bash
   docker compose up --build
   ```

3. **Access Dashboard:**
   - Open `http://localhost:3000`
   - Login with demo credentials: `admin@admin.com` / `admin123`

## 🔌 Connecting Your App

Change just the `base_url` and `api_key` in your application code to route traffic through the safety gateway.

```python
from openai import OpenAI

# Connect to the AI Safety Gateway instead of directly to OpenAI
client = OpenAI(
    api_key="your-generated-proxy-key",
    base_url="http://localhost:8000/v1"
)

# Use normally!
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What is the capital of France?"}]
)
```
