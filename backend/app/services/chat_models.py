from __future__ import annotations

from openai import OpenAI


def complete_chat(
    *,
    system: str,
    user: str,
    api_key: str,
    base_url: str | None,
    model: str,
) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url or None)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    choice = resp.choices[0].message
    return (choice.content or "").strip()
