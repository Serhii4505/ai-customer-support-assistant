# MVP specification

## Purpose
Demonstrate a practical support and sales automation for a small service business. Use a fictional business and synthetic customer data for the portfolio. Demo messages are in English; development guidance can be in Russian.

## Required behavior
1. Accept a customer message with conversation_id and unique message_id.
2. Answer common questions using the supplied business profile and FAQ.
3. Collect name, contact details, and request over multiple turns, asking for one missing item at a time.
4. Classify intent as support, sales, or unknown.
5. Assign lead status: new, warm, or hot. Hot requires explicit buying/booking intent and a contact method. Store an explanation; this is a rule-based label, not a probability.
6. Save conversation history and lead updates to SQLite. Repeated message_id must not create duplicate messages or handoffs.
7. Flag a manager handoff for a hot lead, an explicit request for a person, or a question that cannot be answered from the knowledge base.
8. Return a useful response without inventing prices, policies, availability, or completed actions.

## First demo channel
An n8n webhook with sample JSON requests. Add a chat interface only after the complete request-to-storage flow works.

## API design target
GET /health — service readiness.
POST /chat — conversation_id, message_id, message, optional customer fields.
Response — reply, intent, lead (name, contact, request, status, reason), handoff_required, handoff_reason.
The initial contract is in docs/API.md; these endpoints are planned, not implemented yet.

## Handoff
First save a local handoff record and expose it in the response. Later connect an actual delivery channel in n8n. Do not say a manager was notified unless delivery succeeded. Keep a pending/failed state for retry.

## Acceptance scenarios
- FAQ question gets a grounded answer.
- Unknown answer results in a handoff flag, without invented facts.
- Name and contact survive across messages in the same conversation.
- Separate conversations do not share customer details.
- Explicit buying intent plus contact becomes a hot lead with a reason.
- Repeated message_id does not duplicate storage or notifications.
- Invalid input is rejected; model/network failure produces a controlled response.
- A demo shows the customer reply, persisted lead, and handoff status.

## Outside the first MVP
Payments, CRM integration, multiple messaging channels, voice calls, vector databases, production hosting, and advanced analytics.
