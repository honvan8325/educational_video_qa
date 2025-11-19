from typing import List, Dict, Optional
import asyncio
from app.services.retrievers.base_retriever import BaseRetriever
from app.services.retrievers.vector_retriever import VectorRetriever
from app.services.retrievers.bm25_retriever import BM25Retriever


class HybridRetriever(BaseRetriever):
    """
    Hybrid retriever combining vector (semantic) and BM25 (lexical) search
    using Weighted Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        k: int = 60,
        weight_vector: float = 1.0,
        weight_bm25: float = 1.0,
        embedding_model: str = "dangvantuan",
    ):
        self.vector_retriever = VectorRetriever(embedding_model)
        self.bm25_retriever = BM25Retriever()

        self.k = k
        self.weight_vector = weight_vector
        self.weight_bm25 = weight_bm25

    async def query_similar_contexts(
        self,
        workspace_id: str,
        query_text: str,
        n_results: int = 5,
        video_ids: Optional[List[str]] = None,
    ) -> List[Dict]:

        retrieval_count = max(n_results * 2, 10)

        vector_results, bm25_results = await asyncio.gather(
            self.vector_retriever.query_similar_contexts(
                workspace_id, query_text, retrieval_count, video_ids
            ),
            self.bm25_retriever.query_similar_contexts(
                workspace_id, query_text, retrieval_count, video_ids
            ),
        )

        if not vector_results and not bm25_results:
            return []
        if not vector_results:
            return bm25_results[:n_results]
        if not bm25_results:
            return vector_results[:n_results]

        vector_ranks = {r["id"]: i + 1 for i, r in enumerate(vector_results)}
        bm25_ranks = {r["id"]: i + 1 for i, r in enumerate(bm25_results)}

        all_results = {}
        for r in vector_results:
            all_results[r["id"]] = r
        for r in bm25_results:
            if r["id"] not in all_results:
                all_results[r["id"]] = r

        rrf_scores = {}
        all_ids = set(vector_ranks.keys()) | set(bm25_ranks.keys())

        for doc_id in all_ids:
            score = 0.0
            if doc_id in vector_ranks:
                score += self.weight_vector * (1.0 / (self.k + vector_ranks[doc_id]))
            if doc_id in bm25_ranks:
                score += self.weight_bm25 * (1.0 / (self.k + bm25_ranks[doc_id]))
            rrf_scores[doc_id] = score

        sorted_ids = sorted(
            rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True
        )
        top_ids = sorted_ids[:n_results]

        final_results = []
        for doc_id in top_ids:
            item = all_results[doc_id].copy()
            score = rrf_scores[doc_id]

            # Convert score to 0–1 distance
            item["distance"] = 1.0 / (1.0 + score * 10)

            final_results.append(item)

        return final_results
