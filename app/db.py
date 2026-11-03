import sqlite3
import datetime
from typing import List, Dict, Any, Optional
from app.config import settings

def get_connection():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Support Tickets table (Simulating Jira / CRM backend)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_key TEXT UNIQUE NOT NULL,
            customer_id TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Audit & Observability logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL,
            customer TEXT NOT NULL,
            incoming_message TEXT NOT NULL,
            intent TEXT NOT NULL,
            rag_sources TEXT,
            action_taken TEXT,
            response TEXT NOT NULL,
            slack_alert_sent BOOLEAN DEFAULT 0,
            latency_ms REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def create_ticket(customer_id: str, category: str, priority: str, title: str, description: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    # Generate sequential Jira-like key
    cursor.execute("SELECT COUNT(*) FROM tickets")
    count = cursor.fetchone()[0] + 101
    ticket_key = f"{settings.JIRA_PROJECT_KEY}-{count}"

    cursor.execute("""
        INSERT INTO tickets (ticket_key, customer_id, category, priority, title, description, status)
        VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
    """, (ticket_key, customer_id, category, priority, title, description))

    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()

    return {
        "id": ticket_id,
        "ticket_key": ticket_key,
        "customer_id": customer_id,
        "category": category,
        "priority": priority,
        "title": title,
        "description": description,
        "status": "OPEN",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

def get_all_tickets(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def log_interaction(
    channel: str,
    customer: str,
    incoming_message: str,
    intent: str,
    rag_sources: str,
    action_taken: str,
    response: str,
    slack_alert_sent: bool,
    latency_ms: float
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (channel, customer, incoming_message, intent, rag_sources, action_taken, response, slack_alert_sent, latency_ms)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (channel, customer, incoming_message, intent, rag_sources, action_taken, response, slack_alert_sent, latency_ms))
    conn.commit()
    conn.close()

def get_recent_logs(limit: int = 30) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
