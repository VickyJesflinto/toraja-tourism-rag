"""
rag/embeddings/embedder.py
Sentence Transformer embedding using paraphrase-multilingual-MiniLM-L12-v2.
Supports batch encoding with caching.
"""
import numpy as np
from typing import List, Union
from loguru import logger


class Embedder:
    """
    Wraps sentence-transformers for dense vector encoding.
    Model: paraphrase-multilingual-MiniLM-L12-v2 (supports Indonesian/multilingual)
    Output dimension: 384
    """

    _instance = None   # singleton

    def __new__(cls, model_name: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = None):
        if self._initialized:
            return
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from config.settings import EMBEDDING_MODEL, EMBEDDING_DIMENSION
        self.model_name = model_name or EMBEDDING_MODEL
        self.dimension  = EMBEDDING_DIMENSION
        self._model     = None
        self._initialized = True

    def _load_model(self):
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded.")

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 64,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Encode one or more texts to float32 numpy arrays.
        Returns shape (N, 384) or (384,) for single string.
        """
        self._load_model()

        single = isinstance(texts, str)
        if single:
            texts = [texts]

        vectors = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )
        return vectors[0] if single else vectors

    def encode_query(self, query: str) -> np.ndarray:
        """Encode a single search query."""
        return self.encode(query, normalize=True)

    def encode_documents(self, docs: List[str], batch_size: int = 64) -> np.ndarray:
        """Encode a list of document chunks."""
        return self.encode(docs, batch_size=batch_size, normalize=True)
