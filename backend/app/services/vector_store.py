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

        # Initialize both embedding models
        self.embedding_models = {
            "dangvantuan": HuggingFaceEmbeddings(
                model_name="dangvantuan/vietnamese-embedding",
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": True},
            ),
            "halong": HuggingFaceEmbeddings(
                model_name="hiieu/halong_embedding",
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": True},
            ),
        }

        self._chroma_instances = {}

    def get_or_create_collection(
        self, workspace_id: str, embedding_model: str = "dangvantuan"
    ):

        if embedding_model not in self.embedding_models:
            raise ValueError(
                f"Unknown embedding model: {embedding_model}. Supported: {list(self.embedding_models.keys())}"
            )

        collection_name = f"workspace_{workspace_id}_{embedding_model}"

        if collection_name in self._chroma_instances:
            return self._chroma_instances[collection_name]

        workspace_persist_dir = str(Path(self.persist_directory) / collection_name)

        chroma_instance = Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding_models[embedding_model],
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

        # Save to BOTH embedding models
        for embedding_model in self.embedding_models.keys():
            chroma = self.get_or_create_collection(workspace_id, embedding_model)
            chroma.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    def query_similar_contexts(
        self,
        workspace_id: str,
        query_text: str,
        n_results: int = 5,
        video_ids: Optional[List[str]] = None,
        embedding_model: str = "dangvantuan",
    ) -> List[Dict]:
        print(f"Querying vector store with embedding model: {embedding_model}")

        chroma = self.get_or_create_collection(workspace_id, embedding_model)

        filter_dict = None
        if video_ids is not None and len(video_ids) > 0:
            filter_dict = {"video_id": {"$in": video_ids}}

        results = chroma.similarity_search_with_relevance_scores(
            query=query_text, k=n_results, filter=filter_dict
        )
        print(f"Retrieved {len(results)} contexts from vector store.")

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

    def delete_context_units(
        self,
        workspace_id: str,
        context_ids: List[str],
        embedding_model: Optional[str] = None,
    ):
        """Delete context units from vector store.

        Args:
            workspace_id: Workspace ID
            context_ids: List of context IDs to delete
            embedding_model: Specific model to delete from. If None, deletes from ALL models.
        """
        if embedding_model:
            # Delete from specific model only
            try:
                chroma = self.get_or_create_collection(workspace_id, embedding_model)
                chroma.delete(ids=context_ids)
            except Exception as e:
                print(f"Error deleting context units from {embedding_model}: {e}")
        else:
            # Delete from ALL embedding models
            for model in self.embedding_models.keys():
                try:
                    chroma = self.get_or_create_collection(workspace_id, model)
                    chroma.delete(ids=context_ids)
                except Exception as e:
                    print(f"Error deleting context units from {model}: {e}")

    def clone_workspace_collection(
        self,
        source_workspace_id: str,
        target_workspace_id: str,
        context_id_mapping: Dict[str, str],  # old_context_id -> new_context_id
        video_id_mapping: Dict[str, str],  # old_video_id -> new_video_id
    ):

        for model in self.embedding_models.keys():
            try:
                source_chroma = self.get_or_create_collection(
                    source_workspace_id, model
                )
                target_chroma = self.get_or_create_collection(
                    target_workspace_id, model
                )

                # Get all data including pre-computed embeddings from source
                old_ids = list(context_id_mapping.keys())
                if not old_ids:
                    continue

                source_data = source_chroma.get(
                    ids=old_ids, include=["embeddings", "documents", "metadatas"]
                )

                if not source_data["ids"]:
                    print(f"No data found in source collection for {model}")
                    continue

                # Build new IDs and updated metadatas
                new_ids = []
                new_metadatas = []

                for i, old_id in enumerate(source_data["ids"]):
                    new_id = context_id_mapping[old_id]
                    new_ids.append(new_id)

                    # Update metadata with new IDs
                    old_metadata = source_data["metadatas"][i]
                    new_metadata = old_metadata.copy()
                    new_metadata["id"] = new_id
                    new_metadata["video_id"] = video_id_mapping.get(
                        old_metadata["video_id"], old_metadata["video_id"]
                    )
                    new_metadatas.append(new_metadata)

                # Add to target with pre-computed embeddings (no re-embedding!)
                target_chroma.add(
                    ids=new_ids,
                    embeddings=source_data["embeddings"],
                    documents=source_data["documents"],
                    metadatas=new_metadatas,
                )

                print(
                    f"✅ Fast cloned {len(new_ids)} embeddings to {model} collection (no re-embedding)"
                )
            except Exception as e:
                print(f"Error fast cloning workspace collection for {model}: {e}")

    def delete_workspace_collection(self, workspace_id: str):
        """Delete all collections for a workspace (all embedding models)."""
        for model in self.embedding_models.keys():
            collection_name = f"workspace_{workspace_id}_{model}"

            if collection_name in self._chroma_instances:
                del self._chroma_instances[collection_name]

            workspace_persist_dir = Path(self.persist_directory) / collection_name
            try:
                if workspace_persist_dir.exists():
                    shutil.rmtree(workspace_persist_dir)
            except Exception as e:
                print(f"Error deleting workspace collection {collection_name}: {e}")


vector_store = VectorStore()
