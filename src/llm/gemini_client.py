import json
from typing import Type

from google import genai
from google.genai import types
from pydantic import BaseModel


class GeminiClient:
    def __init__(self, api_key: str, model: str, temperature: float = 0.7):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_message: str,
        response_schema: Type[BaseModel],
    ) -> BaseModel:
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=system_prompt,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=config,
        )

        raw_text = response.text
        if not raw_text:
            raise ValueError("Empty response text from Gemini")

        payload = json.loads(raw_text)
        return response_schema.model_validate(payload)
