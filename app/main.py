from app.extraction import (
    extract_contact,
    extract_name,
    extract_request,
    score_lead,
)
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.assistant import process_message, choose_original_request
from app.database import (
    init_db,
    save_message,
    save_lead,
    get_lead,
    save_handoff,
    get_handoff,
    get_pending_handoffs,
    complete_handoff,
    get_conversation,
    save_conversation,
    save_conversation_lead,
    get_conversation_messages,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI Customer Support / Sales Assistant",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    conversation_id: str | None = Field(default=None, min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=4000)
    name: str | None = Field(default=None, max_length=100)
    contact: str | None = Field(default=None, max_length=200)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Сообщение не должно быть пустым")
        return value

    @field_validator("name", "contact")
    @classmethod
    def normalize_optional_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/conversations/{conversation_id}/messages")
def read_conversation_messages(conversation_id: str):
    messages = get_conversation_messages(conversation_id)

    if not messages:
        raise HTTPException(
            status_code=404,
            detail="История разговора не найдена",
        )

    return {
        "conversation_id": conversation_id,
        "messages": messages,
    }

@app.post("/chat")
def chat(request: ChatRequest):
    conversation_id = (
        request.conversation_id.strip()
        if request.conversation_id
        else None
    )
    conversation_id = conversation_id or None

    previous = {}
    if conversation_id:
        previous = get_conversation(conversation_id) or {}

    history = []

    if conversation_id:
        history = get_conversation_messages(conversation_id)

    detected_name = extract_name(request.message)
    detected_contact = extract_contact(request.message)

    name = (
        request.name
        or detected_name
        or previous.get("name")
    )

    contact = (
        request.contact
        or detected_contact
        or previous.get("contact")
    )

    detected_request = extract_request(
        request.message,
        name=name,
        contact=contact,
    )
    lead_score = score_lead(request.message)

    result = process_message(
        message=request.message,
        name=name,
        contact=contact,
        original_request=previous.get("request"),
        history=history,
    )
    message_id = save_message(
        request.message,
        conversation_id=conversation_id,
    )

    assistant_message_id = None

    if conversation_id:
        assistant_message_id = save_message(
            result["reply"],
            conversation_id=conversation_id,
            role="assistant",
        )

    lead_id = None
    if name or contact:
        if conversation_id:
            lead_id = save_conversation_lead(
                conversation_id=conversation_id,
                message_id=message_id,
                name=name,
                contact=contact,
                lead_score=lead_score,
            )
        else:
            lead_id = save_lead(
                message_id=message_id,
                name=name,
                contact=contact,
                lead_score=lead_score,
            )

    handoff_id = None
    if result["handoff_required"]:
        handoff_id = save_handoff(
            message_id=message_id,
            lead_id=lead_id,
            conversation_id=conversation_id,
        )

    if conversation_id:
        original_request = choose_original_request(
            message=detected_request or request.message,
            previous_request=previous.get("request"),
            name=name,
            contact=contact,
        )

        save_conversation(
            conversation_id=conversation_id,
            name=name,
            contact=contact,
            request=original_request,
        )

    return {
        **result,
        "conversation_id": conversation_id,
        "message": request.message,
        "message_id": message_id,
        "assistant_message_id": assistant_message_id,
        "lead_id": lead_id,
        "handoff_id": handoff_id,
        "mode": "demo",
        "lead_score": lead_score,
        "name": name,
        "contact": contact,
        "original_request": detected_request,
    }


@app.get("/leads/{lead_id}")
def read_lead(lead_id: int):
    lead = get_lead(lead_id)

    if lead is None:
        raise HTTPException(
            status_code=404,
            detail="Заявка не найдена",
        )

    return lead


@app.get("/handoffs")
def list_pending_handoffs():
    return get_pending_handoffs()


@app.get("/handoffs/{handoff_id}")
def read_handoff(handoff_id: int):
    handoff = get_handoff(handoff_id)

    if handoff is None:
        raise HTTPException(
            status_code=404,
            detail="Запрос менеджеру не найден",
        )

    return handoff


@app.post("/handoffs/{handoff_id}/complete")
def mark_handoff_completed(handoff_id: int):
    if not complete_handoff(handoff_id):
        raise HTTPException(
            status_code=404,
            detail="Запрос менеджеру не найден",
        )

    return {
        "id": handoff_id,
        "status": "completed",
    }