from abc import ABC, abstractmethod
from typing import Optional


class BaseGenerator(ABC):

    @abstractmethod
    async def generate_content(self, prompt: str) -> Optional[str]:

        pass
