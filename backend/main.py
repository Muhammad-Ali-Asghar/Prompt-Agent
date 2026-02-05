"""
Prompt RAG Agent - FastAPI Application Entry Point

A production-ready RAG system that generates high-quality prompts
by retrieving Prompt Patterns, Skill Cards, and Secure Coding Guidelines.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import get_settings
from security.middleware import RequestIdMiddleware, SafeLoggingMiddleware
from agent.router import router as agent_router
from ingestion.router import router as ingestion_router
from vectorstore.chroma_store import ChromaVectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Global vector store instance
vector_store: ChromaVectorStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global vector_store
    settings = get_settings()

    # Force logging configuration (Uvicorn overrides basicConfig)
    from security.middleware import RequestIdFilter

    req_id_filter = RequestIdFilter()
    for handler in logging.root.handlers:
        handler.addFilter(req_id_filter)
    # Also attach to uvicorn loggers just in case
    logging.getLogger("uvicorn").addFilter(req_id_filter)
    logging.getLogger("uvicorn.access").addFilter(req_id_filter)

    # Initialize vector store
    logger.info("Initializing vector store...")
    vector_store = ChromaVectorStore(
        persist_directory=settings.chroma_persist_dir,
        collection_name=settings.chroma_collection_name,
    )

    # Make vector store available to routers
    app.state.vector_store = vector_store

    # Load seed data (skills, patterns, guidelines)
    logger.info("Checking for seed data...")
    try:
        from seed_data import load_seed_data

        summary = load_seed_data(vector_store)
        logger.info(f"Startup data check complete: {summary}")
    except Exception as e:
        logger.error(f"Failed to load seed data on startup: {e}")
        logger.warning(
            "Application starting without fresh seed data. Check GOOGLE_API_KEY if this is unexpected."
        )

    logger.info(f"Prompt RAG Agent {settings.app_version} started")
    yield

    # Cleanup
    logger.info("Shutting down Prompt RAG Agent...")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="RAG system for generating high-quality prompts with security guardrails",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(SafeLoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# Mount routers
app.include_router(agent_router, tags=["Agent"])
app.include_router(ingestion_router, prefix="/admin", tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "vector_store": "connected" if vector_store else "disconnected",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
