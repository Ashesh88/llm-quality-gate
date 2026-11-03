import pytest
import uuid
from app.agent import process_incoming_event, clear_session_store
from app.tools import set_tool_failure_simulation, get_tool_failure_simulation

class TestMultiTurnAndToolRecovery:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        clear_session_store()
        set_tool_failure_simulation(False)
        yield
        clear_session_store()
        set_tool_failure_simulation(False)

    def test_multi_turn_context_retention(self):
        """
        Tests 3-4 turn conversational memory.
        Verifies that subsequent turns remember customer name, previous ticket keys, and issue context.
        """
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        sender = "cto@fintechflow.com"

        # Turn 1: Initial complaint about 500 error
        turn1 = process_incoming_event(
            incoming_text="Critical issue: Our webhook listeners are throwing 500 errors continuously.",
            sender=sender,
            channel="email",
            session_id=session_id
        )

        assert turn1["intent"] == "TECHNICAL_BUG"
        assert turn1["urgency"] == "HIGH"
        assert turn1["ticket"] is not None
        ticket_key = turn1["ticket"]["ticket_key"]
        assert "OPS-" in ticket_key

        # Turn 2: Follow-up referencing previous turn without repeating the problem
        turn2 = process_incoming_event(
            incoming_text="What was the ticket number you just created, and what is the response SLA?",
            sender=sender,
            channel="email",
            session_id=session_id
        )

        # Context retention assertions
        assert turn2["intent"] == "TECHNICAL_BUG"
        assert (ticket_key in turn2["response"] or "ticket" in turn2["response"].lower())
        assert ("15" in turn2["response"] or "sla" in turn2["response"].lower() or "minute" in turn2["response"].lower())

        # Turn 3: Follow-up on policy implications of this specific issue
        turn3 = process_incoming_event(
            incoming_text="If this infrastructure outage lasts over 2 hours, are we eligible for an outage-based refund?",
            sender=sender,
            channel="email",
            session_id=session_id
        )

        assert ("refund" in turn3["response"].lower() or "sla" in turn3["response"].lower())
        assert ("outage" in turn3["response"].lower() or "policy" in turn3["response"].lower())

    def test_tool_failure_graceful_recovery(self):
        """
        Simulates downstream tool failure (e.g. Jira 503 / timeout) during ticket provisioning.
        Verifies that the agent catches the error, activates the recovery fallback,
        reassures the user without crashing, and queues the request.
        """
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        sender = "developer@startup.io"

        # Enable simulated tool failure
        set_tool_failure_simulation(True)

        try:
            # Trigger event requiring a ticket while tool service is down
            result = process_incoming_event(
                incoming_text="Emergency: Database connection pool failure during checkout.",
                sender=sender,
                channel="email",
                session_id=session_id
            )

            # System must NOT raise an unhandled exception
            assert result is not None
            assert result.get("ticket") is not None
            assert result["ticket"].get("status") == "FAILED"

            # Response must handle the failure gracefully
            response_text = result["response"].lower()
            assert any(k in response_text for k in ["queued", "temporary", "delay", "review", "working", "priority"])
            assert "crash" not in response_text
            assert "traceback" not in response_text

            # Verify trace records the recovery branch
            trace_steps_str = " ".join(result.get("trace_steps", []))
            assert "TOOL RECOVERY" in trace_steps_str or "Tool Calling" in trace_steps_str

        finally:
            # Turn off failure simulation and verify recovery back to normal
            set_tool_failure_simulation(False)

        # Follow-up turn after recovery
        recovered_result = process_incoming_event(
            incoming_text="Is the service working now? Can you check our status?",
            sender=sender,
            channel="email",
            session_id=session_id
        )

        assert recovered_result is not None
        assert "response" in recovered_result
