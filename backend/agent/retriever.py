"""
Multi-source retriever for the RAG pipeline.
Fetches relevant documents from different knowledge base categories.
"""

import logging
from typing import NamedTuple
from dataclasses import dataclass

from config import get_settings
from vectorstore import ChromaVectorStore, SearchResult
from security import (
    detect_injection, 
    sanitize_for_context, 
    get_injection_severity_score,
    InjectionSeverity
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    """A document retrieved from the knowledge base."""
    doc_id: str
    title: str
    content: str
    doc_type: str
    section: str | None
    relevance_score: float
    is_safe: bool
    injection_warning: str | None = None


class RetrievalResult(NamedTuple):
    """Result of multi-source retrieval."""
    prompt_patterns: list[RetrievedDocument]
    skill_cards: list[RetrievedDocument]
    security_guidelines: list[RetrievedDocument]
    filtered_count: int
    warnings: list[str]


class MultiSourceRetriever:
    """
    Retrieves relevant documents from multiple knowledge base categories.
    Includes injection detection and filtering.
    """
    
    def __init__(self, vector_store: ChromaVectorStore):
        """
        Initialize the retriever.
        
        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store
        self.settings = get_settings()
    
    def retrieve(
        self,
        query: str,
        patterns_k: int = 5,
        skills_k: int = 5,
        guidelines_k: int = 5,
        min_score: float | None = None
    ) -> RetrievalResult:
        """
        Retrieve relevant documents from all knowledge base categories.
        
        Args:
            query: Search query (typically the user request)
            patterns_k: Number of prompt patterns to retrieve
            skills_k: Number of skill cards to retrieve
            guidelines_k: Number of security guidelines to retrieve
            min_score: Minimum relevance score threshold
        
        Returns:
            RetrievalResult with categorized documents
        """
        if min_score is None:
            min_score = self.settings.retrieval_min_score
        
        warnings = []
        filtered_count = 0
        
        # Retrieve from each category
        patterns_raw = self._retrieve_by_type(query, "prompt_pattern", patterns_k, min_score)
        skills_raw = self._retrieve_by_type(query, "skill_card", skills_k, min_score)
        guidelines_raw = self._retrieve_by_type(query, "security_guideline", guidelines_k, min_score)
        
        # Process and filter each category
        patterns, p_filtered, p_warnings = self._process_results(patterns_raw)
        skills, s_filtered, s_warnings = self._process_results(skills_raw)
        guidelines, g_filtered, g_warnings = self._process_results(guidelines_raw)
        
        filtered_count = p_filtered + s_filtered + g_filtered
        warnings.extend(p_warnings)
        warnings.extend(s_warnings)
        warnings.extend(g_warnings)
        
        if filtered_count > 0:
            logger.warning(f"Filtered {filtered_count} documents due to injection attempts")
        
        return RetrievalResult(
            prompt_patterns=patterns,
            skill_cards=skills,
            security_guidelines=guidelines,
            filtered_count=filtered_count,
            warnings=warnings
        )
    
    def _retrieve_by_type(
        self,
        query: str,
        doc_type: str,
        top_k: int,
        min_score: float
    ) -> list[SearchResult]:
        """Retrieve documents of a specific type."""
        try:
            results = self.vector_store.search_by_type(
                query=query,
                doc_type=doc_type,
                top_k=top_k,
                min_score=min_score
            )
            return results
        except Exception as e:
            logger.error(f"Retrieval failed for {doc_type}: {e}")
            return []
    
    def _process_results(
        self,
        results: list[SearchResult]
    ) -> tuple[list[RetrievedDocument], int, list[str]]:
        """
        Process search results and filter for injection attempts.
        
        Returns:
            Tuple of (processed documents, filtered count, warnings)
        """
        processed = []
        filtered_count = 0
        warnings = []
        
        for result in results:
            chunk = result.chunk
            metadata = chunk.metadata
            
            # Check for injection attempts
            injection = detect_injection(chunk.content)
            
            if injection.is_injection:
                if injection.severity in (InjectionSeverity.CRITICAL, InjectionSeverity.HIGH):
                    # Filter out dangerous content entirely
                    filtered_count += 1
                    warnings.append(
                        f"Filtered document '{metadata.get('title', 'unknown')}': "
                        f"{injection.reason}"
                    )
                    continue
                else:
                    # Sanitize but include with warning
                    sanitized_content = sanitize_for_context(chunk.content)
                    processed.append(RetrievedDocument(
                        doc_id=metadata.get("doc_id", chunk.id),
                        title=metadata.get("title", "Unknown"),
                        content=sanitized_content,
                        doc_type=metadata.get("doc_type", "unknown"),
                        section=metadata.get("section"),
                        relevance_score=result.score,
                        is_safe=False,
                        injection_warning=injection.reason
                    ))
            else:
                # Safe content
                processed.append(RetrievedDocument(
                    doc_id=metadata.get("doc_id", chunk.id),
                    title=metadata.get("title", "Unknown"),
                    content=chunk.content,
                    doc_type=metadata.get("doc_type", "unknown"),
                    section=metadata.get("section"),
                    relevance_score=result.score,
                    is_safe=True
                ))
        
        return processed, filtered_count, warnings
    
    def retrieve_for_intent(
        self,
        query: str,
        intent: str,
        is_coding_request: bool = False
    ) -> RetrievalResult:
        """
        Retrieve documents based on classified intent.
        Adjusts retrieval counts based on the type of request.
        
        Args:
            query: User query
            intent: Classified intent
            is_coding_request: Whether this is a coding-related request
        
        Returns:
            RetrievalResult tailored to the intent
        """
        # Default retrieval counts
        patterns_k = 5
        skills_k = 5
        guidelines_k = 3
        
        # Adjust based on intent and coding flag
        if is_coding_request:
            # More security guidelines for coding requests
            guidelines_k = 6
            skills_k = 4
        
        if "security" in intent.lower() or "secure" in intent.lower():
            guidelines_k = 8
            skills_k = 3
        
        if "template" in intent.lower() or "pattern" in intent.lower():
            patterns_k = 8
            skills_k = 3
        
        return self.retrieve(
            query=query,
            patterns_k=patterns_k,
            skills_k=skills_k,
            guidelines_k=guidelines_k
        )
