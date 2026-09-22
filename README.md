# AI Customer Support / Sales Assistant

AI-powered customer support and sales automation project built with Python, FastAPI, SQLite and n8n.

The assistant can process customer messages, answer common questions, store conversation history, extract lead information, classify lead interest and automatically notify a manager when a hot lead appears.

## Features

- Customer support API built with FastAPI
- FAQ-based responses
- Optional OpenAI integration
- Automatic fallback when the AI API is unavailable
- Conversation history by `conversation_id`
- User and assistant message roles
- Automatic name extraction
- Automatic email and phone extraction
- Automatic customer request extraction
- Lead scoring:
  - `cold`
  - `warm`
  - `hot`
- SQLite lead storage
- Manager handoff queue
- n8n workflow automation
- Automatic Gmail notification for hot leads

## Example Workflow

Customer message:

> My name is John. Ready to start the project. When can you begin?

The system extracts:

- Name: John
- Contact: test@example.com
- Request: Ready to start the project. When can you begin
- Lead score: hot

The hot lead is then automatically passed through n8n and a Gmail notification is sent to the manager.

## Architecture

```text
Customer
   |
   v
n8n Webhook
   |
   v
FastAPI /chat
   |
   +--> FAQ / Rule-based Assistant
   |
   +--> Optional OpenAI API
   |
   +--> Conversation History
   |
   +--> Lead Data Extraction
   |
   +--> Lead Scoring
   |
   v
SQLite Database
   |
   v
n8n Hot Lead Check
   |
   v
Gmail Notification
   |
   v
Manager