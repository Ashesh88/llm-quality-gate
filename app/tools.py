import os
import requests
import json
from typing import Dict, Any, Optional
from app.config import settings
from app.db import create_ticket
from app.rag_engine import rag_engine

# Diagnostic flag to simulate tool outage for failure-recovery testing
_SIMULATE_TOOL_FAILURE = False

def set_tool_failure_simulation(enabled: bool):
    global _SIMULATE_TOOL_FAILURE
    _SIMULATE_TOOL_FAILURE = enabled

def get_tool_failure_simulation() -> bool:
    return _SIMULATE_TOOL_FAILURE

def tool_search_knowledge_base(query: str) -> Dict[str, Any]:
    """Retrieves authoritative company policies and technical documentation."""
    docs = rag_engine.retrieve(query, top_k=2)
    if not docs:
        return {
            "found": False,
            "context": "No specific internal documentation matched the query.",
            "sources": []
        }

    combined_text = "\n\n---\n\n".join([f"[{d['source']}] (Score: {d['score']}):\n{d['content']}" for d in docs])
    return {
        "found": True,
        "context": combined_text,
        "sources": [d["source"] for d in docs]
    }

def tool_create_jira_ticket(
    customer_id: str,
    category: str,
    priority: str,
    title: str,
    description: str
) -> Dict[str, Any]:
    """Creates a new Jira / CRM incident ticket for technical bugs or refund escalations."""
    if _SIMULATE_TOOL_FAILURE or os.getenv("SIMULATE_TOOL_FAILURE") == "1":
        # Simulate downstream 503 / timeout for testing resilience & recovery
        return {
            "status": "FAILED",
            "error": "JiraServiceUnavailable: 503 Service Unavailable / Connection Timeout",
            "fallback_action": "QUEUED_FOR_RETRY",
            "assigned_queue": f"{category}_SUPPORT_RETRY"
        }

    valid_priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    if priority.upper() not in valid_priorities:
        priority = "MEDIUM"

    ticket = create_ticket(
        customer_id=customer_id,
        category=category,
        priority=priority.upper(),
        title=title,
        description=description
    )
    return {
        "status": "SUCCESS",
        "ticket_key": ticket["ticket_key"],
        "ticket_id": ticket["id"],
        "assigned_queue": f"{category}_SUPPORT",
        "details": f"Ticket {ticket['ticket_key']} created with priority {priority.upper()}."
    }

def tool_send_slack_alert(
    channel: str,
    message: str,
    urgency: str = "NORMAL"
) -> Dict[str, Any]:
    """Sends an incident notification to the engineering or support Slack channel."""
    emoji = "🚨" if urgency.upper() in ["HIGH", "CRITICAL"] else "📢"
    payload = {
        "text": f"{emoji} *[{urgency.upper()}] Operations Alert*\n*Channel:* #{channel}\n*Details:* {message}"
    }

    if settings.SLACK_WEBHOOK_URL:
        try:
            resp = requests.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=5)
            delivered = (resp.status_code == 200)
        except Exception:
            delivered = False
    else:
        # Mock mode: successfully simulated
        delivered = True

    return {
        "status": "DELIVERED" if delivered else "FAILED",
        "mock_mode": not bool(settings.SLACK_WEBHOOK_URL),
        "channel": channel,
        "urgency": urgency,
        "preview": payload["text"]
    }
