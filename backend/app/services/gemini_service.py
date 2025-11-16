import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import google.generativeai as genai
from app.config import get_settings

settings = get_settings()


class GeminiService:
    """
    Shared Gemini service with API key rotation.
    Provides generic content generation - prompts are defined by callers.
    """

    def __init__(self):
        # Parse comma-separated API keys
        self.api_keys = [key.strip() for key in settings.gemini_api_keys.split(",")]
        self.current_key_index = 0
        self.executor = ThreadPoolExecutor(max_workers=2)

    def _get_next_key(self) -> str:
        """Get next API key in round-robin fashion."""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    def _generate_content_sync(self, prompt: str) -> Optional[str]:
        """
        Synchronous method to generate content using Gemini.
        Runs in thread pool to avoid blocking.
        Returns None if generation fails (safety, copyright, etc.)
        """
        try:
            api_key = self._get_next_key()
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            response = model.generate_content(prompt)
            
            # Check if response has valid content
            if not response.candidates or len(response.candidates) == 0:
                print("Gemini: No candidates in response")
                return None
            
            # Check finish_reason: 1 = STOP (success), 3 = SAFETY, 4 = RECITATION (copyright)
            finish_reason = response.candidates[0].finish_reason
            if finish_reason != 1:
                print(f"Gemini: Blocked response (finish_reason={finish_reason})")
                return None
            
            return response.text.strip()
        except Exception as e:
            print(f"Gemini generation error: {e}")
            return None

    async def generate_content(self, prompt: str) -> Optional[str]:
        """
        Generate content from a prompt using Gemini.

        Args:
            prompt: The prompt to send to Gemini

        Returns:
            Generated content, or None if generation failed
        """
        return await asyncio.get_running_loop().run_in_executor(
            self.executor, self._generate_content_sync, prompt
        )

    async def generate_contents_batch(self, prompts: List[str]) -> List[Optional[str]]:
        """
        Generate content for multiple prompts concurrently.

        Args:
            prompts: List of prompts

        Returns:
            List of generated contents in same order (None if generation failed)
        """
        tasks = [self.generate_content(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)


# Global instance
gemini_service = GeminiService()
