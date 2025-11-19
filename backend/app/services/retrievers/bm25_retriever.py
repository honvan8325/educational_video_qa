from typing import List, Dict, Optional
import numpy as np
from rank_bm25 import BM25Okapi
from app.services.retrievers.base_retriever import BaseRetriever
from app.database import get_database


class BM25Retriever(BaseRetriever):
    async def query_similar_contexts(
        self,
        workspace_id: str,
        query_text: str,
        n_results: int = 5,
        video_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        db = await get_database()

        filter_dict = {}
        if video_ids and len(video_ids) > 0:
            filter_dict["video_id"] = {"$in": video_ids}

        contexts = await db.context_units.find(filter_dict).to_list(None)

        if not contexts:
            return []

        corpus = [ctx["text"].lower().split() for ctx in contexts]

        bm25 = BM25Okapi(corpus)

        tokenized_query = query_text.lower().split()
        scores = bm25.get_scores(tokenized_query)

        top_n = min(n_results, len(scores))
        top_indices = np.argsort(scores)[-top_n:][::-1]

        max_score = scores[top_indices[0]] if len(top_indices) > 0 else 1.0
        if max_score == 0:
            max_score = 1.0

        results = []
        for idx in top_indices:
            ctx = contexts[idx]
            normalized_score = scores[idx] / max_score
            results.append(
                {
                    "id": str(ctx["_id"]),
                    "text": ctx["text"],
                    "metadata": {
                        "video_id": ctx.get("video_id", ""),
                        "video_path": ctx.get("video_path", ""),
                        "start_time": ctx.get("start_time", 0.0),
                        "end_time": ctx.get("end_time", 0.0),
                    },
                    "distance": 1 - normalized_score,
                }
            )

        return results
