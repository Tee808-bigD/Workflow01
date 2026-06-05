# ResearchSwarm — Microsoft Build AI Hackathon

**Theme 05: Agent Swarms** | 3-agent research pipeline built on AutoGen with Azure OpenAI or OpenAI-compatible providers

## Architecture

```
User Question
     │
     ▼
 [Planner Agent]          → Breaks question into 3 sub-tasks
     │
     ▼
 [Researcher Agent × 3]   → Bing search + LLM extraction per sub-task
     │
     ▼
 [Synthesizer Agent]      → Merges findings into a structured answer
     │
     ▼
 React Dashboard          → Live orchestration graph via WebSocket
```

## Stack

| Layer | Tech |
|-------|------|
| Agent framework | AutoGen AgentChat 0.4 |
| LLM | Azure OpenAI, OpenAI, GitHub Models, Hugging Face, OpenRouter, Groq, Together, Fireworks, local/custom OpenAI-compatible APIs |
| Web search | Bing Search API v7 |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + Vite |
| Deployment | Azure App Service + Azure Static Web Apps |

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/research-swarm
cd research-swarm
cp .env.example .env
# Fill in your LLM provider and search provider keys in .env
```

### 2. Backend

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
# Runs on http://localhost:8000
```

### 3. Frontend

```bash
npm install
npm run dev
# Runs on http://localhost:5173
```

### 4. Required environment variables

Create a `.env` file from `.env.example` and set:

- `LLM_PROVIDER`

For Azure OpenAI, set `LLM_PROVIDER=azure` and configure:

- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_MODEL`
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`

Supported `LLM_PROVIDER` values:

- `azure`
- `openai`
- `github`
- `huggingface`
- `openrouter`
- `groq`
- `together`
- `fireworks`
- `local`
- `custom`

For GitHub Models, set `LLM_PROVIDER=github` and configure:

- `GITHUB_TOKEN`
- `GITHUB_MODELS_MODEL`
- `GITHUB_MODELS_BASE_URL`

For Hugging Face Inference Providers, set `LLM_PROVIDER=huggingface` and configure:

- `HUGGINGFACE_API_KEY` or `HF_TOKEN`
- `HUGGINGFACE_MODEL`
- `HUGGINGFACE_BASE_URL`

For any OpenAI-compatible provider, set the matching provider-specific variables, or use:

- `OPENAI_COMPATIBLE_API_KEY`
- `OPENAI_COMPATIBLE_MODEL`
- `OPENAI_COMPATIBLE_BASE_URL`

Optional model capability flags:

- `LLM_SUPPORTS_JSON_OUTPUT`
- `LLM_SUPPORTS_FUNCTION_CALLING`
- `LLM_SUPPORTS_VISION`
- `LLM_MODEL_FAMILY`

For web search, set `SEARCH_PROVIDER=auto` and configure any one of:

- `BING_SEARCH_API_KEY`
- `TAVILY_API_KEY`
- `SERPER_API_KEY`
- `BRAVE_SEARCH_API_KEY`

To run without web search, set:

- `SEARCH_PROVIDER=none`

General app settings:

- `CORS_ORIGIN`

Check config before running the UI:

```bash
curl http://localhost:8000/config
```

Without the selected LLM provider values, the UI may connect but the agents will not return a real answer.

### 5. Azure keys you need

- **Azure OpenAI** — create a resource, deploy `gpt-4o`, grab endpoint + key
- **GitHub Models** — create a GitHub token with Models access, then set `LLM_PROVIDER=github`
- **Hugging Face** — create a Hugging Face token, then set `LLM_PROVIDER=huggingface`
- **OpenAI-compatible providers** — set the provider key, model, and base URL from `.env.example`
- **Search API** — use Bing, Tavily, Serper, Brave Search, or `SEARCH_PROVIDER=none`

## Azure Deployment

```bash
# Backend → Azure App Service (B1 tier is fine for demo)
az webapp up --name research-swarm-api --runtime PYTHON:3.11

# Frontend → Azure Static Web Apps
npm run build
# Deploy /dist via Azure Static Web Apps GitHub action
```

Set all `.env` values as App Settings in your App Service.

## Team

| Name | Role |
|------|------|
| [Your Name] | Full-stack + AI |
