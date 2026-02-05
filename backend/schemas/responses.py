"""
API response schemas for the Prompt RAG Agent.
"""

from pydantic import BaseModel, Field
from typing import Any


class Citation(BaseModel):
    """Citation for a retrieved document used in prompt generation."""
    
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    section: str | None = Field(None, description="Specific section referenced")
    reason_used: str = Field(..., description="Why this document was included")


class SelectedSkill(BaseModel):
    """A skill card selected for inclusion in the prompt."""
    
    id: str = Field(..., description="Skill identifier")
    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Brief skill description")
    when_to_use: str = Field(..., description="When to apply this skill")
    relevance_score: float = Field(..., description="Relevance to the request")


class SafetyCheck(BaseModel):
    """A safety check performed on the generated prompt."""
    
    check_name: str = Field(..., description="Name of the safety check")
    passed: bool = Field(..., description="Whether the check passed")
    details: str | None = Field(None, description="Additional details")


class GeneratePromptResponse(BaseModel):
    """Response schema for prompt generation endpoint."""
    
    final_prompt: str | dict[str, Any] = Field(
        ...,
        description="The generated prompt (string or structured JSON)"
    )
    
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions made during generation"
    )
    
    safety_checks: list[SafetyCheck] = Field(
        default_factory=list,
        description="Safety checks performed"
    )
    
    citations: list[Citation] = Field(
        default_factory=list,
        description="Documents referenced in generation"
    )
    
    selected_skills: list[SelectedSkill] = Field(
        default_factory=list,
        description="Skill cards included in the prompt"
    )
    
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the generation"
    )


class DocumentInfo(BaseModel):
    """Information about an ingested document."""
    
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    doc_type: str = Field(..., description="Type of document")
    version: str = Field(..., description="Document version")
    created_at: str = Field(..., description="Creation timestamp")
    chunk_count: int = Field(..., description="Number of chunks")
    embedded: bool = Field(default=True, description="Whether embedded in vector store")


class IngestDocumentResponse(BaseModel):
    """Response schema for document ingestion."""
    
    success: bool = Field(..., description="Whether ingestion succeeded")
    doc_id: str = Field(..., description="Assigned document ID")
    chunk_count: int = Field(..., description="Number of chunks created")
    message: str = Field(..., description="Status message")


class ListDocumentsResponse(BaseModel):
    """Response schema for listing documents."""
    
    documents: list[DocumentInfo] = Field(
        default_factory=list,
        description="List of documents"
    )
    total_count: int = Field(..., description="Total document count")


class DeleteDocumentResponse(BaseModel):
    """Response schema for document deletion."""
    
    success: bool = Field(..., description="Whether deletion succeeded")
    deleted_chunks: int = Field(..., description="Number of chunks deleted")
    message: str = Field(..., description="Status message")


class HealthResponse(BaseModel):
    """Response schema for health endpoint."""
    
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Application version")
    vector_store: str = Field(..., description="Vector store connection status")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    request_id: str | None = Field(None, description="Request ID for tracing")
