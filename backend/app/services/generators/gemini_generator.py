from typing import Optional
from app.services.generators.base_generator import BaseGenerator
from app.services.gemini_service import gemini_service


class GeminiGenerator(BaseGenerator):
    async def generate_content(self, prompt: str) -> Optional[str]:

        return await gemini_service.generate_content(prompt)
