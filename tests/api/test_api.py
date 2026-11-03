import time
import pytest
import requests
from framework.config import config
from tests.conftest import SESSION_METRICS

BASE_URL = "http://127.0.0.1:8000"

class TestFastAPIQualityGate:

    def _measure_request(self, method: str, url: str, **kwargs):
        start = time.time()
        resp = requests.request(method, url, timeout=10, **kwargs)
        latency_ms = round((time.time() - start) * 1000, 2)
        SESSION_METRICS["api_latencies"].append(latency_ms)
        return resp, latency_ms

    def test_swagger_and_openapi_schema(self):
        """Validates FastAPI OpenAPI JSON specification and Swagger UI availability."""
        resp, latency = self._measure_request("GET", f"{BASE_URL}/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()

        assert "openapi" in schema
        assert "paths" in schema
        paths = schema["paths"]

        # Ensure all required production routes are documented in Swagger
        expected_routes = [
            "/api/health",
            "/webhook/email",
            "/webhook/whatsapp",
            "/api/chat",
            "/api/tickets",
            "/api/logs"
        ]
        for route in expected_routes:
            assert route in paths, f"Route '{route}' missing from OpenAPI specification!"

        # Check /docs UI
        docs_resp, _ = self._measure_request("GET", f"{BASE_URL}/docs")
        assert docs_resp.status_code == 200

    def test_health_endpoint(self):
        """Validates /api/health service check and latency."""
        resp, latency = self._measure_request("GET", f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert latency < 500  # Health check must be sub-500ms

    def test_email_webhook_endpoint(self):
        """Validates /webhook/email processing, schema conformance, and latency SLA."""
        payload = {
            "sender": "cto@enterprise.io",
            "subject": "CRITICAL: 500 Outage on payment endpoint",
            "body": "Production webhook listeners are receiving 500 internal server error."
        }
        resp, latency = self._measure_request("POST", f"{BASE_URL}/webhook/email", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        # Schema validation
        assert "intent" in data
        assert "urgency" in data
        assert "response" in data
        assert "ticket" in data
        assert data["ticket"] is not None
        assert "OPS-" in data["ticket"]["ticket_key"]

        # Latency SLA Check (< 3000ms)
        assert latency < config.API_MAX_LATENCY_MS, (
            f"Email webhook latency {latency}ms exceeded SLA threshold of {config.API_MAX_LATENCY_MS}ms!"
        )

    def test_whatsapp_webhook_endpoint(self):
        """Validates /webhook/whatsapp conversational webhook endpoint."""
        payload = {
            "sender": "+919876543210",
            "message": "Hey team, how much is the Starter plan per month?"
        }
        resp, latency = self._measure_request("POST", f"{BASE_URL}/webhook/whatsapp", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["channel"] == "whatsapp"
        assert "response" in data
        assert "29" in data["response"]
        assert latency < config.API_MAX_LATENCY_MS

    def test_chat_multi_turn_endpoint(self):
        """Validates /api/chat multi-turn conversational session endpoint."""
        session_id = "test-sess-9021"
        payload = {
            "session_id": session_id,
            "sender": "user@domain.com",
            "message": "I would like to know your refund policy for annual subscriptions.",
            "channel": "chat"
        }
        resp, latency = self._measure_request("POST", f"{BASE_URL}/api/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["session_id"] == session_id
        assert "refund" in data["response"].lower()

    def test_tickets_and_audit_logs_endpoints(self):
        """Validates /api/tickets and /api/logs audit endpoints."""
        tickets_resp, _ = self._measure_request("GET", f"{BASE_URL}/api/tickets?limit=10")
        assert tickets_resp.status_code == 200
        tickets = tickets_resp.json()
        assert isinstance(tickets, list)

        logs_resp, _ = self._measure_request("GET", f"{BASE_URL}/api/logs?limit=10")
        assert logs_resp.status_code == 200
        logs = logs_resp.json()
        assert isinstance(logs, list)

    def test_invalid_payload_validation_error(self):
        """Negative test: validates 422 Unprocessable Entity when required fields are missing."""
        invalid_payload = {"sender": "not_enough_fields"}
        resp, _ = self._measure_request("POST", f"{BASE_URL}/webhook/email", json=invalid_payload)
        assert resp.status_code == 422
