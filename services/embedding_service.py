"""
Embedding Service for CLIP model.
Handles loading the model and encoding text/images to embeddings.
"""

import logging
from typing import Union, List, Optional
from io import BytesIO

import torch
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Model configurations
MODEL_CONFIGS = {
    "clip-ViT-B-32-multilingual-v1": {
        "type": "sentence-transformers",
        "embedding_dim": 512,
    },
    "clip-ViT-B-32": {
        "type": "sentence-transformers",
        "embedding_dim": 512,
    },
    "clip-ViT-L-14": {
        "type": "sentence-transformers",
        "embedding_dim": 768,
    },
    "xlm-roberta-large-ViT-H-14": {
        "type": "open_clip",
        "pretrained": "frozen_laion5b_s13b_b90k",
        "embedding_dim": 1024,
    },
}


class EmbeddingService:
    """Service for generating CLIP embeddings from text and images."""

    def __init__(self, model_name: str = "clip-ViT-B-32-multilingual-v1", device: str = "auto"):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the CLIP model to use
            device: Device to run model on ("auto", "cuda", "mps", "cpu")
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.preprocess = None
        self.model_type = None
        self.embedding_dim = None

        # Determine device
        if device == "auto":
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)

        logger.info(f"Using device: {self.device}")

        # Load the model
        self._load_model()

    def _load_model(self):
        """Load the CLIP model based on configuration."""
        if self.model_name not in MODEL_CONFIGS:
            raise ValueError(f"Unknown model: {self.model_name}. Available: {list(MODEL_CONFIGS.keys())}")

        config = MODEL_CONFIGS[self.model_name]
        self.model_type = config["type"]
        self.embedding_dim = config["embedding_dim"]

        logger.info(f"Loading model: {self.model_name} (type: {self.model_type})")

        if self.model_type == "sentence-transformers":
            self._load_sentence_transformer()
        elif self.model_type == "open_clip":
            self._load_open_clip(config.get("pretrained"))

        logger.info(f"Model loaded! Embedding dimension: {self.embedding_dim}")

    def _load_sentence_transformer(self):
        """Load a sentence-transformers CLIP model."""
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(self.model_name, device=str(self.device))

    def _load_open_clip(self, pretrained: str):
        """Load an OpenCLIP model."""
        import open_clip

        # Parse model name - remove the prefix if present
        clip_model_name = self.model_name
        if "xlm-roberta" in self.model_name.lower():
            clip_model_name = "xlm-roberta-large-ViT-H-14"

        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            clip_model_name,
            pretrained=pretrained,
            device=self.device
        )
        self.tokenizer = open_clip.get_tokenizer(clip_model_name)
        self.model.eval()

    def encode_text(self, text: Union[str, List[str]]) -> List[float]:
        """
        Encode text to embedding vector.

        Args:
            text: Single text string or list of strings

        Returns:
            Embedding as a list of floats (for single text) or list of lists
        """
        if isinstance(text, str):
            texts = [text]
            single = True
        else:
            texts = text
            single = False

        if self.model_type == "sentence-transformers":
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
        else:
            # OpenCLIP
            with torch.no_grad():
                tokens = self.tokenizer(texts).to(self.device)
                embeddings = self.model.encode_text(tokens)
                embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
                embeddings = embeddings.cpu().numpy()

        if single:
            return embeddings[0].tolist()
        return [e.tolist() for e in embeddings]

    def encode_image(self, image: Union[str, BytesIO, Image.Image, bytes]) -> List[float]:
        """
        Encode an image to embedding vector.

        Args:
            image: Image path, BytesIO, PIL Image, or bytes

        Returns:
            Embedding as a list of floats
        """
        # Load image if needed
        if isinstance(image, str):
            pil_image = Image.open(image)
        elif isinstance(image, bytes):
            pil_image = Image.open(BytesIO(image))
        elif isinstance(image, BytesIO):
            pil_image = Image.open(image)
        elif isinstance(image, Image.Image):
            pil_image = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        # Convert to RGB if necessary
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        if self.model_type == "sentence-transformers":
            embedding = self.model.encode(
                pil_image,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
        else:
            # OpenCLIP
            with torch.no_grad():
                image_tensor = self.preprocess(pil_image).unsqueeze(0).to(self.device)
                embedding = self.model.encode_image(image_tensor)
                embedding = embedding / embedding.norm(dim=-1, keepdim=True)
                embedding = embedding.cpu().numpy()[0]

        return embedding.tolist()

    def encode_images_batch(self, images: List[Union[str, BytesIO, Image.Image]], batch_size: int = 8) -> List[List[float]]:
        """
        Encode multiple images in batches.

        Args:
            images: List of image paths, BytesIO objects, or PIL Images
            batch_size: Batch size for processing

        Returns:
            List of embeddings
        """
        all_embeddings = []

        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]

            # Load images
            pil_images = []
            for img in batch:
                if isinstance(img, str):
                    pil_image = Image.open(img)
                elif isinstance(img, BytesIO):
                    pil_image = Image.open(img)
                elif isinstance(img, Image.Image):
                    pil_image = img
                else:
                    raise ValueError(f"Unsupported image type: {type(img)}")

                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
                pil_images.append(pil_image)

            if self.model_type == "sentence-transformers":
                embeddings = self.model.encode(
                    pil_images,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
            else:
                # OpenCLIP
                with torch.no_grad():
                    image_tensors = torch.stack([
                        self.preprocess(img) for img in pil_images
                    ]).to(self.device)
                    embeddings = self.model.encode_image(image_tensors)
                    embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
                    embeddings = embeddings.cpu().numpy()

            all_embeddings.extend([e.tolist() for e in embeddings])

        return all_embeddings
