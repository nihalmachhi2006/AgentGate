from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path

from app import audit
from app.catalog import list_products
from app.agent import chat

app = FastAPI(title="AgentGate")
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

audit.init_db()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = None


@app.get("/catalog")
def get_catalog():
    return list_products()


@app.post("/chat")
def post_chat(req: ChatRequest):
    reply, updated_history = chat(req.session_id, req.message, req.history)
    return {"reply": reply, "history": updated_history}


@app.get("/audit")
def get_audit(session_id: Optional[str] = None, limit: int = 50):
    return audit.get_log(session_id=session_id, limit=limit)


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")
