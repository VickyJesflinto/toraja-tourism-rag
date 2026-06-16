"""
rag/retrieval/faiss_store.py
FAISS vector store: build flat inner-product index, add/remove/search vectors.
Persists index and ID mapping to disk.
"""
import os
import json
import pickle
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.settings import FAISS_INDEX_PATH, EMBEDDING_DIMENSION, FAISS_K


class FAISSStore:
    """
    Wrapper around faiss.IndexFlatIP (cosine similarity via normalized vectors).
    Maintains a mapping: faiss_position → chunk primary key in DB.
    """

    INDEX_FILE   = "index.faiss"
    MAPPING_FILE = "id_mapping.pkl"

    def __init__(
        self,
        index_path: Path = FAISS_INDEX_PATH,
        dimension: int   = EMBEDDING_DIMENSION,
    ):
        self.index_path = Path(index_path)
        self.dimension  = dimension
        self.index_path.mkdir(parents=True, exist_ok=True)
        self._index     = None
        self._id_map: List[int] = []   # faiss_position → db chunk_id
        self._load_or_create()

    # ─── Lifecycle ────────────────────────────────────────────────────────────
    def _load_or_create(self):
        import faiss
        idx_file = self.index_path / self.INDEX_FILE
        map_file = self.index_path / self.MAPPING_FILE

        if idx_file.exists() and map_file.exists():
            self._index = faiss.read_index(str(idx_file))
            with open(map_file, "rb") as f:
                self._id_map = pickle.load(f)
            logger.info(f"FAISS index loaded: {self._index.ntotal} vectors")
        else:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._id_map = []
            logger.info("New FAISS index created.")

    def save(self):
        import faiss
        faiss.write_index(self._index, str(self.index_path / self.INDEX_FILE))
        with open(self.index_path / self.MAPPING_FILE, "wb") as f:
            pickle.dump(self._id_map, f)
        logger.debug("FAISS index saved.")

    # ─── Add ──────────────────────────────────────────────────────────────────
    def add_vectors(
        self,
        vectors: np.ndarray,
        chunk_ids: List[int],
    ) -> List[int]:
        """
        Add normalized float32 vectors.
        Returns list of faiss positions assigned.
        """
        vectors = vectors.astype(np.float32)
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        start_pos = len(self._id_map)
        self._index.add(vectors)
        self._id_map.extend(chunk_ids)
        self.save()

        positions = list(range(start_pos, start_pos + len(chunk_ids)))
        logger.info(f"Added {len(chunk_ids)} vectors. Total: {self._index.ntotal}")
        return positions

    # ─── Search ───────────────────────────────────────────────────────────────
    def search(
        self,
        query_vector: np.ndarray,
        k: int = FAISS_K,
    ) -> List[Tuple[int, float]]:
        """
        Search top-k nearest vectors.
        Returns list of (chunk_db_id, similarity_score).
        """
        if self._index.ntotal == 0:
            return []

        query = query_vector.astype(np.float32).reshape(1, -1)
        k = min(k, self._index.ntotal)
        scores, positions = self._index.search(query, k)

        results = []
        for pos, score in zip(positions[0], scores[0]):
            if pos < 0:
                continue
            chunk_id = self._id_map[pos]
            results.append((chunk_id, float(score)))
        return results

    # ─── Remove ───────────────────────────────────────────────────────────────
    def remove_by_chunk_ids(self, chunk_ids: List[int]):
        """Rebuild index without the given chunk IDs (FAISS flat has no delete)."""
        import faiss

        positions_to_remove = {i for i, cid in enumerate(self._id_map) if cid in chunk_ids}
        remaining_positions = [i for i in range(len(self._id_map)) if i not in positions_to_remove]

        if not remaining_positions:
            self._index = faiss.IndexFlatIP(self.dimension)
            self._id_map = []
        else:
            # Reconstruct vectors for remaining positions
            all_vecs = self._index.reconstruct_n(0, self._index.ntotal)
            kept_vecs = np.array([all_vecs[i] for i in remaining_positions], dtype=np.float32)
            kept_ids  = [self._id_map[i] for i in remaining_positions]

            self._index = faiss.IndexFlatIP(self.dimension)
            self._index.add(kept_vecs)
            self._id_map = kept_ids

        self.save()
        logger.info(f"Removed {len(positions_to_remove)} vectors. Remaining: {self._index.ntotal}")

    # ─── Properties ───────────────────────────────────────────────────────────
    @property
    def total_vectors(self) -> int:
        return self._index.ntotal if self._index else 0

    def get_vectors_by_chunk_ids(
        self,
        chunk_ids: List[int],
    ) -> np.ndarray | None:
        """
        Rekonstruksi vektor embedding dari FAISS berdasarkan chunk DB-ID.
        Dibutuhkan oleh algoritma MMR untuk menghitung similarity antar-chunk.

        Returns:
            np.ndarray shape (N, D) sesuai urutan chunk_ids,
            atau None jika gagal / index kosong.
        """
        if self._index is None or self._index.ntotal == 0:
            return None

        # Bangun reverse map: chunk_db_id → faiss_position
        db_id_to_pos = {db_id: pos for pos, db_id in enumerate(self._id_map)}

        positions = []
        for cid in chunk_ids:
            pos = db_id_to_pos.get(cid)
            if pos is not None:
                positions.append(pos)

        if not positions:
            return None

        try:
            all_vecs = self._index.reconstruct_n(0, self._index.ntotal)
            vectors  = np.array([all_vecs[p] for p in positions], dtype=np.float32)
            return vectors
        except Exception as e:
            logger.error(f"FAISS reconstruct error: {e}")
            return None
