from __future__ import annotations

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured. "
        "Add it to your .env file."
    )

client = genai.Client(
    api_key=GEMINI_API_KEY,
)


def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the response."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text