import re


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"
)


def extract_contact(message: str) -> str | None:
    email_match = EMAIL_PATTERN.search(message)

    if email_match:
        return email_match.group(0)

    phone_match = PHONE_PATTERN.search(message)

    if phone_match:
        return phone_match.group(0).strip()

    return None

NAME_PATTERNS = [
    re.compile(
        r"\bменя зовут\s+([A-Za-zА-Яа-яЁёІіЇїЄє'-]{2,50})",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*я\s+([A-ZА-ЯЁІЇЄ][A-Za-zА-Яа-яЁёІіЇїЄє'-]{1,49})\s*[.!]?\s*$",
    ),
    re.compile(
        r"\bmy name is\s+([A-Za-z'-]{2,50})",
        re.IGNORECASE,
    ),
]


def extract_name(message: str) -> str | None:
    for pattern in NAME_PATTERNS:
        match = pattern.search(message)

        if match:
            name = match.group(1).strip(" .,!?:;")
            if name:
                return name

    return None

def extract_request(
    message: str,
    name: str | None = None,
    contact: str | None = None,
) -> str | None:
    text = message.strip()

    if contact:
        text = re.sub(
            re.escape(contact),
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\b(моя\s+почта|мой\s+email|email|e-mail|почта)\b\s*[:\-]?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

    if name:
        text = re.sub(
            rf"\bменя зовут\s+{re.escape(name)}\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"\bmy name is\s+{re.escape(name)}\b",
            "",
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(
        r"^\s*(здравствуйте|привет|добрый день|hello|hi)[,!.\s]*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(r"\s+", " ", text)
    text = text.strip(" ,.!?:;-")

    normalized = text.casefold()

    if not text or normalized in {
        "спасибо",
        "благодарю",
        "да",
        "нет",
        "ок",
        "thanks",
        "thank you",
        "yes",
        "no",
        "ok",
    }:
        return None

    return text

def score_lead(message: str) -> str:
    text = message.casefold()

    hot_keywords = (
        "готов купить",
        "готов заказать",
        "хочу заказать",
        "хочу купить",
        "готов начать",
        "можем начать",
        "когда можете начать",
        "send invoice",
        "ready to buy",
        "ready to start",
        "want to order",
    )

    warm_keywords = (
        "цена",
        "стоимость",
        "срок",
        "сколько стоит",
        "консультац",
        "условия",
        "price",
        "cost",
        "timeline",
        "quote",
    )

    if any(keyword in text for keyword in hot_keywords):
        return "hot"

    if any(keyword in text for keyword in warm_keywords):
        return "warm"

    return "cold"