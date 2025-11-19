import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from google import genai
from google.genai import types

from app.config import get_settings

settings = get_settings()


class GeminiService:
    def __init__(self):
        self.api_keys = [key.strip() for key in settings.gemini_api_keys.split(",")]
        if not self.api_keys:
            raise ValueError("No Gemini API keys configured")

        self.clients: List[genai.Client] = [
            genai.Client(api_key=key) for key in self.api_keys
        ]

        self.current_key_index = 0
        self._lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)

    def _get_current_client(self) -> genai.Client:
        with self._lock:
            return self.clients[self.current_key_index]

    def _rotate_client(self):
        with self._lock:
            self.current_key_index = (self.current_key_index + 1) % len(self.clients)

    @staticmethod
    def _is_quota_error(e: Exception) -> bool:
        msg = str(e).lower()
        if "429" in msg or "quota" in msg or "rate limit" in msg:
            return True
        status = getattr(e, "status", None)
        return status == 429

    @staticmethod
    def _is_auth_error(e: Exception) -> bool:
        msg = str(e).lower()
        if "401" in msg or "403" in msg:
            return True
        status = getattr(e, "status", None)
        return status in (401, 403)

    def _generate_content_sync(self, prompt: str) -> Optional[str]:
        max_retries = len(self.api_keys)
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            client = self._get_current_client()

            try:
                config = types.GenerateContentConfig(
                    temperature=0.2,
                    top_p=0.95,
                    # max_output_tokens=1024,
                    # thinking_config=types.ThinkingConfig(thinking_budget=0),
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=config,
                )

                return (response.text or "").strip()

            except Exception as e:
                last_error = e

                # if self._is_quota_error(e):
                #     print(
                #         f"⚠️  Quota/rate-limit on current API key "
                #         f"(attempt {attempt + 1}/{max_retries}), rotating key..."
                #     )
                #     self._rotate_client()
                #     continue

                # if self._is_auth_error(e):
                #     print(
                #         f"⚠️  Auth error (invalid/disabled key) "
                #         f"(attempt {attempt + 1}/{max_retries}), rotating key..."
                #     )
                #     self._rotate_client()
                #     continue

                # print(f"Gemini generation error (non-quota/auth): {e}")
                print(f"⚠️  Gemini generation error: {e}")
                print(f"(attempt {attempt + 1}/{max_retries}), rotating key...")
                self._rotate_client()
                continue

        print(f"❌ All API keys failed. Last error: {last_error}")
        return None

    async def generate_content(self, prompt: str) -> Optional[str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor, self._generate_content_sync, prompt
        )

    async def generate_contents_batch(self, prompts: List[str]) -> List[Optional[str]]:
        tasks = [self.generate_content(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)


gemini_service = GeminiService()
