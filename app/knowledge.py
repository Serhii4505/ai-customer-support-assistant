import json
from pathlib import Path

FAQ_PATH = (
    Path(__file__).resolve().parent.parent
    / "knowledge"
    / "faq.json"
)


def find_faq_answer(message: str) -> str | None:
    with FAQ_PATH.open(encoding="utf-8-sig") as file:
        knowledge = json.load(file)

    text = message.casefold()

    for item in knowledge["faq"]:
        for keyword in item["keywords"]:
            if keyword.casefold() in text:
                return item["answer"]

    return None