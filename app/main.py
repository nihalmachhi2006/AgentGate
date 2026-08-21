import json
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path

from app import audit
from app.catalog import list_products
from app.agent import chat
from app.config import RAZORPAY_KEY_ID, RAZORPAY_CONFIGURED

app = FastAPI(title="AgentGate")
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

audit.init_db()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: Optional[List[Dict[str, Any]]] = None


@app.get("/razorpay-config")
def razorpay_config():
    """
    Returns the PUBLIC Razorpay key_id so the browser can initialise Checkout.js.
    The secret key never leaves the server.
    """
    return {"key_id": RAZORPAY_KEY_ID, "configured": RAZORPAY_CONFIGURED}


@app.get("/catalog")
def get_catalog():
    return list_products()


@app.post("/chat")
def post_chat(req: ChatRequest):
    reply, updated_history = chat(req.session_id, req.message, req.history)

    # Scan the updated history (newest first) for a successful, real Razorpay order
    # created during this turn, so the frontend can open Checkout.js immediately.
    pending_payment = None
    for msg in reversed(updated_history):
        if msg.get("role") == "tool":
            try:
                content = json.loads(msg["content"])
                if (
                    content.get("success")
                    and content.get("razorpay_order_id")
                    and not content.get("mock")
                ):
                    pending_payment = {
                        "order_id": content["razorpay_order_id"],
                        "amount_inr": content["amount_inr"],
                        "key_id": content.get("key_id") or RAZORPAY_KEY_ID,
                    }
                    break
            except (json.JSONDecodeError, KeyError):
                pass

    return {"reply": reply, "history": updated_history, "pending_payment": pending_payment}


@app.get("/audit")
def get_audit(session_id: Optional[str] = None, limit: int = 50):
    return audit.get_log(session_id=session_id, limit=limit)


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")
