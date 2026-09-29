"""Embedding retrieval over the curated knowledge base, backed by Chroma Cloud."""

import os

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

from src.kb.snippets import SNIPPETS
from src.models import RetrievedSnippet

load_dotenv()

_COLLECTION_NAME = "medical_kb"

# Chroma's built-in ONNX-runtime embedder (all-MiniLM-L6-v2 under the hood).
# Used instead of sentence-transformers/torch to avoid that dependency chain.
_embedding_fn = embedding_functions.DefaultEmbeddingFunction()

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("CHROMA_API_KEY")
        tenant = os.environ.get("CHROMA_TENANT")
        database = os.environ.get("CHROMA_DATABASE")
        if not (api_key and tenant and database):
            raise RuntimeError(
                "CHROMA_API_KEY, CHROMA_TENANT, and CHROMA_DATABASE must be set. "
                "Copy .env.example to .env and fill them in from your Chroma "
                "Cloud dashboard (https://trychroma.com)."
            )
        _client = chromadb.CloudClient(api_key=api_key, tenant=tenant, database=database)
    return _client


def _get_collection():
    client = _get_client()
    collection = client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=_embedding_fn,
    )
    if collection.count() != len(SNIPPETS):
        # Rebuild from scratch if the KB has changed size since last run.
        client.delete_collection(_COLLECTION_NAME)
        collection = client.create_collection(
            name=_COLLECTION_NAME,
            embedding_function=_embedding_fn,
        )
        collection.add(
            ids=[s["id"] for s in SNIPPETS],
            documents=[s["text"] for s in SNIPPETS],
            metadatas=[{"category": s["category"], "title": s["title"]} for s in SNIPPETS],
        )
    return collection


def search(query: str, k: int = 4, category: str | None = None) -> list[RetrievedSnippet]:
    collection = _get_collection()
    query_kwargs = {"query_texts": [query], "n_results": k}
    if category:
        query_kwargs["where"] = {"category": category}
    results = collection.query(**query_kwargs)

    snippets: list[RetrievedSnippet] = []
    for doc_id, doc_text, metadata, distance in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        snippets.append(
            RetrievedSnippet(
                id=doc_id,
                category=metadata["category"],
                title=metadata["title"],
                text=doc_text,
                distance=distance,
            )
        )
    return snippets
