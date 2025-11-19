from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseRetriever(ABC):
    @abstractmethod
    async def query_similar_contexts(
        self,
        workspace_id: str,
        query_text: str,
        n_results: int = 5,
        video_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        pass
