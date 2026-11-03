# Technical Support & Incident Escalation Policy

## 1. Webhook and API Outages
- If customers report `500 Internal Server Error`, `Connection Timeout`, or failing webhooks, our engineering team flags this as a **P1 (High Urgency)** incident.
- An incident ticket MUST be filed in Jira/CRM under `INCIDENT_TECHNICAL` with priority `HIGH`.
- The engineering team on-call must be notified immediately via the `#incident-alerts` Slack channel.

## 2. Authentication and API Keys
- API keys can be rolled with zero downtime via the Developer Dashboard > Security > Rotate Key.
- Expired JWT tokens return `401 Unauthorized`. Clients must refresh tokens using the `/auth/refresh` endpoint with their valid refresh token.

## 3. SLA & Response Matrix
- **Priority 1 (Critical Outage):** First response < 15 minutes, resolution target < 2 hours.
- **Priority 2 (High / Degraded Performance):** First response < 1 hour.
- **Priority 3 (General Query / How-to):** First response < 24 hours.
