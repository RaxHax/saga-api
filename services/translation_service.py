"""
Translation Service.
Handles translating text from Icelandic to English using Google Translate API.
"""

import logging
import httpx

logger = logging.getLogger(__name__)

# Google Translate API key (hardcoded for Saga project)
GOOGLE_TRANSLATE_API_KEY = "AIzaSyBrB-NHAQMeqwqOIhK8TAZXBP3O9mb2xv8"
GOOGLE_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"


class TranslationService:
    """Service for translating text from Icelandic to English."""

    def __init__(self):
        """Initialize the translation service."""
        self.api_key = GOOGLE_TRANSLATE_API_KEY
        self.api_url = GOOGLE_TRANSLATE_URL
        logger.info("Translation service initialized (Icelandic -> English)")

    async def translate_to_english(self, text: str) -> str:
        """
        Translate Icelandic text to English.

        Args:
            text: The Icelandic text to translate

        Returns:
            The translated English text, or original text if translation fails
        """
        if not text or not text.strip():
            return text

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    params={"key": self.api_key},
                    json={
                        "q": text,
                        "source": "is",  # Icelandic
                        "target": "en",  # English
                        "format": "text"
                    },
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                translated_text = data["data"]["translations"][0]["translatedText"]

                logger.info(f"Translated: '{text}' -> '{translated_text}'")
                return translated_text

        except httpx.HTTPStatusError as e:
            logger.error(f"Translation API HTTP error: {e.response.status_code} - {e.response.text}")
            return text
        except httpx.RequestError as e:
            logger.error(f"Translation API request error: {e}")
            return text
        except (KeyError, IndexError) as e:
            logger.error(f"Translation API response parsing error: {e}")
            return text
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text


# Global instance
translation_service: TranslationService = None


def get_translation_service() -> TranslationService:
    """Get or create the translation service singleton."""
    global translation_service
    if translation_service is None:
        translation_service = TranslationService()
    return translation_service
