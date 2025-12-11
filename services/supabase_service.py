"""
Supabase Search Service.
Handles searching media items by embedding similarity.
"""

import os
import logging
from typing import List, Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseSearchService:
    """Service for searching media in Supabase using vector similarity."""

    def __init__(self, url: str, key: str):
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL
            key: Supabase API key (anon or service key)
        """
        self.url = url
        self.key = key
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "media-files")
        self.client: Client = create_client(url, key)
        logger.info(f"Supabase client initialized for: {url}")

    def _get_public_url(self, storage_path: Optional[str]) -> Optional[str]:
        """Get public URL for a storage path."""
        if not storage_path:
            return None
        try:
            return self.client.storage.from_(self.bucket_name).get_public_url(storage_path)
        except Exception as e:
            logger.warning(f"Failed to get public URL for {storage_path}: {e}")
            return None

    async def search_by_embedding(
        self,
        embedding: List[float],
        search_type: str = "combined",
        limit: int = 20,
        threshold: float = 0.0,
        file_type: Optional[str] = None,
        decade: Optional[str] = None
    ) -> List[dict]:
        """
        Search media items by embedding similarity.

        Args:
            embedding: Query embedding vector
            search_type: Which embedding to search against ('visual', 'text', 'combined')
            limit: Maximum number of results
            threshold: Minimum similarity score (0-1)
            file_type: Filter by 'image' or 'video'
            decade: Filter by decade (e.g., '1950s')

        Returns:
            List of search results with similarity scores
        """
        try:
            # Call the Supabase RPC function
            response = self.client.rpc(
                "search_media_by_embedding",
                {
                    "query_embedding": embedding,
                    "search_type": search_type,
                    "match_threshold": threshold,
                    "match_count": limit,
                    "file_type_filter": file_type,
                    "decade_filter": decade
                }
            ).execute()

            if not response.data:
                return []

            # Process results
            results = []
            for item in response.data:
                result = {
                    "id": str(item.get("id", "")),
                    "filename": item.get("filename", ""),
                    "original_filename": item.get("original_filename"),
                    "file_type": item.get("file_type", ""),
                    "mime_type": item.get("mime_type"),
                    "file_size": item.get("file_size"),
                    "storage_path": item.get("storage_path", ""),
                    "thumbnail_path": item.get("thumbnail_path"),
                    "description": item.get("description"),
                    "tags": item.get("tags"),
                    "decade": item.get("decade"),
                    "duration_seconds": item.get("duration_seconds"),
                    "metadata": item.get("metadata"),
                    "similarity_score": float(item.get("similarity", 0)),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                }

                # Add public URLs
                result["storage_url"] = self._get_public_url(result["storage_path"])
                result["thumbnail_url"] = self._get_public_url(result["thumbnail_path"])

                results.append(result)

            logger.info(f"Search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    async def hybrid_search(
        self,
        embedding: List[float],
        text_query: str,
        search_type: str = "combined",
        limit: int = 20,
        threshold: float = 0.0,
        vector_weight: float = 0.7,
        text_weight: float = 0.3,
        file_type: Optional[str] = None,
        decade: Optional[str] = None
    ) -> List[dict]:
        """
        Hybrid search combining vector similarity and text search.

        Args:
            embedding: Query embedding vector
            text_query: Text query for full-text search
            search_type: Which embedding to search against
            limit: Maximum number of results
            threshold: Minimum score threshold
            vector_weight: Weight for vector similarity (0-1)
            text_weight: Weight for text match (0-1)
            file_type: Filter by file type
            decade: Filter by decade

        Returns:
            List of search results with combined scores
        """
        try:
            response = self.client.rpc(
                "hybrid_search_media",
                {
                    "query_embedding": embedding,
                    "query_text": text_query,
                    "search_type": search_type,
                    "match_threshold": threshold,
                    "match_count": limit,
                    "vector_weight": vector_weight,
                    "text_weight": text_weight,
                    "file_type_filter": file_type,
                    "decade_filter": decade
                }
            ).execute()

            if not response.data:
                return []

            results = []
            for item in response.data:
                result = {
                    "id": str(item.get("id", "")),
                    "filename": item.get("filename", ""),
                    "original_filename": item.get("original_filename"),
                    "file_type": item.get("file_type", ""),
                    "mime_type": item.get("mime_type"),
                    "file_size": item.get("file_size"),
                    "storage_path": item.get("storage_path", ""),
                    "thumbnail_path": item.get("thumbnail_path"),
                    "description": item.get("description"),
                    "tags": item.get("tags"),
                    "decade": item.get("decade"),
                    "duration_seconds": item.get("duration_seconds"),
                    "metadata": item.get("metadata"),
                    "similarity_score": float(item.get("combined_score", item.get("similarity", 0))),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                }

                result["storage_url"] = self._get_public_url(result["storage_path"])
                result["thumbnail_url"] = self._get_public_url(result["thumbnail_path"])

                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            raise

    def test_connection(self) -> bool:
        """Test if Supabase connection is working."""
        try:
            # Try a simple query
            self.client.table("media_items").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
