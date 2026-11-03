import os
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.config import settings
from app.db import init_db, get_all_tickets, get_recent_logs
from app.agent import process_incoming_event, clear_session_store

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Event-Driven AI Operations Agent evaluated via DeepEval CI Quality Gates."
)

@app.on_event("startup")
def on_startup():
    init_db()

# Request Models
class EmailWebhookPayload(BaseModel):
    sender: str = Field(..., example="client@enterprise.com", description="Sender email address")
    subject: str = Field(..., example="Critical 500 Error in Webhook Dispatch", description="Email subject")
    body: str = Field(..., example="Our production webhook endpoints are failing with 500 errors.", description="Email body content")

class WhatsAppWebhookPayload(BaseModel):
    sender: str = Field(..., example="+919140382381", description="Sender phone number")
    message: str = Field(..., example="Hey, I purchased the starter plan 2 days ago and want a refund.", description="Chat message")

class ChatConversationPayload(BaseModel):
    session_id: str = Field(..., example="sess-4091", description="Unique conversation session id for multi-turn tracking")
    sender: str = Field(default="client@enterprise.com", example="client@enterprise.com")
    message: str = Field(..., example="Can you check my refund request?")
    channel: str = Field(default="chat", example="chat")

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_ui():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "LLM Quality Gate - AI Operations Agent is live. Visit /docs for Swagger UI."}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "groq_enabled": bool(settings.GROQ_API_KEY),
        "openai_enabled": bool(settings.OPENAI_API_KEY)
    }

@app.post("/webhook/email", status_code=status.HTTP_200_OK)
def handle_email_webhook(payload: EmailWebhookPayload) -> Dict[str, Any]:
    full_text = f"Subject: {payload.subject}\n\nBody: {payload.body}"
    result = process_incoming_event(
        incoming_text=full_text,
        sender=payload.sender,
        channel="email"
    )
    return result

@app.post("/webhook/whatsapp", status_code=status.HTTP_200_OK)
def handle_whatsapp_webhook(payload: WhatsAppWebhookPayload) -> Dict[str, Any]:
    result = process_incoming_event(
        incoming_text=payload.message,
        sender=payload.sender,
        channel="whatsapp"
    )
    return result

@app.post("/api/chat", status_code=status.HTTP_200_OK)
def handle_chat_turn(payload: ChatConversationPayload) -> Dict[str, Any]:
    result = process_incoming_event(
        incoming_text=payload.message,
        sender=payload.sender,
        channel=payload.channel,
        session_id=payload.session_id
    )
    return result

@app.get("/api/tickets")
def list_tickets(limit: int = 25) -> List[Dict[str, Any]]:
    return get_all_tickets(limit=limit)

@app.get("/api/logs")
def list_logs(limit: int = 25) -> List[Dict[str, Any]]:
    return get_recent_logs(limit=limit)
