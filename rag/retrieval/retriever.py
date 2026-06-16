"""
rag/retrieval/retriever.py

RAG Retriever dengan dua strategi:

1. Standard  — top-K berdasarkan cosine similarity tertinggi ke query.
               Cepat, tapi bisa menghasilkan chunk redundan jika banyak
               dokumen membahas topik yang sama.

2. MMR — Maximal Marginal Relevance (default)
   Memilih chunk secara iteratif dengan menyeimbangkan dua kriteria:
     • Relevance  : seberapa mirip chunk dengan query  (cosine similarity)
     • Diversity  : seberapa BERBEDA chunk dari chunk yang sudah dipilih

   Formula per iterasi:
     score(cᵢ) = λ · sim(cᵢ, query) − (1−λ) · max_{cⱼ∈S} sim(cᵢ, cⱼ)

   Parameter λ (lambda_mmr):
     λ = 1.0  →  pure relevance  (identik dengan standard)
     λ = 0.5  →  seimbang        (default — direkomendasikan)
     λ = 0.0  →  pure diversity

   Validasi (vector 384-dim realistis, sim(c0,c1)=0.93):
     Standard λ=—  : memilih [c0, c1, c2] — c0 & c1 redundan ❌
     MMR      λ=0.5: memilih [c0, c2, c3] — beragam ✅
     MMR      λ=0.3: memilih [c0, c3, c4] — maksimal diversity ✅

   Proses:
     1. Ambil candidate pool besar dari FAISS (fetch_k, default=20)
     2. Pilih chunk pertama = chunk paling relevan ke query
     3. Tiap iterasi berikutnya: pilih chunk dengan skor MMR tertinggi
        (paling relevan DAN paling berbeda dari yang sudah terpilih)
     4. Ulangi sampai k chunk terpilih
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.settings import FAISS_K, MMR_ENABLED, MMR_LAMBDA, MMR_FETCH_K
from rag.embeddings.embedder import Embedder
from rag.retrieval.faiss_store import FAISSStore
from database.connection import db_session
from database.models import DocumentChunk, Document


# ─── Data class ───────────────────────────────────────────────────────────────

class RetrievedChunk:
    def __init__(
        self,
        chunk_id:  int,
        content:   str,
        score:     float,
        mmr_score: float,
        source:    str,
        meta_data:  Dict[str, Any],
    ):
        self.chunk_id  = chunk_id
        self.content   = content
        self.score     = score       # cosine similarity asli ke query
        self.mmr_score = mmr_score   # skor MMR akhir (= score jika mode standard)
        self.source    = source
        self.meta_data  = meta_data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id":  self.chunk_id,
            "content":   self.content,
            "score":     round(self.score, 4),
            "mmr_score": round(self.mmr_score, 4),
            "source":    self.source,
            "meta_data":  self.meta_data,
        }


# ─── Similarity helper ────────────────────────────────────────────────────────

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity dua vektor 1-D.
    Sentence-transformer sudah menormalisasi vektornya (L2=1),
    sehingga cosine sim ≡ dot product. Kita tetap hitung eksplisit
    untuk keamanan jika ada vektor dari sumber lain.
    """
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ─── MMR algorithm ────────────────────────────────────────────────────────────

def _mmr_select(
    query_vector:      np.ndarray,    # shape (D,)
    candidate_vectors: np.ndarray,    # shape (N, D)
    candidate_scores:  List[float],   # cosine sim tiap candidate ke query
    k:                 int,
    lambda_mmr:        float = 0.5,
) -> List[int]:
    """
    Algoritma MMR — memilih k indeks dari candidate_vectors.

    Pada setiap iterasi:
      - Hitung skor MMR tiap candidate yang belum dipilih
      - Pilih candidate dengan skor MMR tertinggi
      - Tambahkan ke set S (sudah dipilih) dan hapus dari remaining

    Returns:
        List[int] — indeks ke dalam candidate_vectors (urutan pemilihan)
    """
    n = len(candidate_scores)
    k = min(k, n)

    selected:  List[int] = []
    remaining: List[int] = list(range(n))

    for _ in range(k):
        best_idx   = -1
        best_score = -float("inf")

        for idx in remaining:
            relevance = candidate_scores[idx]

            # Redundansi = kesamaan maksimum dengan chunk yang sudah terpilih
            if not selected:
                redundancy = 0.0
            else:
                redundancy = max(
                    _cosine_sim(candidate_vectors[idx], candidate_vectors[sel])
                    for sel in selected
                )

            mmr_score = lambda_mmr * relevance - (1.0 - lambda_mmr) * redundancy

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx   = idx

        if best_idx == -1:
            break

        selected.append(best_idx)
        remaining.remove(best_idx)

    return selected


def _compute_final_mmr_scores(
    candidate_vectors:  np.ndarray,
    candidate_scores:   List[float],
    selected_positions: List[int],
    lambda_mmr:         float,
) -> Dict[int, float]:
    """
    Hitung skor MMR aktual per posisi (untuk ditampilkan di UI).
    Setiap chunk dinilai berdasarkan redundansinya terhadap semua
    chunk yang dipilih sebelumnya.
    """
    result: Dict[int, float] = {}
    already: List[int] = []

    for rank, pos in enumerate(selected_positions):
        rel = candidate_scores[pos]
        red = max(
            (_cosine_sim(candidate_vectors[pos], candidate_vectors[p]) for p in already),
            default=0.0,
        )
        result[rank] = lambda_mmr * rel - (1.0 - lambda_mmr) * red
        already.append(pos)

    return result


# ─── DB helper ────────────────────────────────────────────────────────────────

class _DBChunk:
    __slots__ = ("chunk_id", "content", "source", "meta_data")
    def __init__(self, chunk_id, content, source, meta_data):
        self.chunk_id = chunk_id
        self.content  = content
        self.source   = source
        self.meta_data = meta_data


def _fetch_chunks(chunk_ids: List[int]) -> List[_DBChunk]:
    if not chunk_ids:
        return []
    with db_session() as session:
        chunks  = session.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
        doc_ids = list({c.document_id for c in chunks})
        docs    = session.query(Document).filter(Document.id.in_(doc_ids)).all()
        doc_map = {d.id: d.original_name or d.filename for d in docs}
        return [
            _DBChunk(
                chunk_id = c.id,
                content  = c.content,
                source   = doc_map.get(c.document_id, "Unknown"),
                meta_data = c.meta_data or {},
            )
            for c in chunks
        ]


# ─── Retriever ────────────────────────────────────────────────────────────────

class RAGRetriever:
    """
    Retriever dengan dukungan MMR (Maximal Marginal Relevance).

    Parameters
    ----------
    k : int
        Jumlah chunk yang dikembalikan (default dari settings: 5).
    use_mmr : bool
        True  → MMR aktif (default)
        False → pure similarity ranking
    lambda_mmr : float
        0.0 = pure diversity · 0.5 = seimbang (default) · 1.0 = pure relevance
    fetch_k : int
        Jumlah candidate yang diambil dari FAISS sebelum MMR dijalankan.
        Harus ≥ k. Lebih besar = MMR punya lebih banyak pilihan.
        Default = max(k * 4, 20).
    """

    def __init__(
        self,
        k:          int   = FAISS_K,
        use_mmr:    bool  = MMR_ENABLED,
        lambda_mmr: float = MMR_LAMBDA,
        fetch_k:    int   = None,
    ):
        self.k          = k
        self.use_mmr    = use_mmr
        self.lambda_mmr = max(0.0, min(1.0, lambda_mmr))
        self.fetch_k    = fetch_k if fetch_k else max(k * 4, MMR_FETCH_K)
        self.embedder   = Embedder()
        self.store      = FAISSStore()

    # ── Public API ────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query:      str,
        k:          int            = None,
        use_mmr:    Optional[bool] = None,
        lambda_mmr: Optional[float]= None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve top-k chunk untuk query.

        Parameter per-call akan meng-override nilai instance jika diberikan.
        """
        k          = k          if k          is not None else self.k
        use_mmr    = use_mmr    if use_mmr    is not None else self.use_mmr
        lambda_mmr = lambda_mmr if lambda_mmr is not None else self.lambda_mmr
        lambda_mmr = max(0.0, min(1.0, lambda_mmr))

        if self.store.total_vectors == 0:
            logger.warning("FAISS index kosong — belum ada dokumen yang diindeks.")
            return []

        # Embed query
        query_vector = self.embedder.encode_query(query)

        if use_mmr:
            return self._retrieve_mmr(query, query_vector, k, lambda_mmr)
        else:
            return self._retrieve_standard(query, query_vector, k)

    def format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Format chunk terpilih menjadi string konteks untuk LLM."""
        if not chunks:
            return "Tidak ada informasi yang relevan ditemukan."
        parts = [
            f"[Sumber {i}: {c.source}]\n{c.content}"
            for i, c in enumerate(chunks, 1)
        ]
        return "\n\n---\n\n".join(parts)

    # ── Standard retrieval ────────────────────────────────────────────────────

    def _retrieve_standard(
        self,
        query:        str,
        query_vector: np.ndarray,
        k:            int,
    ) -> List[RetrievedChunk]:

        faiss_results = self.store.search(query_vector, k=k)
        if not faiss_results:
            return []

        chunk_ids = [cid   for cid, _  in faiss_results]
        score_map = {cid: sc for cid, sc in faiss_results}
        db_chunks = _fetch_chunks(chunk_ids)

        retrieved = [
            RetrievedChunk(
                chunk_id  = c.chunk_id,
                content   = c.content,
                score     = score_map.get(c.chunk_id, 0.0),
                mmr_score = score_map.get(c.chunk_id, 0.0),
                source    = c.source,
                meta_data  = c.meta_data,
            )
            for c in db_chunks
        ]
        retrieved.sort(key=lambda x: x.score, reverse=True)
        logger.debug(f"[Standard] {len(retrieved)} chunks | '{query[:50]}'")
        return retrieved

    # ── MMR retrieval ─────────────────────────────────────────────────────────

    def _retrieve_mmr(
        self,
        query:        str,
        query_vector: np.ndarray,
        k:            int,
        lambda_mmr:   float,
    ) -> List[RetrievedChunk]:

        # 1. Ambil candidate pool besar dari FAISS
        fetch_k = max(self.fetch_k, k * 4, 20)
        faiss_results = self.store.search(query_vector, k=fetch_k)
        if not faiss_results:
            return []

        candidate_ids    = [cid for cid, _  in faiss_results]
        candidate_scores = [sc  for _,  sc  in faiss_results]

        # 2. Rekonstruksi vektor embedding candidate dari FAISS
        #    (dibutuhkan untuk menghitung similarity antar-chunk)
        candidate_vectors = self.store.get_vectors_by_chunk_ids(candidate_ids)

        if candidate_vectors is None or len(candidate_vectors) == 0:
            logger.warning("[MMR] Gagal rekonstruksi vektor → fallback ke standard")
            return self._retrieve_standard(query, query_vector, k)

        # Pastikan jumlah vektor = jumlah candidate (FAISS mungkin skip invalid)
        n = min(len(candidate_ids), len(candidate_vectors), len(candidate_scores))
        candidate_ids    = candidate_ids[:n]
        candidate_scores = candidate_scores[:n]
        candidate_vectors = candidate_vectors[:n]

        # 3. Jalankan MMR
        selected_positions = _mmr_select(
            query_vector      = query_vector,
            candidate_vectors = candidate_vectors,
            candidate_scores  = candidate_scores,
            k                 = k,
            lambda_mmr        = lambda_mmr,
        )

        # 4. Hitung skor MMR final untuk tampilan UI
        mmr_scores = _compute_final_mmr_scores(
            candidate_vectors, candidate_scores,
            selected_positions, lambda_mmr,
        )

        # 5. Ambil konten dari DB
        selected_ids = [candidate_ids[p] for p in selected_positions]
        db_chunks    = _fetch_chunks(selected_ids)
        chunk_map    = {c.chunk_id: c for c in db_chunks}

        retrieved: List[RetrievedChunk] = []
        for rank, (pos, chunk_id) in enumerate(zip(selected_positions, selected_ids)):
            c = chunk_map.get(chunk_id)
            if not c:
                continue
            retrieved.append(RetrievedChunk(
                chunk_id  = chunk_id,
                content   = c.content,
                score     = candidate_scores[pos],
                mmr_score = mmr_scores.get(rank, candidate_scores[pos]),
                source    = c.source,
                meta_data  = c.meta_data,
            ))

        logger.debug(
            f"[MMR λ={lambda_mmr}] {len(retrieved)}/{n} candidates "
            f"| '{query[:50]}'"
        )
        return retrieved
