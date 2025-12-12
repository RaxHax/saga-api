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

    async def text_search(
        self,
        text_query: str,
        limit: int = 20,
        file_type: Optional[str] = None,
        decade: Optional[str] = None
    ) -> List[dict]:
        """
        Full-text search on descriptions, tags, and filenames.

        Args:
            text_query: Text query for full-text search
            limit: Maximum number of results
            file_type: Filter by file type
            decade: Filter by decade

        Returns:
            List of search results with text relevance scores
        """
        try:
            # Build query with text search on description, tags, filename
            query = self.client.table("media_items").select("*")

            # Apply filters
            if file_type:
                query = query.eq("file_type", file_type)
            if decade:
                query = query.eq("decade", decade)

            # Use ilike for case-insensitive partial matching on multiple fields
            # We search in description, original_filename, and tags
            search_term = f"%{text_query}%"
            query = query.or_(
                f"description.ilike.{search_term},"
                f"original_filename.ilike.{search_term},"
                f"filename.ilike.{search_term},"
                f"tags.cs.{{{text_query}}}"
            )

            query = query.limit(limit)
            response = query.execute()

            if not response.data:
                return []

            results = []
            for item in response.data:
                # Calculate a simple text relevance score based on match quality
                text_score = self._calculate_text_relevance(item, text_query)

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
                    "similarity_score": text_score,
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                }

                result["storage_url"] = self._get_public_url(result["storage_path"])
                result["thumbnail_url"] = self._get_public_url(result["thumbnail_path"])

                results.append(result)

            # Sort by text relevance score
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results

        except Exception as e:
            logger.error(f"Text search error: {e}")
            raise

    def _calculate_text_relevance(self, item: dict, query: str) -> float:
        """
        Calculate text relevance score based on where and how the query matches.

        Returns a score between 0 and 1.
        """
        query_lower = query.lower()
        score = 0.0

        # Check description (highest weight)
        description = (item.get("description") or "").lower()
        if query_lower in description:
            # Exact match in description
            if description == query_lower:
                score += 0.5
            elif description.startswith(query_lower) or description.endswith(query_lower):
                score += 0.4
            else:
                score += 0.3

        # Check filename
        filename = (item.get("original_filename") or item.get("filename") or "").lower()
        if query_lower in filename:
            score += 0.25

        # Check tags
        tags = item.get("tags") or []
        if isinstance(tags, list):
            for tag in tags:
                if query_lower in tag.lower():
                    score += 0.25
                    break

        return min(score, 1.0)  # Cap at 1.0

    def test_connection(self) -> bool:
        """Test if Supabase connection is working."""
        try:
            # Try a simple query
            self.client.table("media_items").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
