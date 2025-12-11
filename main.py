"""
Saga Archive Search API
A FastAPI service for semantic image search using multilingual CLIP embeddings.
Designed for Railway deployment.
"""

import os
import io
import logging
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from services.embedding_service import EmbeddingService
from services.supabase_service import SupabaseSearchService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services (initialized at startup)
embedding_service: Optional[EmbeddingService] = None
supabase_service: Optional[SupabaseSearchService] = None

# API Key security
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Verify the API key from request header."""
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        logger.warning("API_KEY not set in environment - API is unprotected!")
        return "no-key-required"

    if not api_key or api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Provide X-API-Key header."
        )
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global embedding_service, supabase_service

    # Startup: Load model and initialize services
    logger.info("Starting up Saga Search API...")

    # Initialize embedding service (loads CLIP model)
    model_name = os.getenv("CLIP_MODEL", "clip-ViT-B-32-multilingual-v1")
    device = os.getenv("DEVICE", "auto")
    logger.info(f"Loading CLIP model: {model_name} on device: {device}")

    embedding_service = EmbeddingService(model_name=model_name, device=device)
    logger.info("CLIP model loaded successfully!")

    # Initialize Supabase service
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")  # Can be anon or service key

    if not supabase_url or not supabase_key:
        logger.warning("SUPABASE_URL and SUPABASE_KEY not set - API will start in degraded mode")
        supabase_service = None
    else:
        try:
            supabase_service = SupabaseSearchService(url=supabase_url, key=supabase_key)
            logger.info("Supabase service initialized!")
        except Exception as exc:
            logger.error("Failed to initialize Supabase service: %s", exc)
            supabase_service = None

    logger.info("Saga Search API ready!")

    yield

    # Shutdown
    logger.info("Shutting down Saga Search API...")


# Create FastAPI app
app = FastAPI(
    title="Saga Archive Search API",
    description="Semantic image search API using multilingual CLIP embeddings",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models ---

class SearchResult(BaseModel):
    """A single search result."""
    id: str
    filename: str
    original_filename: Optional[str] = None
    file_type: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    storage_path: str
    thumbnail_path: Optional[str] = None
    storage_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    decade: Optional[str] = None
    duration_seconds: Optional[float] = None
    metadata: Optional[dict] = None
    similarity_score: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TextSearchRequest(BaseModel):
    """Request body for text-based search."""
    query: str = Field(..., description="Search query text", min_length=1)
    search_type: str = Field(
        default="combined",
        description="Embedding type to search: 'visual', 'text', or 'combined'"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    file_type: Optional[str] = Field(default=None, description="Filter by file type: 'image' or 'video'")
    decade: Optional[str] = Field(default=None, description="Filter by decade (e.g., '1950s')")


class TextSearchResponse(BaseModel):
    """Response for text search."""
    query: str
    search_type: str
    results: List[SearchResult]
    count: int


class ImageSearchResponse(BaseModel):
    """Response for image search."""
    search_type: str
    results: List[SearchResult]
    count: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    model_name: str
    supabase_connected: bool


# --- Endpoints ---

@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Saga Archive Search API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Info"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        model_loaded=embedding_service is not None and embedding_service.model is not None,
        model_name=embedding_service.model_name if embedding_service else "not loaded",
        supabase_connected=supabase_service is not None
    )


@app.post("/search", response_model=TextSearchResponse, tags=["Search"])
async def search_by_text(
    request: TextSearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Search for images using a text query.

    The query text is encoded using the multilingual CLIP model and compared
    against stored embeddings using cosine similarity.

    **Search Types:**
    - `visual`: Search against image embeddings (best for visual descriptions)
    - `text`: Search against text embeddings from descriptions/metadata
    - `combined`: Search against combined embeddings (recommended, default)
    """
    if not embedding_service or not supabase_service:
        raise HTTPException(status_code=503, detail="Services not initialized")

    # Validate search type
    if request.search_type not in ["visual", "text", "combined"]:
        raise HTTPException(
            status_code=400,
            detail="search_type must be 'visual', 'text', or 'combined'"
        )

    logger.info(f"Text search: '{request.query}' (type={request.search_type}, limit={request.limit})")

    # Encode the query text
    query_embedding = embedding_service.encode_text(request.query)

    # Search in Supabase
    results = await supabase_service.search_by_embedding(
        embedding=query_embedding,
        search_type=request.search_type,
        limit=request.limit,
        threshold=request.threshold,
        file_type=request.file_type,
        decade=request.decade
    )

    return TextSearchResponse(
        query=request.query,
        search_type=request.search_type,
        results=results,
        count=len(results)
    )


@app.get("/search", response_model=TextSearchResponse, tags=["Search"])
async def search_by_text_get(
    query: str = Query(..., description="Search query text", min_length=1),
    search_type: str = Query(default="combined", description="Embedding type: 'visual', 'text', or 'combined'"),
    limit: int = Query(default=20, ge=1, le=100, description="Max results"),
    threshold: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum similarity"),
    file_type: Optional[str] = Query(default=None, description="Filter: 'image' or 'video'"),
    decade: Optional[str] = Query(default=None, description="Filter by decade"),
    api_key: str = Depends(verify_api_key)
):
    """
    Search for images using a text query (GET method).

    Same as POST /search but using query parameters.
    """
    request = TextSearchRequest(
        query=query,
        search_type=search_type,
        limit=limit,
        threshold=threshold,
        file_type=file_type,
        decade=decade
    )
    return await search_by_text(request, api_key)


@app.post("/search/image", response_model=ImageSearchResponse, tags=["Search"])
async def search_by_image(
    image: UploadFile = File(..., description="Image file to search with"),
    search_type: str = Query(default="combined", description="Embedding type: 'visual', 'text', or 'combined'"),
    limit: int = Query(default=20, ge=1, le=100, description="Max results"),
    threshold: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum similarity"),
    file_type: Optional[str] = Query(default=None, description="Filter: 'image' or 'video'"),
    decade: Optional[str] = Query(default=None, description="Filter by decade"),
    api_key: str = Depends(verify_api_key)
):
    """
    Search for similar images using an uploaded image.

    Upload an image and find visually similar items in the archive.
    The image is encoded using the CLIP model and compared against stored embeddings.

    **Supported formats:** JPEG, PNG, WebP, GIF
    """
    if not embedding_service or not supabase_service:
        raise HTTPException(status_code=503, detail="Services not initialized")

    # Validate search type
    if search_type not in ["visual", "text", "combined"]:
        raise HTTPException(
            status_code=400,
            detail="search_type must be 'visual', 'text', or 'combined'"
        )

    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be an image"
        )

    logger.info(f"Image search: {image.filename} (type={search_type}, limit={limit})")

    # Read image bytes
    image_bytes = await image.read()

    # Encode the image
    try:
        query_embedding = embedding_service.encode_image(io.BytesIO(image_bytes))
    except Exception as e:
        logger.error(f"Failed to encode image: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")

    # Search in Supabase
    results = await supabase_service.search_by_embedding(
        embedding=query_embedding,
        search_type=search_type,
        limit=limit,
        threshold=threshold,
        file_type=file_type,
        decade=decade
    )

    return ImageSearchResponse(
        search_type=search_type,
        results=results,
        count=len(results)
    )


@app.get("/models", tags=["Info"])
async def list_models(api_key: str = Depends(verify_api_key)):
    """List available CLIP models and current model info."""
    return {
        "current_model": embedding_service.model_name if embedding_service else None,
        "embedding_dimension": embedding_service.embedding_dim if embedding_service else None,
        "device": str(embedding_service.device) if embedding_service else None,
        "available_models": [
            {
                "id": "clip-ViT-B-32-multilingual-v1",
                "name": "Multilingual CLIP ViT-B/32",
                "dimensions": 512,
                "languages": "50+ including Icelandic",
                "size": "~600MB"
            },
            {
                "id": "clip-ViT-B-32",
                "name": "CLIP ViT-B/32 (OpenAI)",
                "dimensions": 512,
                "languages": "English only",
                "size": "~350MB"
            },
            {
                "id": "clip-ViT-L-14",
                "name": "CLIP ViT-L/14 (OpenAI)",
                "dimensions": 768,
                "languages": "English only",
                "size": "~900MB"
            },
            {
                "id": "xlm-roberta-large-ViT-H-14",
                "name": "XLM-RoBERTa + ViT-H/14",
                "dimensions": 1024,
                "languages": "100+ languages",
                "size": "~2.5GB"
            }
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT", "production") == "development"
    )
