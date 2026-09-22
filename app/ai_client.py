import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def ai_is_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def generate_ai_reply(
    message: str,
    history: list[dict] | None = None,
) -> str | None:
    try:
        input_messages = [
            {
                "role": "system",
                "content": (
                    "Ты AI Customer Support / Sales Assistant. "
                    "Отвечай кратко, понятно и профессионально. "
                    "Учитывай предыдущую историю разговора. "
                    "Не выдумывай факты о компании. "
                    "Если информации недостаточно, скажи, что вопрос "
                    "нужно уточнить у менеджера."
                ),
            }
        ]

        if history:
            for item in history[-10:]:
                role = item.get("role")
                text = item.get("message")

                if role in ("user", "assistant") and text:
                    input_messages.append(
                        {
                            "role": role,
                            "content": text,
                        }
                    )

        input_messages.append(
            {
                "role": "user",
                "content": message,
            }
        )

        response = client.responses.create(
            model="gpt-5-mini",
            input=input_messages,
        )

        return response.output_text

    except Exception:
        return None