# Saga Archive Search API

A FastAPI service for semantic image search using multilingual CLIP embeddings. Designed for deployment on Railway with Supabase as the backend.

## Features

- **Text Search**: Search images using natural language queries in 50+ languages
- **Image Search**: Find visually similar images by uploading a reference image
- **Icelandic Translation**: Translate Icelandic queries to English for improved visual search accuracy
- **Configurable Search Types**: Search against visual, text, or combined embeddings
- **Hybrid Search**: Combine vector similarity with full-text search
- **API Key Protection**: Secure your API with a simple API key
- **Pre-loaded Model**: CLIP model loads at startup for fast inference

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
| `API_KEY` | Yes | Secret key to protect your API |
| `GOOGLE_TRANSLATE_API_KEY` | No | Google Cloud Translation API key (enables `translate` feature) |
| `CLIP_MODEL` | No | Model to use (default: `clip-ViT-B-32-multilingual-v1`) |
| `SUPABASE_BUCKET` | No | Storage bucket name (default: `media-files`) |

### 3. Test the API

```bash
# Health check
curl https://your-app.railway.app/health

# Text search
curl -X POST https://your-app.railway.app/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "sunset over mountains", "limit": 10}'

# Text search with Icelandic translation
curl -X POST https://your-app.railway.app/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "sólsetur yfir fjöllum", "translate": true, "limit": 10}'

# Image search
curl -X POST https://your-app.railway.app/search/image \
  -H "X-API-Key: your-api-key" \
  -F "image=@photo.jpg" \
  -F "limit=10"
```

## Translation Feature

The API includes a **translate** toggle that translates Icelandic queries to English before encoding with the CLIP model. This can significantly improve visual search accuracy.

### Why Translation?

While the multilingual CLIP model understands Icelandic text, the **visual** component of CLIP was primarily trained on English image captions. Translating Icelandic queries to English before encoding can result in better visual matches.

### Using Translation

**POST /search**
```json
{
  "query": "sólsetur yfir fjöllum",
  "translate": true,
  "search_type": "visual",
  "limit": 10
}
```

**GET /search**
```
/search?query=sólsetur%20yfir%20fjöllum&translate=true&search_type=visual&limit=10
```

### Response with Translation

When `translate: true` is used, the response includes both the original and translated query:

```json
{
  "query": "sólsetur yfir fjöllum",
  "translated_query": "sunset over the mountains",
  "search_type": "visual",
  "count": 5,
  "results": [...]
}
```

### When to Use Translation

| Scenario | Recommended |
|----------|-------------|
| Icelandic query + Visual search | `translate: true` |
| Icelandic query + Text search | `translate: false` (text embeddings may already match) |
| English query | `translate: false` |
| Combined search | Try both and compare results |

## API Endpoints

### `GET /health`
Health check endpoint (no auth required).

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "clip-ViT-B-32-multilingual-v1",
  "supabase_connected": true,
  "translation_available": true
}
```

### `POST /search`
Search by text query.

**Headers:**
- `X-API-Key`: Your API key

**Body:**
```json
{
  "query": "your search text",
  "search_type": "combined",
  "limit": 20,
  "threshold": 0.0,
  "file_type": null,
  "decade": null,
  "translate": false
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Search query text |
| `search_type` | string | `"combined"` | `"visual"`, `"text"`, or `"combined"` |
| `limit` | int | `20` | Max results (1-100) |
| `threshold` | float | `0.0` | Min similarity score (0.0-1.0) |
| `file_type` | string | `null` | Filter: `"image"` or `"video"` |
| `decade` | string | `null` | Filter by decade (e.g., `"1950s"`) |
| `translate` | bool | `false` | Translate Icelandic to English before CLIP encoding |

### `GET /search`
Same as POST but with query parameters:
```
/search?query=sunset&search_type=combined&limit=10&translate=false
```

### `POST /search/image`
Search by uploading an image.

**Headers:**
- `X-API-Key`: Your API key

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
  "query": "sólsetur yfir fjöllum",
  "translated_query": "sunset over the mountains",
  "search_type": "visual",
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

## Search Types Explained

| Type | Description | Best For |
|------|-------------|----------|
| `visual` | Searches against image embeddings | Visual similarity (colors, composition, objects) |
| `text` | Searches against text embeddings from descriptions/metadata | Finding items by their descriptions or tags |
| `combined` | Searches against combined embeddings | **Recommended default** - balanced approach |

## Available Models

| Model | Dimensions | Languages | Size | Notes |
|-------|------------|-----------|------|-------|
| `clip-ViT-B-32-multilingual-v1` | 512 | 50+ | ~600MB | **Default**, best multilingual |
| `clip-ViT-B-32` | 512 | English | ~350MB | Fastest |
| `clip-ViT-L-14` | 768 | English | ~900MB | Higher quality |
| `xlm-roberta-large-ViT-H-14` | 1024 | 100+ | ~2.5GB | Best quality, requires schema change |

**Note:** If using `xlm-roberta-large-ViT-H-14`, your Supabase schema must use `vector(1024)` instead of `vector(512)`.

## Example Usage

### Python

```python
import requests

API_URL = "https://your-app.railway.app"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Search with Icelandic query (translated to English)
response = requests.post(
    f"{API_URL}/search",
    headers=headers,
    json={
        "query": "gamlar ljósmyndir af Reykjavík",
        "translate": True,
        "search_type": "visual",
        "limit": 10
    }
)

data = response.json()
print(f"Original: {data['query']}")
print(f"Translated: {data['translated_query']}")
print(f"Found {data['count']} results")

for result in data['results']:
    print(f"  - {result['filename']}: {result['similarity_score']:.2f}")
```

### JavaScript/TypeScript

```typescript
const API_URL = "https://your-app.railway.app";
const API_KEY = "your-api-key";

async function searchImages(query: string, translate: boolean = false) {
  const response = await fetch(`${API_URL}/search`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      translate,
      search_type: "visual",
      limit: 10,
    }),
  });

  const data = await response.json();
  console.log(`Original: ${data.query}`);
  console.log(`Translated: ${data.translated_query}`);
  console.log(`Found ${data.count} results`);

  return data.results;
}

// Search with Icelandic query
searchImages("hestur á túni", true);
```

### cURL

```bash
# Search with translation enabled
curl -X POST "https://your-app.railway.app/search" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "fólk á götu í Reykjavík",
    "translate": true,
    "search_type": "visual",
    "limit": 5
  }'

# Using GET with query parameters
curl -G "https://your-app.railway.app/search" \
  -H "X-API-Key: your-api-key" \
  --data-urlencode "query=skip í höfn" \
  --data-urlencode "translate=true" \
  --data-urlencode "search_type=visual" \
  --data-urlencode "limit=10"
```

## Local Development

```bash
# Clone and enter directory
cd saga-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
export API_KEY="your-api-key"
export GOOGLE_TRANSLATE_API_KEY="your-google-translate-key"  # Optional

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

### 401 Unauthorized
- Include `X-API-Key` header with your API key
- Verify `API_KEY` environment variable is set

### Connection to Supabase fails
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct
- Check if your Supabase project is active

### Translation not working
- Check that `GOOGLE_TRANSLATE_API_KEY` is set
- Verify the API key has Cloud Translation API enabled
- Check health endpoint: `translation_available` should be `true`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT REQUEST                           │
│         (Text Query with translate=true)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   FastAPI Main Application    │
         │   - API Key Verification      │
         │   - Request Validation        │
         └────────────┬──────────────────┘
                      │
                      ▼
         ┌───────────────────────────────┐
         │   Translation Service         │
         │   (Google Translate API)      │
         │   Icelandic → English         │
         └────────────┬──────────────────┘
                      │
                      ▼
         ┌───────────────────────────────┐
         │   Embedding Service           │
         │   (CLIP Model)                │
         │   Text → 512D Vector          │
         └────────────┬──────────────────┘
                      │
                      ▼
         ┌───────────────────────────────┐
         │   Supabase Search Service     │
         │   (pgvector Similarity)       │
         └────────────┬──────────────────┘
                      │
                      ▼
         ┌───────────────────────────────┐
         │   Ranked Results              │
         │   + Translated Query          │
         └────────────────────────────────┘
```

## License

MIT
