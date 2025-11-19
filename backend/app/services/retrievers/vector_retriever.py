from typing import List, Dict, Optional
from app.services.retrievers.base_retriever import BaseRetriever
from app.services.vector_store import vector_store


class VectorRetriever(BaseRetriever):
    def __init__(self, embedding_model: str = "dangvantuan"):
        self.embedding_model = embedding_model

    async def query_similar_contexts(
        self,
        workspace_id: str,
        query_text: str,
        n_results: int = 5,
        video_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        return vector_store.query_similar_contexts(
            workspace_id, query_text, n_results, video_ids, self.embedding_model
        )
