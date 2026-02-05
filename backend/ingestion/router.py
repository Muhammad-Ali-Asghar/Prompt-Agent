"""
Admin API routes for document ingestion.
"""

import logging
from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse

from config import get_settings
from schemas import (
    IngestDocumentRequest,
    IngestDocumentResponse,
    ListDocumentsResponse,
    DeleteDocumentResponse,
    DocumentInfo
)
from security import validate_user_request, detect_injection, sanitize_text
from vectorstore import ChromaVectorStore
from .chunker import DocumentChunker, generate_doc_id

logger = logging.getLogger(__name__)
router = APIRouter()


def get_vector_store(request: Request) -> ChromaVectorStore:
    """Dependency to get vector store from app state."""
    return request.app.state.vector_store


@router.post("/ingest", response_model=IngestDocumentResponse)
async def ingest_document(
    request_data: IngestDocumentRequest,
    vector_store: Annotated[ChromaVectorStore, Depends(get_vector_store)]
):
    """
    Ingest a document into the knowledge base.
    
    Accepts Markdown or YAML content for:
    - prompt_pattern: Prompt templates and examples
    - skill_card: Reusable instruction modules
    - security_guideline: Secure coding guidelines
    """
    try:
        # Validate content
        validation = validate_user_request(request_data.content)
        if not validation.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid content: {', '.join(validation.errors)}"
            )
        
        # Check for injection attempts in content (warn but don't block)
        injection_check = detect_injection(request_data.content)
        if injection_check.is_injection:
            logger.warning(
                f"Potential injection in ingested doc '{request_data.title}': "
                f"{injection_check.reason}"
            )
        
        # Generate document ID
        doc_id = generate_doc_id(request_data.doc_type, request_data.title)
        
        # Chunk the document
        chunker = DocumentChunker()
        chunks = chunker.chunk_document(
            content=validation.sanitized_text,
            title=request_data.title,
            doc_type=request_data.doc_type,
            version=request_data.version,
            doc_id=doc_id
        )
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Document produced no valid chunks"
            )
        
        # Add to vector store
        chunk_ids = vector_store.add_documents(chunks)
        
        logger.info(
            f"Ingested document: id={doc_id}, title={request_data.title}, "
            f"type={request_data.doc_type}, chunks={len(chunk_ids)}"
        )
        
        return IngestDocumentResponse(
            success=True,
            doc_id=doc_id,
            chunk_count=len(chunk_ids),
            message=f"Successfully ingested '{request_data.title}' with {len(chunk_ids)} chunks"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.post("/ingest/file", response_model=IngestDocumentResponse)
async def ingest_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form(...),
    version: str = Form("1.0"),
    vector_store: ChromaVectorStore = Depends(get_vector_store)
):
    """
    Ingest a document from an uploaded file.
    Supports .md, .txt, .yaml, .yml files.
    """
    # Validate file type
    allowed_extensions = {'.md', '.txt', '.yaml', '.yml'}
    file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate doc_type
    valid_types = {'prompt_pattern', 'skill_card', 'security_guideline'}
    if doc_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid doc_type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Read file content
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded text"
        )
    
    # Use the JSON ingestion endpoint logic
    request_data = IngestDocumentRequest(
        title=title,
        doc_type=doc_type,
        content=content_str,
        version=version
    )
    
    return await ingest_document(request_data, vector_store)


@router.get("/documents", response_model=ListDocumentsResponse)
async def list_documents(
    doc_type: str | None = None,
    limit: int = 100,
    vector_store: ChromaVectorStore = Depends(get_vector_store)
):
    """
    List all documents in the knowledge base.
    Optionally filter by document type.
    """
    try:
        docs = vector_store.list_documents(doc_type=doc_type, limit=limit)
        
        documents = [
            DocumentInfo(
                doc_id=doc["doc_id"],
                title=doc["title"],
                doc_type=doc["doc_type"],
                version=doc["version"],
                created_at=doc["created_at"],
                chunk_count=doc["chunk_count"],
                embedded=True
            )
            for doc in docs
        ]
        
        return ListDocumentsResponse(
            documents=documents,
            total_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/documents/{doc_id}", response_model=DeleteDocumentResponse)
async def delete_document(
    doc_id: str,
    vector_store: ChromaVectorStore = Depends(get_vector_store)
):
    """
    Delete a document and all its chunks from the knowledge base.
    """
    try:
        deleted_count = vector_store.delete_by_metadata({"doc_id": doc_id})
        
        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_id}"
            )
        
        logger.info(f"Deleted document: id={doc_id}, chunks={deleted_count}")
        
        return DeleteDocumentResponse(
            success=True,
            deleted_chunks=deleted_count,
            message=f"Successfully deleted document '{doc_id}' ({deleted_count} chunks)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/reembed/{doc_id}")
async def reembed_document(
    doc_id: str,
    vector_store: ChromaVectorStore = Depends(get_vector_store)
):
    """
    Re-embed an existing document.
    Useful when embedding model changes.
    """
    # This would require storing original content separately
    # For now, return not implemented
    raise HTTPException(
        status_code=501,
        detail="Re-embedding requires document storage. Upload the document again."
    )


@router.get("/stats")
async def get_stats(
    vector_store: ChromaVectorStore = Depends(get_vector_store)
):
    """Get statistics about the knowledge base."""
    try:
        total_chunks = vector_store.get_document_count()
        docs = vector_store.list_documents(limit=1000)
        
        # Count by type
        type_counts = {}
        for doc in docs:
            doc_type = doc.get("doc_type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        return {
            "total_documents": len(docs),
            "total_chunks": total_chunks,
            "by_type": type_counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
