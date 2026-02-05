"""
Abstract base class for vector store implementations.
Allows swapping between ChromaDB, Pinecone, Weaviate, etc.
"""

from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    id: str
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None


@dataclass
class SearchResult:
    """Result from a vector similarity search."""
    chunk: DocumentChunk
    score: float
    

class VectorStoreInterface(ABC):
    """Abstract interface for vector store implementations."""
    
    @abstractmethod
    def add_documents(self, chunks: list[DocumentChunk]) -> list[str]:
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of document chunks with content and metadata
        
        Returns:
            List of IDs for the added chunks
        """
        pass
    
    @abstractmethod
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            List of search results with scores
        """
        pass
    
    @abstractmethod
    def delete(self, ids: list[str]) -> bool:
        """
        Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
        
        Returns:
            True if deletion was successful
        """
        pass
    
    @abstractmethod
    def delete_by_metadata(self, metadata_filter: dict[str, Any]) -> int:
        """
        Delete documents matching metadata filter.
        
        Args:
            metadata_filter: Metadata conditions for deletion
        
        Returns:
            Number of documents deleted
        """
        pass
    
    @abstractmethod
    def list_documents(
        self, 
        doc_type: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        List documents in the store.
        
        Args:
            doc_type: Optional filter by document type
            limit: Maximum number of results
        
        Returns:
            List of document metadata
        """
        pass
    
    @abstractmethod
    def get_document_count(self) -> int:
        """
        Get total number of documents in the store.
        
        Returns:
            Document count
        """
        pass
