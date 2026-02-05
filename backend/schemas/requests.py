"""
API request schemas for the Prompt RAG Agent.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal
from enum import Enum


class TargetModel(str, Enum):
    """Supported target models for prompt generation."""
    GEMINI = "gemini"
    CLAUDE = "claude"
    GPT = "gpt"
    GENERIC = "generic"


class PromptStyle(str, Enum):
    """Prompt output styles."""
    CONCISE = "concise"
    DETAILED = "detailed"
    STEP_BY_STEP = "step_by_step"


class OutputFormat(str, Enum):
    """Output format options."""
    PLAIN = "plain"
    JSON = "json"


class GeneratePromptRequest(BaseModel):
    """Request schema for prompt generation endpoint."""
    
    user_request: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user's request describing what prompt they need"
    )
    
    target_model: TargetModel = Field(
        default=TargetModel.GENERIC,
        description="Target LLM for the generated prompt"
    )
    
    prompt_style: PromptStyle = Field(
        default=PromptStyle.DETAILED,
        description="Style of the generated prompt"
    )
    
    constraints: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Additional constraints for the prompt"
    )
    
    context: str | None = Field(
        default=None,
        max_length=50000,
        description="Optional project context or details"
    )
    
    output_format: OutputFormat = Field(
        default=OutputFormat.PLAIN,
        description="Format of the final prompt output"
    )
    
    @field_validator('user_request')
    @classmethod
    def validate_user_request(cls, v: str) -> str:
        """Ensure user request is not just whitespace."""
        if not v.strip():
            raise ValueError("User request cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator('constraints')
    @classmethod
    def validate_constraints(cls, v: list[str]) -> list[str]:
        """Clean and validate constraints."""
        return [c.strip() for c in v if c.strip()]


class IngestDocumentRequest(BaseModel):
    """Request schema for document ingestion."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Document title"
    )
    
    doc_type: Literal["prompt_pattern", "skill_card", "security_guideline"] = Field(
        ...,
        description="Type of document being ingested"
    )
    
    content: str = Field(
        ...,
        min_length=1,
        description="Document content (Markdown or YAML)"
    )
    
    version: str = Field(
        default="1.0",
        description="Document version"
    )


class DeleteDocumentRequest(BaseModel):
    """Request schema for document deletion."""
    
    doc_id: str = Field(
        ...,
        min_length=1,
        description="Document ID to delete"
    )
