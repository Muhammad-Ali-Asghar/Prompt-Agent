"""
Document chunking utilities for the Prompt RAG Agent.
Handles splitting documents into chunks while preserving metadata.
"""

import re
import uuid
from typing import Generator
from datetime import datetime

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_settings
from vectorstore.base import DocumentChunk
from .schemas import DocumentMetadata


class DocumentChunker:
    """Handles chunking of documents for vector storage."""

    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None):
        """
        Initialize the document chunker.

        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        # Use different separators based on content type
        self.markdown_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n## ",  # H2 headers
                "\n### ",  # H3 headers
                "\n#### ",  # H4 headers
                "\n\n",  # Paragraphs
                "\n",  # Lines
                ". ",  # Sentences
                " ",  # Words
                "",  # Characters
            ],
            keep_separator=True,
        )

        self.yaml_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n---\n",  # YAML document separator
                "\n- id:",  # Skill card separator
                "\n\n",  # Paragraphs
                "\n",  # Lines
                " ",  # Words
                "",  # Characters
            ],
            keep_separator=True,
        )

    def chunk_document(
        self,
        content: str,
        title: str,
        doc_type: str,
        version: str = "1.0",
        doc_id: str | None = None,
    ) -> list[DocumentChunk]:
        """
        Split a document into chunks with metadata.

        Args:
            content: Document content
            title: Document title
            doc_type: Type of document (prompt_pattern, skill_card, security_guideline)
            version: Document version
            doc_id: Optional document ID (generated if not provided)

        Returns:
            List of document chunks with metadata
        """
        if not content.strip():
            return []

        # Generate document ID if not provided
        if not doc_id:
            doc_id = f"{doc_type}_{uuid.uuid4().hex[:8]}"

        # Choose splitter based on content type
        if self._is_yaml_content(content):
            splitter = self.yaml_splitter
        else:
            splitter = self.markdown_splitter

        # Split into chunks
        texts = splitter.split_text(content)

        # Create document chunks with metadata
        chunks = []
        created_at = datetime.utcnow().isoformat()

        for i, text in enumerate(texts):
            # Extract section name if possible
            section = self._extract_section_name(text)

            metadata = DocumentMetadata(
                doc_id=doc_id,
                title=title,
                doc_type=doc_type,
                version=version,
                created_at=created_at,
                chunk_index=i,
                total_chunks=len(texts),
                section=section,
            )

            chunk = DocumentChunk(
                id=f"{doc_id}_chunk_{i}", content=text, metadata=metadata.to_dict()
            )
            chunks.append(chunk)

        return chunks

    def chunk_skill_card(
        self, content: str, title: str, version: str = "1.0"
    ) -> list[DocumentChunk]:
        """
        Chunk a skill card document.
        Skill cards are typically kept as single chunks if small enough.

        Args:
            content: YAML content of the skill card
            title: Skill card title
            version: Version string

        Returns:
            List of document chunks
        """
        # For skill cards, try to keep them as single chunks
        if len(content) <= self.chunk_size * 1.5:
            doc_id = f"skill_card_{uuid.uuid4().hex[:8]}"
            metadata = DocumentMetadata(
                doc_id=doc_id,
                title=title,
                doc_type="skill_card",
                version=version,
                created_at=datetime.utcnow().isoformat(),
                chunk_index=0,
                total_chunks=1,
                section="full",
            )

            return [
                DocumentChunk(
                    id=f"{doc_id}_chunk_0", content=content, metadata=metadata.to_dict()
                )
            ]

        # If too large, chunk normally
        return self.chunk_document(
            content=content, title=title, doc_type="skill_card", version=version
        )

    def _is_yaml_content(self, content: str) -> bool:
        """Check if content appears to be YAML."""
        yaml_indicators = [
            content.strip().startswith("---"),
            content.strip().startswith("- id:"),
            ": |" in content,  # Multi-line strings
            bool(re.search(r"^\s*-\s+\w+:", content, re.MULTILINE)),
        ]
        return any(yaml_indicators)

    def _extract_section_name(self, text: str) -> str | None:
        """Extract section name from chunk text."""
        # Look for markdown headers
        header_match = re.search(r"^#{1,4}\s+(.+)$", text, re.MULTILINE)
        if header_match:
            return header_match.group(1).strip()

        # Look for YAML id field
        id_match = re.search(r"^-?\s*id:\s*(\S+)", text, re.MULTILINE)
        if id_match:
            return id_match.group(1).strip()

        # Look for name field
        name_match = re.search(r"^\s*name:\s*(.+)$", text, re.MULTILINE)
        if name_match:
            return name_match.group(1).strip()

        return None


def generate_doc_id(doc_type: str, title: str) -> str:
    """
    Generate a deterministic document ID based on type and title.

    Args:
        doc_type: Document type
        title: Document title

    Returns:
        Unique document ID
    """
    # Create a slug from the title
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:30]
    short_uuid = uuid.uuid4().hex[:6]
    return f"{doc_type}_{slug}_{short_uuid}"
