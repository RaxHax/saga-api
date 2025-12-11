# Saga Archive Search API

A FastAPI service for semantic image search using multilingual CLIP embeddings. Designed for deployment on Railway with Supabase as the backend.

## Features

- **Text Search**: Search images using natural language queries in 50+ languages
- **Image Search**: Find visually similar images by uploading a reference image
- **Configurable Search Types**: Search against visual, text, or combined embeddings
- **Pre-loaded Model**: CLIP model loads at startup for fast inference
- **Open by Default**: Public endpoints with no API key required

## Quick Start

### 1. Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

Or manually:

1. Create a new Railway project
2. Connect your GitHub repo (or upload this folder)
3. Add environment variables (see below)
4. Deploy!

### 2. Environment Variables

Set these in Railway's Variables tab:

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon or service key |
| `CLIP_MODEL` | No | Model to use (default: `clip-ViT-B-32-multilingual-v1`) |
| `SUPABASE_BUCKET` | No | Storage bucket name (default: `media-files`) |

### 3. Test the API

```bash
# Health check
curl https://your-app.railway.app/health

# Text search
curl -X POST https://your-app.railway.app/search \
  -H "Content-Type: application/json" \
  -d '{"query": "sunset over mountains", "limit": 10}'

# Image search
curl -X POST https://your-app.railway.app/search/image \
  -F "image=@photo.jpg" \
  -F "limit=10"
```

## API Endpoints

### `GET /health`
Health check endpoint (no auth required).

### `POST /search`
Search by text query.

**Body:**
```json
{
  "query": "your search text",
  "search_type": "combined",  // "visual", "text", or "combined"
  "limit": 20,
  "threshold": 0.0,
  "file_type": null,  // "image" or "video"
  "decade": null      // e.g., "1950s"
}
```

### `GET /search`
Same as POST but with query parameters:
```
/search?query=sunset&search_type=combined&limit=10
```

### `POST /search/image`
Search by uploading an image.

**Form Data:**
- `image`: Image file (JPEG, PNG, WebP, GIF)
- `search_type`: "visual", "text", or "combined" (default: "combined")
- `limit`: Max results (default: 20)
- `threshold`: Min similarity (default: 0.0)
- `file_type`: Filter by type
- `decade`: Filter by decade

### `GET /models`
List available CLIP models and current model info.

## Response Format

```json
{
  "query": "sunset over mountains",
  "search_type": "combined",
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "filename": "IMG_001.jpg",
      "original_filename": "sunset_photo.jpg",
      "file_type": "image",
      "mime_type": "image/jpeg",
      "file_size": 1234567,
      "storage_path": "images/IMG_001.jpg",
      "storage_url": "https://...",
      "thumbnail_path": "thumbnails/IMG_001.jpg",
      "thumbnail_url": "https://...",
      "description": "Beautiful sunset over mountain range",
      "tags": ["sunset", "mountains", "landscape"],
      "decade": "2020s",
      "metadata": {},
      "similarity_score": 0.85,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Available Models

| Model | Dimensions | Languages | Size | Notes |
|-------|------------|-----------|------|-------|
| `clip-ViT-B-32-multilingual-v1` | 512 | 50+ | ~600MB | **Default**, best multilingual |
| `clip-ViT-B-32` | 512 | English | ~350MB | Fastest |
| `clip-ViT-L-14` | 768 | English | ~900MB | Higher quality |
| `xlm-roberta-large-ViT-H-14` | 1024 | 100+ | ~2.5GB | Best quality, requires schema change |

**Note:** If using `xlm-roberta-large-ViT-H-14`, your Supabase schema must use `vector(1024)` instead of `vector(512)`.

## Local Development

```bash
# Clone and enter directory
cd railway-search-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your values

# Run the server
uvicorn main:app --reload --port 8000

# Open docs at http://localhost:8000/docs
```

## Railway Configuration

Railway will automatically:
- Detect the Dockerfile
- Build and deploy your app
- Set the `PORT` environment variable
- Provide HTTPS with a custom domain

## Embedding the search UI

If you want to drop a lightweight, read-only search widget into another site, copy the embed snippet in [`USAGE.md`](USAGE.md). It talks directly to the `GET /search` endpoint using the same parameters as the API examples above and defaults to the deployed instance at `https://web-production-2d594.up.railway.app`.

### Recommended Railway Settings

- **Instance Type**: Starter or Pro (model needs ~1GB RAM)
- **Region**: Choose closest to your Supabase region
- **Replicas**: 1 (model is loaded per instance)

## Supabase Setup

Ensure your Supabase project has:

1. **pgvector extension** enabled
2. **media_items table** with embedding columns
3. **search_media_by_embedding** RPC function

See the main project's `resources/schema.sql` for the complete schema.

## Troubleshooting

### Model loading fails
- Ensure enough RAM (minimum 1GB for default model)
- Check Railway logs for specific error

### Search returns empty results
- Verify embeddings exist in your database
- Check that `search_type` matches your indexed embeddings
- Lower the `threshold` value

### Connection to Supabase fails
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Check if your Supabase project is active

## License

MIT
