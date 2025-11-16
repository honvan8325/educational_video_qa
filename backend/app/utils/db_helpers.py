"""
Helper functions for database operations
"""

from bson import ObjectId
from typing import Dict, Any, List


def convert_objectid_to_str(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB ObjectId to string in a document.

    Args:
        document: MongoDB document

    Returns:
        Document with _id converted to string
    """
    if document and "_id" in document:
        document["_id"] = str(document["_id"])
    return document


def convert_objectid_list_to_str(
    documents: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert MongoDB ObjectId to string in a list of documents.

    Args:
        documents: List of MongoDB documents

    Returns:
        List of documents with _id converted to string
    """
    return [convert_objectid_to_str(doc) for doc in documents]


def prepare_id_filter(id_value: str) -> ObjectId:
    """
    Prepare an ID for MongoDB filter by converting string to ObjectId.

    Args:
        id_value: String ID

    Returns:
        ObjectId for MongoDB query
    """
    return ObjectId(id_value)
