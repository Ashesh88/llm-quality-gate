"""
Page Object Model (POM) for the AI Operations Web Dashboard.
"""

from playwright.sync_api import Page, expect

class DashboardPage:
    def __init__(self, page: Page, base_url: str = "http://localhost:8000"):
        self.page = page
        self.base_url = base_url

        # Locators
        self.channel_select = page.locator("#channel")
        self.sender_input = page.locator("#sender")
        self.subject_input = page.locator("#subject")
        self.body_textarea = page.locator("#body")
        self.submit_button = page.locator(".btn-submit")
        self.trace_box = page.locator("#trace-terminal")
        self.ticket_result = page.locator("#ticket-result")
        self.slack_result = page.locator("#slack-result")
        self.response_preview = page.locator("#response-preview")
        self.tickets_table_body = page.locator("#tickets-body")
        self.refresh_tickets_button = page.locator("button:has-text('Refresh')")

    def navigate(self):
        self.page.goto(f"{self.base_url}/")
        self.page.wait_for_load_state("domcontentloaded")

    def submit_complaint(
        self,
        sender: str,
        subject: str,
        body: str,
        channel: str = "email"
    ):
        self.channel_select.select_option(channel)
        self.sender_input.fill(sender)
        if channel == "email":
            self.subject_input.fill(subject)
        self.body_textarea.fill(body)
        self.submit_button.click()

    def wait_for_response(self, timeout_ms: int = 8000):
        # Wait until trace-terminal contains completion steps
        self.page.wait_for_selector("#trace-terminal", timeout=timeout_ms)
        self.page.wait_for_function(
            "() => document.getElementById('response-preview').innerText.length > 25",
            timeout=timeout_ms
        )

    def get_ticket_text(self) -> str:
        return self.ticket_result.inner_text()

    def get_response_text(self) -> str:
        return self.response_preview.inner_text()

    def get_trace_text(self) -> str:
        return self.trace_box.inner_text()
