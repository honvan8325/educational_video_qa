import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List, Dict, Optional
from app.config import get_settings
from app.models.context_unit import ContextUnit
import numpy as np
import shutil
from pathlib import Path

import torch

settings = get_settings()


class VectorStore:
    def __init__(self):
        self.persist_directory = settings.chroma_persist_dir

        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        self.text_embedding_model = HuggingFaceEmbeddings(
            model_name="dangvantuan/vietnamese-embedding",
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )

        self._chroma_instances = {}

    def get_or_create_collection(self, workspace_id: str):
        collection_name = f"workspace_{workspace_id}"

        if collection_name in self._chroma_instances:
            return self._chroma_instances[collection_name]

        workspace_persist_dir = str(Path(self.persist_directory) / collection_name)

        chroma_instance = Chroma(
            collection_name=collection_name,
            embedding_function=self.text_embedding_model,
            persist_directory=workspace_persist_dir,
        )

        self._chroma_instances[collection_name] = chroma_instance

        return chroma_instance

    def add_context_units(
        self,
        workspace_id: str,
        video_id: str,
        video_path: str,
        context_units: List[ContextUnit],
    ):
        chroma = self.get_or_create_collection(workspace_id)

        texts = []
        metadatas = []
        ids = []

        for context_unit in context_units:
            context_id = str(context_unit.id)
            text = context_unit.text

            texts.append(text)
            ids.append(context_id)

            metadatas.append(
                {
                    "id": context_id,  # Store ID in metadata for retrieval
                    "video_id": video_id,
                    "video_path": video_path,
                    "start_time": float(context_unit.start_time),
                    "end_time": float(context_unit.end_time),
                }
            )

        chroma.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    def query_similar_contexts(
        self, workspace_id: str, query_text: str, n_results: int = 5, video_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        chroma = self.get_or_create_collection(workspace_id)

        # Build filter for video_ids if provided
        filter_dict = None
        if video_ids is not None and len(video_ids) > 0:
            filter_dict = {"video_id": {"$in": video_ids}}

        results = chroma.similarity_search_with_relevance_scores(
            query=query_text, k=n_results, filter=filter_dict
        )

        retrieved_contexts = []
        for doc, score in results:
            retrieved_contexts.append(
                {
                    "id": doc.metadata.get("id", ""),
                    "text": doc.page_content,
                    "metadata": {
                        "video_id": doc.metadata.get("video_id", ""),
                        "video_path": doc.metadata.get("video_path", ""),
                        "start_time": doc.metadata.get("start_time", 0.0),
                        "end_time": doc.metadata.get("end_time", 0.0),
                    },
                    "distance": 1 - score,
                }
            )

        return retrieved_contexts

    def delete_context_units(self, workspace_id: str, context_ids: List[str]):
        chroma = self.get_or_create_collection(workspace_id)

        try:
            chroma.delete(ids=context_ids)
        except Exception as e:
            print(f"Error deleting context units: {e}")
            pass

    def delete_workspace_collection(self, workspace_id: str):
        collection_name = f"workspace_{workspace_id}"

        if collection_name in self._chroma_instances:
            del self._chroma_instances[collection_name]

        workspace_persist_dir = Path(self.persist_directory) / collection_name
        try:
            if workspace_persist_dir.exists():
                shutil.rmtree(workspace_persist_dir)
        except Exception as e:
            print(f"Error deleting workspace collection: {e}")
            pass


vector_store = VectorStore()
