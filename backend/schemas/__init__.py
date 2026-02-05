"""API schemas module for the Prompt RAG Agent."""

from .requests import (
    GeneratePromptRequest,
    IngestDocumentRequest,
    DeleteDocumentRequest,
    TargetModel,
    PromptStyle,
    OutputFormat
)
from .responses import (
    GeneratePromptResponse,
    Citation,
    SelectedSkill,
    SafetyCheck,
    DocumentInfo,
    IngestDocumentResponse,
    ListDocumentsResponse,
    DeleteDocumentResponse,
    HealthResponse,
    ErrorResponse
)

__all__ = [
    # Requests
    "GeneratePromptRequest",
    "IngestDocumentRequest",
    "DeleteDocumentRequest",
    "TargetModel",
    "PromptStyle",
    "OutputFormat",
    # Responses
    "GeneratePromptResponse",
    "Citation",
    "SelectedSkill",
    "SafetyCheck",
    "DocumentInfo",
    "IngestDocumentResponse",
    "ListDocumentsResponse",
    "DeleteDocumentResponse",
    "HealthResponse",
    "ErrorResponse"
]
