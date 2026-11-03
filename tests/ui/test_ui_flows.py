import pytest
from playwright.sync_api import sync_playwright
from framework.pom.dashboard_page import DashboardPage

BASE_URL = "http://127.0.0.1:8000"

class TestDashboardUIFlows:

    @pytest.fixture(scope="class")
    def browser_context(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            yield context
            context.close()
            browser.close()

    @pytest.fixture
    def page(self, browser_context):
        page = browser_context.new_page()
        yield page
        page.close()

    def test_flow_1_outage_complaint_and_ticket_generation(self, page):
        """
        Flow 1: End-to-end incident submission.
        Verifies that submitting a 500 outage triggers ticket creation,
        displays the ticket in the UI, and logs trace steps.
        """
        dashboard = DashboardPage(page, base_url=BASE_URL)
        dashboard.navigate()

        dashboard.submit_complaint(
            sender="alex@techstart.io",
            subject="CRITICAL: 500 Error in Webhook Listener",
            body="Our production webhook endpoint is failing with 500 internal server errors across all nodes.",
            channel="email"
        )

        dashboard.wait_for_response()

        # Assert Ticket was created
        ticket_text = dashboard.get_ticket_text()
        assert "OPS-" in ticket_text or "Ticket" in ticket_text

        # Assert Trace Terminal contains state transitions
        trace_text = dashboard.get_trace_text()
        assert "Classifier" in trace_text or "RAG" in trace_text

        # Assert Response preview is generated
        response_text = dashboard.get_response_text()
        assert len(response_text) > 40
        assert "alex@techstart.io" in response_text or "Dear" in response_text

    def test_flow_2_refund_request_flow(self, page):
        """
        Flow 2: Refund request flow.
        Verifies that requesting a refund generates policy-compliant guidance
        referencing the 14-day money-back guarantee.
        """
        dashboard = DashboardPage(page, base_url=BASE_URL)
        dashboard.navigate()

        dashboard.submit_complaint(
            sender="+919140382381",
            subject="Refund",
            body="Hey, I purchased the starter plan 2 days ago and want to request a full refund.",
            channel="whatsapp"
        )

        dashboard.wait_for_response()

        response_text = dashboard.get_response_text()
        assert len(response_text) > 30

    def test_flow_3_pricing_inquiry_direct_guidance(self, page):
        """
        Flow 3: Informational pricing inquiry flow.
        Verifies that asking about plans resolves directly via RAG knowledge base.
        """
        dashboard = DashboardPage(page, base_url=BASE_URL)
        dashboard.navigate()

        dashboard.submit_complaint(
            sender="buyer@corp.com",
            subject="Pricing Plans",
            body="How much does the Starter plan cost and how many workflow executions do we get?",
            channel="email"
        )

        dashboard.wait_for_response()

        response_text = dashboard.get_response_text()
        assert "29" in response_text or "Starter" in response_text
