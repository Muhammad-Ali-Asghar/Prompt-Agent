"""
API routes for the RAG agent.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from config import get_settings
from schemas import GeneratePromptRequest, GeneratePromptResponse
from security import get_request_id
from vectorstore import ChromaVectorStore
from .chain import PromptGenerationChain

logger = logging.getLogger(__name__)
router = APIRouter()


def get_vector_store(request: Request) -> ChromaVectorStore:
    """Dependency to get vector store from app state."""
    return request.app.state.vector_store


def get_chain(
    vector_store: Annotated[ChromaVectorStore, Depends(get_vector_store)]
) -> PromptGenerationChain:
    """Dependency to get the prompt generation chain."""
    return PromptGenerationChain(vector_store)


@router.post("/generate-prompt", response_model=GeneratePromptResponse)
async def generate_prompt(
    request: GeneratePromptRequest,
    chain: Annotated[PromptGenerationChain, Depends(get_chain)]
):
    """
    Generate a high-quality prompt from the user's request.
    
    This endpoint:
    1. Validates and sanitizes the input
    2. Classifies the intent of the request
    3. Retrieves relevant prompt patterns, skill cards, and security guidelines
    4. Filters retrieved content for injection attempts
    5. Synthesizes a structured prompt
    6. Runs quality gates to ensure completeness
    7. Returns the prompt with citations and safety checks
    """
    try:
        response = await chain.generate(request)
        
        logger.info(
            f"Generated prompt: target={request.target_model.value}, "
            f"style={request.prompt_style.value}, "
            f"citations={len(response.citations)}"
        )
        
        return response
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prompt generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Prompt generation failed. Please try again."
        )
