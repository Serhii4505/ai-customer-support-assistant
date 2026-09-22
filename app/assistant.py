from app.ai_client import ai_is_configured, generate_ai_reply
from app.knowledge import find_faq_answer


def process_message(
    message: str,
    name: str | None = None,
    contact: str | None = None,
    original_request: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    text = message.casefold()
    has_contact = bool(contact and contact.strip())

    if text.strip(" \t\n.!?,") in (
        "спасибо", "спасибо большое", "благодарю",
        "thanks", "thank you"
    ):
        return {
            "reply": "Пожалуйста! Если появятся вопросы, напишите.",
            "intent": "unknown",
            "handoff_required": False,
        }

    if any(word in text for word in (
        "менеджер", "оператор", "человек", "manager", "human"
    )):
        if original_request:
            reply = (
                "Ваш запрос сохранён: "
                f"«{original_request}». "
            )
            if has_contact:
                reply += "Контакт для связи указан."
            else:
                reply += "Оставьте контакт для связи с менеджером."
        else:
            reply = (
                "Контакт для связи указан. "
                "Опишите вопрос, который хотите обсудить с менеджером."
                if has_contact
                else "Опишите ваш вопрос и оставьте контакт для связи."
            )

        return {
            "reply": reply,
            "intent": "support",
            "handoff_required": True,
        }

    faq_answer = find_faq_answer(message)
    if faq_answer is not None:
        return {
            "reply": faq_answer,
            "intent": "sales",
            "handoff_required": False,
        }

        if ai_is_configured():
            ai_reply = generate_ai_reply(
                message,
                history=history,
            )

        if ai_reply:
            return {
                "reply": ai_reply,
                "intent": "unknown",
                "handoff_required": False,
            }

    if any(word in text for word in (
        "цен", "стоим", "заказ", "купить", "консультац",
        "price", "cost", "buy", "book"
    )):
        return {
            "reply": "Какая услуга вас интересует? Уточните, что вам нужно.",
            "intent": "sales",
            "handoff_required": False,
        }

    if text.strip(" \t\n.!?,") in (
        "привет", "здравствуйте", "добрый день", "hello", "hi"
    ):
        return {
            "reply": "Здравствуйте! Чем можем помочь?",
            "intent": "unknown",
            "handoff_required": False,
        }

    reply = (
        "В базе знаний нет точного ответа на ваш вопрос. "
        "Нужно уточнение менеджера. Контакт для связи указан."
        if has_contact
        else
        "В базе знаний нет точного ответа на ваш вопрос. "
        "Оставьте контакт для уточнения у менеджера."
    )

    return {
        "reply": reply,
        "intent": "unknown",
        "handoff_required": True,
    }

def choose_original_request(
    message: str,
    previous_request: str | None = None,
    name: str | None = None,
    contact: str | None = None,
) -> str | None:
    if previous_request:
        return previous_request

    text = message.strip()
    normalized = text.casefold().strip(" \t\n.!?,")

    short_messages = {
        "привет", "здравствуйте", "добрый день", "hello", "hi",
        "спасибо", "спасибо большое", "thanks", "thank you",
        "да", "нет", "ок", "окей", "yes", "no", "ok",
        "хочу поговорить с менеджером",
        "соедините с менеджером",
    }

    if normalized in short_messages:
        return None

    for value in (name, contact):
        if value and text.casefold() == value.strip().casefold():
            return None

    return text or None