"""
Translation Service using Google Translate API.
Translates Icelandic queries to English for improved CLIP visual search.
"""

import logging
import os
from typing import Optional
import urllib.request
import urllib.parse
import json

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating text using Google Translate API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the translation service.

        Args:
            api_key: Google Translate API key. If not provided, uses GOOGLE_TRANSLATE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GOOGLE_TRANSLATE_API_KEY")
        self.base_url = "https://translation.googleapis.com/language/translate/v2"

        if not self.api_key:
            logger.warning("GOOGLE_TRANSLATE_API_KEY not set - translation will be disabled")

    @property
    def is_available(self) -> bool:
        """Check if translation service is available."""
        return self.api_key is not None

    def translate(
        self,
        text: str,
        source_language: str = "is",  # Icelandic
        target_language: str = "en"    # English
    ) -> str:
        """
        Translate text from source language to target language.

        Args:
            text: Text to translate
            source_language: Source language code (default: 'is' for Icelandic)
            target_language: Target language code (default: 'en' for English)

        Returns:
            Translated text, or original text if translation fails
        """
        if not self.api_key:
            logger.warning("Translation requested but API key not configured")
            return text

        if not text or not text.strip():
            return text

        try:
            # Build the request URL
            params = {
                "key": self.api_key,
                "q": text,
                "source": source_language,
                "target": target_language,
                "format": "text"
            }

            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

            # Make the request
            req = urllib.request.Request(url, method="POST")
            req.add_header("Content-Type", "application/json")

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))

            # Extract translated text
            translated_text = result["data"]["translations"][0]["translatedText"]

            logger.info(f"Translated: '{text}' -> '{translated_text}'")
            return translated_text

        except urllib.error.HTTPError as e:
            logger.error(f"Translation API HTTP error: {e.code} - {e.reason}")
            return text
        except urllib.error.URLError as e:
            logger.error(f"Translation API URL error: {e.reason}")
            return text
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Translation API response parsing error: {e}")
            return text
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text

    def translate_icelandic_to_english(self, text: str) -> str:
        """
        Convenience method to translate Icelandic to English.

        Args:
            text: Icelandic text to translate

        Returns:
            English translation, or original text if translation fails
        """
        return self.translate(text, source_language="is", target_language="en")
