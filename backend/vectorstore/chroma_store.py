"""
ChromaDB implementation of the vector store interface.
"""

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import get_settings
from .base import VectorStoreInterface, DocumentChunk, SearchResult

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStoreInterface):
    """ChromaDB-based vector store implementation."""

    def __init__(
        self, persist_directory: str, collection_name: str = "prompt_rag_docs"
    ):
        """
        Initialize ChromaDB vector store.

        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        settings = get_settings()

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

        # Initialize embeddings using Google Generative AI
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model, google_api_key=settings.google_api_key
        )

        logger.info(
            f"ChromaDB initialized: collection={collection_name}, "
            f"docs={self.collection.count()}"
        )

    def _generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        return self.embeddings.embed_documents(texts)

    def _generate_query_embedding(self, query: str) -> list[float]:
        """Generate embedding for a query."""
        return self.embeddings.embed_query(query)

    def add_documents(self, chunks: list[DocumentChunk]) -> list[str]:
        """Add document chunks to ChromaDB."""
        if not chunks:
            return []

        # Prepare data for ChromaDB
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]

        # Sanitize metadata: remove None values as ChromaDB doesn't support them
        metadatas = []
        for chunk in chunks:
            clean_metadata = {k: v for k, v in chunk.metadata.items() if v is not None}
            metadatas.append(clean_metadata)

        # Generate embeddings
        embeddings = self._generate_embeddings(documents)

        # Add to collection
        self.collection.add(
            ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
        )

        logger.info(f"Added {len(chunks)} chunks to ChromaDB")
        return ids

    def search(
        self, query: str, top_k: int = 5, filter_metadata: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        """Search for similar documents in ChromaDB."""
        # Generate query embedding
        query_embedding = self._generate_query_embedding(query)

        # Build where clause for metadata filtering
        where = None
        if filter_metadata:
            if len(filter_metadata) == 1:
                key, value = next(iter(filter_metadata.items()))
                where = {key: value}
            else:
                where = {"$and": [{k: v} for k, v in filter_metadata.items()]}

        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to SearchResult objects
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB returns distances, convert to similarity scores
                # For cosine distance, similarity = 1 - distance
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1 - distance

                chunk = DocumentChunk(
                    id=doc_id,
                    content=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                )
                search_results.append(SearchResult(chunk=chunk, score=score))

        return search_results

    def delete(self, ids: list[str]) -> bool:
        """Delete documents by IDs."""
        if not ids:
            return True

        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} chunks from ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Failed to delete chunks: {e}")
            return False

    def delete_by_metadata(self, metadata_filter: dict[str, Any]) -> int:
        """Delete documents matching metadata filter."""
        if not metadata_filter:
            return 0

        # Build where clause
        if len(metadata_filter) == 1:
            key, value = next(iter(metadata_filter.items()))
            where = {key: value}
        else:
            where = {"$and": [{k: v} for k, v in metadata_filter.items()]}

        # Get matching IDs
        results = self.collection.get(where=where, include=[])

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} chunks matching filter")
            return len(results["ids"])

        return 0

    def list_documents(
        self, doc_type: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List unique documents (by doc_id) in the store."""
        where = {"doc_type": doc_type} if doc_type else None

        results = self.collection.get(where=where, limit=limit, include=["metadatas"])

        # Extract unique documents by doc_id
        seen_docs = {}
        for i, metadata in enumerate(results["metadatas"] or []):
            doc_id = metadata.get("doc_id", results["ids"][i])
            if doc_id not in seen_docs:
                seen_docs[doc_id] = {
                    "doc_id": doc_id,
                    "title": metadata.get("title", "Unknown"),
                    "doc_type": metadata.get("doc_type", "unknown"),
                    "version": metadata.get("version", "1.0"),
                    "created_at": metadata.get("created_at", ""),
                    "chunk_count": 1,
                }
            else:
                seen_docs[doc_id]["chunk_count"] += 1

        return list(seen_docs.values())

    def get_document_count(self) -> int:
        """Get total chunk count in the store."""
        return self.collection.count()

    def search_by_type(
        self, query: str, doc_type: str, top_k: int = 5, min_score: float = 0.0
    ) -> list[SearchResult]:
        """
        Search for documents of a specific type.

        Args:
            query: Search query
            doc_type: Document type filter (prompt_pattern, skill_card, security_guideline)
            top_k: Number of results
            min_score: Minimum similarity score threshold

        Returns:
            Filtered search results
        """
        results = self.search(
            query, top_k=top_k, filter_metadata={"doc_type": doc_type}
        )
        return [r for r in results if r.score >= min_score]
