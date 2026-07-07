"""
tests/test_retriever_mmr.py

Unit test untuk rag/retrieval/retriever.py — fokus pada algoritma MMR murni
(tidak menyentuh FAISS atau database, hanya fungsi matematis):
- _cosine_sim()              : cosine similarity antar vektor
- _mmr_select()               : algoritma pemilihan chunk MMR
- _compute_final_mmr_scores() : perhitungan skor MMR final untuk tampilan UI
- RetrievedChunk              : data class hasil retrieval
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

from rag.retrieval.retriever import (
    _cosine_sim, _mmr_select, _compute_final_mmr_scores, RetrievedChunk,
)


# ─── _cosine_sim() ─────────────────────────────────────────────────────────────

class TestCosineSim:
    def test_identical_vectors_similarity_1(self):
        v = np.array([1.0, 2.0, 3.0])
        assert abs(_cosine_sim(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors_similarity_0(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert abs(_cosine_sim(a, b)) < 1e-6

    def test_opposite_vectors_similarity_negative_1(self):
        a = np.array([1.0, 0.0])
        b = np.array([-1.0, 0.0])
        assert abs(_cosine_sim(a, b) - (-1.0)) < 1e-6

    def test_zero_vector_returns_zero_not_nan(self):
        a = np.zeros(5)
        b = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = _cosine_sim(a, b)
        assert result == 0.0
        assert not np.isnan(result)

    def test_both_zero_vectors(self):
        a = np.zeros(5)
        b = np.zeros(5)
        assert _cosine_sim(a, b) == 0.0

    def test_similarity_is_scale_invariant(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([2.0, 4.0, 6.0])
        assert abs(_cosine_sim(a, b) - 1.0) < 1e-6


# ─── _mmr_select() ─────────────────────────────────────────────────────────────

class TestMMRSelect:
    def _make_realistic_vectors(self, seed=42, dim=384):
        """
        Skenario candidate vector realistis seperti embedding sentence-transformer
        asli: c0 & c1 near-duplicate (sim tinggi), c2-c4 makin berbeda dari query.
        """
        rng = np.random.RandomState(seed)
        q_base = rng.randn(dim)
        q_base /= np.linalg.norm(q_base)

        c0 = q_base + rng.randn(dim) * 0.05
        c0 /= np.linalg.norm(c0)

        c1 = c0 + rng.randn(dim) * 0.02
        c1 /= np.linalg.norm(c1)

        c2 = q_base + rng.randn(dim) * 0.3
        c2 /= np.linalg.norm(c2)

        c3 = q_base + rng.randn(dim) * 0.6
        c3 /= np.linalg.norm(c3)

        c4 = q_base + rng.randn(dim) * 1.0
        c4 /= np.linalg.norm(c4)

        candidates = np.array([c0, c1, c2, c3, c4])
        scores = [_cosine_sim(q_base, c) for c in candidates]
        return q_base, candidates, scores

    def test_returns_k_indices(self):
        q, cands, scores = self._make_realistic_vectors()
        result = _mmr_select(q, cands, scores, k=3, lambda_mmr=0.5)
        assert len(result) == 3

    def test_returns_fewer_if_k_exceeds_candidates(self):
        q, cands, scores = self._make_realistic_vectors()
        result = _mmr_select(q, cands, scores, k=100, lambda_mmr=0.5)
        assert len(result) == len(scores)

    def test_first_selection_is_most_relevant(self):
        q, cands, scores = self._make_realistic_vectors()
        result = _mmr_select(q, cands, scores, k=3, lambda_mmr=0.5)
        most_relevant_idx = int(np.argmax(scores))
        assert result[0] == most_relevant_idx

    def test_avoids_near_duplicate_with_balanced_lambda(self):
        """
        Skenario kunci: c0 dan c1 near-duplicate (sim > 0.85).
        Dengan lambda=0.5, MMR seharusnya tidak memilih keduanya bersamaan.
        """
        q, cands, scores = self._make_realistic_vectors()
        sim_c0_c1 = _cosine_sim(cands[0], cands[1])
        assert sim_c0_c1 > 0.85

        result = _mmr_select(q, cands, scores, k=3, lambda_mmr=0.5)
        assert not (0 in result and 1 in result), (
            "MMR dengan lambda=0.5 seharusnya menghindari memilih dua chunk "
            "yang sangat mirip satu sama lain (redundan)"
        )

    def test_lambda_1_equals_pure_relevance_ranking(self):
        q, cands, scores = self._make_realistic_vectors()
        k = 3
        mmr_result = _mmr_select(q, cands, scores, k=k, lambda_mmr=1.0)
        standard_result = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:k]
        assert set(mmr_result) == set(standard_result)

    def test_lambda_0_maximizes_diversity_avoids_redundant_pair(self):
        q, cands, scores = self._make_realistic_vectors()
        result = _mmr_select(q, cands, scores, k=3, lambda_mmr=0.0)
        assert not (0 in result and 1 in result)

    def test_empty_candidates_returns_empty_list(self):
        q = np.random.randn(384)
        result = _mmr_select(q, np.array([]).reshape(0, 384), [], k=5, lambda_mmr=0.5)
        assert result == []

    def test_k_zero_returns_empty_list(self):
        q, cands, scores = self._make_realistic_vectors()
        result = _mmr_select(q, cands, scores, k=0, lambda_mmr=0.5)
        assert result == []

    def test_single_candidate(self):
        q, cands, scores = self._make_realistic_vectors()
        result = _mmr_select(q, cands[:1], scores[:1], k=3, lambda_mmr=0.5)
        assert result == [0]

    def test_no_duplicate_indices_in_result(self):
        q, cands, scores = self._make_realistic_vectors()
        result = _mmr_select(q, cands, scores, k=5, lambda_mmr=0.5)
        assert len(result) == len(set(result))


# ─── _compute_final_mmr_scores() ───────────────────────────────────────────────

class TestComputeFinalMMRScores:
    def test_first_rank_score_equals_relevance_only(self):
        cands = np.array([[1.0, 0.0], [0.0, 1.0]])
        scores = [0.9, 0.5]
        selected_positions = [0, 1]
        lam = 0.5

        result = _compute_final_mmr_scores(cands, scores, selected_positions, lam)
        expected_rank0 = lam * scores[0] - (1 - lam) * 0.0
        assert abs(result[0] - expected_rank0) < 1e-6

    def test_scores_dict_has_entry_per_selected(self):
        cands = np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]])
        scores = [0.9, 0.5, 0.3]
        selected_positions = [0, 1, 2]
        result = _compute_final_mmr_scores(cands, scores, selected_positions, 0.5)
        assert len(result) == 3
        assert set(result.keys()) == {0, 1, 2}


# ─── RetrievedChunk ────────────────────────────────────────────────────────────

class TestRetrievedChunk:
    def test_to_dict_contains_all_fields(self):
        chunk = RetrievedChunk(
            chunk_id=1, content="isi chunk", score=0.85, mmr_score=0.72,
            source="dokumen.pdf", metadata={"page": 1},
        )
        d = chunk.to_dict()
        assert d["chunk_id"] == 1
        assert d["content"] == "isi chunk"
        assert d["score"] == 0.85
        assert d["mmr_score"] == 0.72
        assert d["source"] == "dokumen.pdf"
        assert d["metadata"] == {"page": 1}

    def test_to_dict_rounds_scores(self):
        chunk = RetrievedChunk(
            chunk_id=1, content="x", score=0.123456789, mmr_score=0.987654321,
            source="x.pdf", metadata={},
        )
        d = chunk.to_dict()
        assert d["score"] == round(0.123456789, 4)
        assert d["mmr_score"] == round(0.987654321, 4)
