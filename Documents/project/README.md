# 🚀 ResearchSwarm — AI Agent Orchestration

ResearchSwarm is a high-performance, 3-agent research pipeline designed for the Microsoft Build AI Hackathon. It leverages a swarm architecture to break down complex questions, conduct parallel research, and synthesize a comprehensive final answer.

## 🏗️ Architecture

The system uses a linear orchestration pipeline:
**User Question** $\rightarrow$ **Planner Agent** $\rightarrow$ **Researcher Agent (x3)** $\rightarrow$ **Synthesizer Agent** $\rightarrow$ **React Dashboard**

- **Planner**: Decomposes the original question into 3 distinct, searchable sub-tasks.
- **Researcher**: Extracts key facts, figures, and insights (via web search or internal knowledge).
- **Synthesizer**: Aggregates all findings into a structured, markdown-formatted final response.

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Agent Framework** | AutoGen AgentChat 0.4 |
| **LLM Provider** | Groq (Llama 3.3 70B) |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | React 18 + Vite |
| **Communication** | WebSockets (Real-time event streaming) |

## 🚀 Quick Start

### 1. Backend Setup
```bash
# Clone the repo
git clone https://github.com/Tee808-bigD/Workflow.git
cd Workflow
# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Configure .env
cp .env.example .env
# Run server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup
```bash
# Install dependencies
npm install
# Configure environment
# Create .env in root with VITE_WS_URL=ws://localhost:8000/ws/research
npm run dev
```

## 📖 Deployment Guide
For detailed instructions on deploying to Netlify and Azure, please refer to the [DEPLOYMENT.md](./DEPLOYMENT.md) file.

## 🔒 Security
- **API Keys**: Managed via `.env` files (ignored by git).
- **CORS**: Configurable via `CORS_ORIGIN` to protect the API.
- **Real-time Updates**: Built with an event-driven WebSocket architecture for low-latency updates.

---
*Built for the Microsoft Build AI Hackathon*
