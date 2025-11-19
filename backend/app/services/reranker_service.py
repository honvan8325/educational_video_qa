from typing import List, Dict
import torch
from sentence_transformers import CrossEncoder
import time


class RerankerService:

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):

        self.model_name = model_name
        self.model = None
        self._device = self._get_device()

    def _get_device(self) -> str:

        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _load_model(self):
        if self.model is None:
            print(f"Loading reranker model: {self.model_name} on {self._device}")
            start_time = time.time()

            self.model = CrossEncoder(
                self.model_name,
                max_length=512,
                device=self._device,
            )

            load_time = time.time() - start_time
            print(f"Reranker model loaded in {load_time:.2f} seconds")

    def rerank(
        self,
        query: str,
        contexts: List[Dict],
        top_n: int = None,
    ) -> List[Dict]:

        if not contexts:
            return []

        # Lazy load model
        self._load_model()

        # Prepare (query, text) pairs for scoring
        pairs = [[query, ctx["text"]] for ctx in contexts]

        # Score with CrossEncoder
        print(f"Reranking {len(contexts)} contexts...")
        start_time = time.time()

        scores = self.model.predict(pairs)

        rerank_time = time.time() - start_time
        print(f"Reranking completed in {rerank_time:.2f} seconds")

        for i, ctx in enumerate(contexts):
            ctx["rerank_score"] = float(scores[i])
            ctx["distance"] = -float(scores[i])

        reranked_contexts = sorted(
            contexts, key=lambda x: x["rerank_score"], reverse=True
        )

        if top_n is not None:
            reranked_contexts = reranked_contexts[:top_n]

        print(f"Returned top {len(reranked_contexts)} contexts after reranking")
        return reranked_contexts


reranker_service = RerankerService()
