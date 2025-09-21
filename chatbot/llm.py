from config import client
from typing import List

def call_llm(system_prompt: str, context_blocks: List[str], user_question: str) -> str:
    if not client:
        return ("(OpenAI API key missing) I can’t call the model right now. "
                "Please set OPENAI_API_KEY in the Space settings.")
    joined_context = "\n\n---\n".join(context_blocks[:6])
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": "CONTEXT (trusted facts and retrieved data):\n" + joined_context},
        {"role": "user", "content": user_question},
    ]
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
            max_tokens=550,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I had an issue generating a response: {e}"
