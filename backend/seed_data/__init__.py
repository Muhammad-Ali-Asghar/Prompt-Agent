"""
Seed data loader for the Prompt RAG Agent.
Loads initial skill cards, prompt patterns, and security guidelines.
"""

import os
import logging
from pathlib import Path

import yaml

from ingestion.chunker import DocumentChunker
from vectorstore import ChromaVectorStore

logger = logging.getLogger(__name__)

SEED_DATA_DIR = Path(__file__).parent


def load_seed_data(vector_store: ChromaVectorStore) -> dict:
    """
    Load all seed data into the vector store.

    Args:
        vector_store: Vector store instance

    Returns:
        Summary of loaded documents
    """
    chunker = DocumentChunker()
    summary = {"skills": 0, "patterns": 0, "guidelines": 0, "total_chunks": 0}

    # Load skill cards
    skills_dir = SEED_DATA_DIR / "skills"
    if skills_dir.exists():
        for skills_file in skills_dir.glob("*.yaml"):
            count, chunks = _load_skill_cards(skills_file, chunker, vector_store)
            summary["skills"] += count
            summary["total_chunks"] += chunks

    # Load prompt patterns
    patterns_dir = SEED_DATA_DIR / "patterns"
    if patterns_dir.exists():
        for pattern_file in patterns_dir.glob("*.md"):
            count, chunks = _load_markdown_doc(
                pattern_file, "prompt_pattern", chunker, vector_store
            )
            summary["patterns"] += count
            summary["total_chunks"] += chunks

    # Load security guidelines
    guidelines_dir = SEED_DATA_DIR / "guidelines"
    if guidelines_dir.exists():
        for guideline_file in guidelines_dir.glob("*.md"):
            count, chunks = _load_markdown_doc(
                guideline_file, "security_guideline", chunker, vector_store
            )
            summary["guidelines"] += count
            summary["total_chunks"] += chunks

    logger.info(
        f"Loaded seed data: {summary['skills']} skills, "
        f"{summary['patterns']} patterns, {summary['guidelines']} guidelines, "
        f"{summary['total_chunks']} total chunks"
    )

    return summary


def _load_skill_cards(
    file_path: Path, chunker: DocumentChunker, vector_store: ChromaVectorStore
) -> tuple[int, int]:
    """Load skill cards from YAML file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Parse YAML to get individual skills
        skills = yaml.safe_load(content)

        if not skills:
            return 0, 0

        total_chunks = 0
        for skill in skills:
            # Convert skill back to YAML for storage
            skill_content = yaml.dump(skill, default_flow_style=False)
            skill_name = skill.get("name", skill.get("id", "Unknown Skill"))

            chunks = chunker.chunk_skill_card(
                content=skill_content, title=skill_name, version="1.0"
            )

            if chunks:
                vector_store.add_documents(chunks)
                total_chunks += len(chunks)

        logger.info(f"Loaded {len(skills)} skill cards from {file_path.name}")
        return len(skills), total_chunks

    except Exception as e:
        logger.error(f"Failed to load skill cards from {file_path}: {e}")
        return 0, 0


def _load_markdown_doc(
    file_path: Path,
    doc_type: str,
    chunker: DocumentChunker,
    vector_store: ChromaVectorStore,
) -> tuple[int, int]:
    """Load a markdown document."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Extract title from first heading or filename
        title = file_path.stem.replace("_", " ").title()
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        chunks = chunker.chunk_document(
            content=content, title=title, doc_type=doc_type, version="1.0"
        )

        if chunks:
            vector_store.add_documents(chunks)
            logger.info(f"Loaded {doc_type}: {title} ({len(chunks)} chunks)")
            return 1, len(chunks)

        return 0, 0

    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return 0, 0


if __name__ == "__main__":
    # Allow running directly to seed the database
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))

    from config import get_settings

    settings = get_settings()
    vector_store = ChromaVectorStore(
        persist_directory=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
    )

    summary = load_seed_data(vector_store)
    print(f"Seed data loaded: {summary}")
