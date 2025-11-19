from app.services.retrievers.base_retriever import BaseRetriever
from app.services.retrievers.vector_retriever import VectorRetriever
from app.services.retrievers.bm25_retriever import BM25Retriever
from app.services.retrievers.hybrid_retriever import HybridRetriever


def get_retriever(
    retriever_type: str = "vector", embedding_model: str = "dangvantuan"
) -> BaseRetriever:
    print(f"Initializing retriever of type: {retriever_type}")
    if retriever_type == "vector":
        return VectorRetriever(embedding_model)
    elif retriever_type == "bm25":
        return BM25Retriever()
    elif retriever_type == "hybrid":
        return HybridRetriever(embedding_model=embedding_model)
    else:
        raise ValueError(
            f"Unknown retriever type: {retriever_type}. "
            f"Supported types: 'vector', 'bm25', 'hybrid'"
        )


__all__ = [
    "BaseRetriever",
    "VectorRetriever",
    "BM25Retriever",
    "HybridRetriever",
    "get_retriever",
]
