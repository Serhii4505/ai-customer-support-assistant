# Planned API contract

Local development endpoint: POST /chat

Request:
```json
{
  "conversation_id": "demo-001",
  "message_id": "demo-001-msg-001",
  "message": "I want to book a consultation. My name is Alex.",
  "customer": {"name": null, "contact": null}
}
```

Response shape:
```json
{
  "reply": "Thanks, Alex. What email address can we use to contact you?",
  "intent": "sales",
  "lead": {
    "name": "Alex",
    "contact": null,
    "request": "Book a consultation",
    "status": "warm",
    "reason": "Booking intent present; contact missing"
  },
  "handoff_required": false,
  "handoff_reason": null
}
```

This is an illustrative contract, not output from a running model.
Reject empty identifiers and blank messages; cap message length at 4000 characters. Missing customer fields remain null. A repeated message_id with different content should return a conflict. External access will require authentication before exposure.
