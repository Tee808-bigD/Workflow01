"""
main.py — FastAPI app
WebSocket /ws/research streams agent events in real time
"""

import json
import os
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from agents import config_status, run_swarm

load_dotenv()

app = FastAPI(title="Research Swarm API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "Research Swarm API",
        "status": "ok",
        "endpoints": {
            "health": "/health",
            "config": "/config",
            "websocket": "/ws/research",
            "docs": "/docs",
        },
        "message": "Use the React app for the UI and connect to /ws/research for live runs.",
    }


@app.get("/health")
async def health():
    config = config_status()
    return {"status": "ok" if config["ok"] else "config_error", "config": config}


@app.get("/config")
async def config():
    return config_status()


@app.websocket("/ws/research")
async def research_ws(websocket: WebSocket):
    """
    Client sends: { "question": "..." }
    Server streams: agent event dicts as JSON lines
    """
    await websocket.accept()

    try:
        raw = await websocket.receive_text()
        payload = json.loads(raw)
        question = payload.get("question", "").strip()

        if not question:
            await websocket.send_json({"agent": "system", "status": "error", "message": "No question provided"})
            await websocket.close()
            return

        config = config_status()
        if not config["ok"]:
            await websocket.send_json({"agent": "system", "status": "error", "message": "; ".join(config["issues"])})
            await websocket.close()
            return

        async for event in run_swarm(question):
            await websocket.send_json(event)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"agent": "system", "status": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
