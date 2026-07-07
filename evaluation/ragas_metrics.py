"""
evaluation/ragas_metrics.py

Implementasi native empat metrik inti RAGAS (Retrieval-Augmented Generation
Assessment), mengikuti formula resmi dari paper RAGAS (Es et al., 2023),
tanpa bergantung pada library `ragas` yang memiliki dependency chain rapuh
(konflik versi langchain-community yang sering berubah di lingkungan sandbox).

Setiap metrik memanggil LLM (via OpenRouter, model yang sama dengan yang
dipakai chatbot produksi: openai/gpt-oss-120b) sebagai "judge" untuk menilai
kualitas jawaban RAG secara terstruktur.

=== Empat Metrik ===

1. FAITHFULNESS (0.0 - 1.0)
   "Apakah jawaban benar-benar didukung oleh konteks yang di-retrieve?"
   Formula: jumlah klaim yang didukung konteks / total klaim dalam jawaban.
   Langkah: (a) pecah jawaban jadi klaim atomik, (b) untuk tiap klaim, LLM
   menilai apakah klaim tersebut bisa diverifikasi dari konteks (Yes/No).

2. ANSWER RELEVANCY (0.0 - 1.0)
   "Apakah jawaban relevan dan tidak melenceng dari pertanyaan?"
   Formula: rata-rata cosine similarity antara pertanyaan asli dan beberapa
   pertanyaan yang di-generate ulang oleh LLM dari jawaban (reverse-engineer).

3. CONTEXT PRECISION (0.0 - 1.0)
   "Apakah chunk yang di-retrieve relevan, atau ada yang 'sampah'?"
   Formula: precision@k dengan pembobotan berdasarkan posisi (chunk relevan
   di posisi atas mendapat bobot lebih besar -- mirip average precision).

4. CONTEXT RECALL (0.0 - 1.0)
   "Apakah ground truth bisa sepenuhnya dijawab dari konteks yang di-retrieve?"
   Formula: jumlah kalimat ground truth yang didukung konteks / total kalimat
   ground truth. Mengukur apakah retriever 'melewatkan' info penting.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL,
    OPENROUTER_SITE_URL, OPENROUTER_APP_NAME, LLM_MODEL,
    RAGAS_JUDGE_MODEL, RAGAS_JUDGE_TEMPERATURE, RAGAS_JUDGE_MAX_TOKENS,
)


def _call_judge_llm(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    """Panggil LLM (via OpenRouter) sebagai judge, kembalikan teks mentah."""
    from openai import OpenAI
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": OPENROUTER_SITE_URL,
            "X-Title": OPENROUTER_APP_NAME,
        },
    )
    response = client.chat.completions.create(
        model=RAGAS_JUDGE_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=max_tokens or RAGAS_JUDGE_MAX_TOKENS,
        temperature=RAGAS_JUDGE_TEMPERATURE,
    )
    return response.choices[0].message.content.strip()


def _parse_json_response(raw: str):
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def _cosine_similarity(a, b) -> float:
    import numpy as np
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


# ─── 1. FAITHFULNESS ───────────────────────────────────────────────────────────

_FAITHFULNESS_EXTRACT_PROMPT = """Berikut adalah sebuah pertanyaan dan jawaban.
Pecah JAWABAN menjadi daftar klaim/pernyataan atomik (satu fakta sederhana per klaim).
Setiap klaim harus berdiri sendiri dan dapat diverifikasi secara independen.

Pertanyaan: {question}
Jawaban: {answer}

Kembalikan HANYA JSON array berisi string klaim, contoh:
["klaim pertama", "klaim kedua", "klaim ketiga"]
"""

_FAITHFULNESS_VERIFY_PROMPT = """Berikut adalah sebuah klaim dan konteks/dokumen referensi.
Tentukan apakah klaim tersebut didukung oleh konteks (informasi dalam klaim
benar-benar ada atau bisa disimpulkan langsung dari konteks).

Konteks:
{context}

Klaim: {claim}

Jawab HANYA dengan JSON: {{"supported": true}} atau {{"supported": false}}
"""


def faithfulness(question: str, answer: str, contexts: List[str]) -> dict:
    """
    Mengukur seberapa besar proporsi klaim dalam jawaban yang didukung
    oleh konteks yang di-retrieve. Skor tinggi = jawaban tidak mengarang.
    """
    if not answer.strip():
        return {"score": 0.0, "claims": [], "detail": "Jawaban kosong"}

    combined_context = "\n\n".join(contexts) if contexts else "(tidak ada konteks)"

    raw = _call_judge_llm(
        "Kamu adalah sistem ekstraksi klaim untuk evaluasi RAG. Kembalikan HANYA JSON array.",
        _FAITHFULNESS_EXTRACT_PROMPT.format(question=question, answer=answer),
    )
    try:
        claims = _parse_json_response(raw)
        if not isinstance(claims, list) or not claims:
            return {"score": 0.0, "claims": [], "detail": "Gagal ekstrak klaim"}
    except (json.JSONDecodeError, ValueError):
        return {"score": 0.0, "claims": [], "detail": f"Parse error: {raw[:200]}"}

    results = []
    for claim in claims:
        try:
            raw_verify = _call_judge_llm(
                "Kamu adalah verifikator fakta untuk evaluasi RAG. Kembalikan HANYA JSON.",
                _FAITHFULNESS_VERIFY_PROMPT.format(context=combined_context, claim=claim),
            )
            verdict = _parse_json_response(raw_verify)
            supported = bool(verdict.get("supported", False))
        except (json.JSONDecodeError, ValueError, AttributeError):
            supported = False
        results.append({"claim": claim, "supported": supported})

    n_supported = sum(1 for r in results if r["supported"])
    score = n_supported / len(claims) if claims else 0.0

    return {"score": round(score, 4), "claims": results, "n_total": len(claims), "n_supported": n_supported}


# ─── 2. ANSWER RELEVANCY ───────────────────────────────────────────────────────

_RELEVANCY_REVERSE_PROMPT = """Berdasarkan jawaban berikut, buat {n} variasi pertanyaan
yang kemungkinan besar menghasilkan jawaban tersebut. Pertanyaan harus singkat dan jelas.

Jawaban: {answer}

Kembalikan HANYA JSON array berisi string pertanyaan, contoh:
["pertanyaan 1", "pertanyaan 2", "pertanyaan 3"]
"""


def answer_relevancy(question: str, answer: str, embedder, n_questions: int = 3) -> dict:
    """
    Mengukur relevansi jawaban dengan men-generate ulang beberapa pertanyaan
    dari jawaban (reverse-engineering), lalu menghitung cosine similarity
    rata-rata dengan pertanyaan asli menggunakan embedder yang sama dengan
    yang dipakai sistem produksi.

    embedder: objek dengan method encode_query(text) -> np.ndarray
    """
    if not answer.strip():
        return {"score": 0.0, "generated_questions": [], "detail": "Jawaban kosong"}

    raw = _call_judge_llm(
        "Kamu adalah generator pertanyaan untuk evaluasi RAG. Kembalikan HANYA JSON array.",
        _RELEVANCY_REVERSE_PROMPT.format(answer=answer, n=n_questions),
    )
    try:
        generated_questions = _parse_json_response(raw)
        if not isinstance(generated_questions, list) or not generated_questions:
            return {"score": 0.0, "generated_questions": [], "detail": "Gagal generate pertanyaan"}
    except (json.JSONDecodeError, ValueError):
        return {"score": 0.0, "generated_questions": [], "detail": f"Parse error: {raw[:200]}"}

    original_vec = embedder.encode_query(question)
    similarities = []
    for gq in generated_questions:
        gq_vec = embedder.encode_query(gq)
        sim = _cosine_similarity(original_vec, gq_vec)
        similarities.append(sim)

    score = sum(similarities) / len(similarities) if similarities else 0.0

    return {
        "score": round(max(0.0, score), 4),
        "generated_questions": generated_questions,
        "similarities": [round(s, 4) for s in similarities],
    }


# ─── 3. CONTEXT PRECISION ──────────────────────────────────────────────────────

_PRECISION_RELEVANCE_PROMPT = """Tentukan apakah POTONGAN KONTEKS berikut relevan
untuk menjawab PERTANYAAN.

Pertanyaan: {question}

Potongan Konteks: {context_chunk}

Jawab HANYA dengan JSON: {{"relevant": true}} atau {{"relevant": false}}
"""


def context_precision(question: str, contexts: List[str]) -> dict:
    """
    Mengukur proporsi chunk yang di-retrieve yang benar-benar relevan,
    dengan pembobotan posisi (Average Precision) -- chunk relevan yang
    muncul di posisi lebih atas memberi kontribusi skor lebih besar.
    """
    if not contexts:
        return {"score": 0.0, "relevance_flags": [], "detail": "Tidak ada konteks"}

    relevance_flags = []
    for ctx in contexts:
        try:
            raw = _call_judge_llm(
                "Kamu adalah evaluator relevansi konteks untuk RAG. Kembalikan HANYA JSON.",
                _PRECISION_RELEVANCE_PROMPT.format(question=question, context_chunk=ctx),
            )
            verdict = _parse_json_response(raw)
            relevant = bool(verdict.get("relevant", False))
        except (json.JSONDecodeError, ValueError, AttributeError):
            relevant = False
        relevance_flags.append(relevant)

    precisions_at_k = []
    n_relevant_so_far = 0
    for k, is_relevant in enumerate(relevance_flags, start=1):
        if is_relevant:
            n_relevant_so_far += 1
            precisions_at_k.append(n_relevant_so_far / k)

    score = sum(precisions_at_k) / len(precisions_at_k) if precisions_at_k else 0.0

    return {
        "score": round(score, 4),
        "relevance_flags": relevance_flags,
        "n_relevant": sum(relevance_flags),
        "n_total": len(contexts),
    }


# ─── 4. CONTEXT RECALL ─────────────────────────────────────────────────────────

_RECALL_DECOMPOSE_PROMPT = """Pecah GROUND TRUTH berikut menjadi daftar kalimat/klaim atomik.

Ground Truth: {ground_truth}

Kembalikan HANYA JSON array berisi string klaim, contoh:
["klaim pertama", "klaim kedua"]
"""

_RECALL_ATTRIBUTION_PROMPT = """Tentukan apakah KLAIM berikut dapat diatribusikan
(didukung/dapat ditemukan) di dalam KONTEKS yang diberikan.

Konteks:
{context}

Klaim: {claim}

Jawab HANYA dengan JSON: {{"attributed": true}} atau {{"attributed": false}}
"""


def context_recall(ground_truth: str, contexts: List[str]) -> dict:
    """
    Mengukur seberapa besar proporsi informasi dalam ground truth yang
    bisa ditemukan dalam konteks yang di-retrieve. Skor rendah berarti
    retriever 'melewatkan' informasi penting yang seharusnya ada.
    """
    if not ground_truth.strip():
        return {"score": 0.0, "claims": [], "detail": "Ground truth kosong"}

    combined_context = "\n\n".join(contexts) if contexts else "(tidak ada konteks)"

    raw = _call_judge_llm(
        "Kamu adalah sistem dekomposisi klaim untuk evaluasi RAG. Kembalikan HANYA JSON array.",
        _RECALL_DECOMPOSE_PROMPT.format(ground_truth=ground_truth),
    )
    try:
        claims = _parse_json_response(raw)
        if not isinstance(claims, list) or not claims:
            return {"score": 0.0, "claims": [], "detail": "Gagal dekomposisi ground truth"}
    except (json.JSONDecodeError, ValueError):
        return {"score": 0.0, "claims": [], "detail": f"Parse error: {raw[:200]}"}

    results = []
    for claim in claims:
        try:
            raw_attr = _call_judge_llm(
                "Kamu adalah evaluator atribusi klaim untuk RAG. Kembalikan HANYA JSON.",
                _RECALL_ATTRIBUTION_PROMPT.format(context=combined_context, claim=claim),
            )
            verdict = _parse_json_response(raw_attr)
            attributed = bool(verdict.get("attributed", False))
        except (json.JSONDecodeError, ValueError, AttributeError):
            attributed = False
        results.append({"claim": claim, "attributed": attributed})

    n_attributed = sum(1 for r in results if r["attributed"])
    score = n_attributed / len(claims) if claims else 0.0

    return {
        "score": round(score, 4), "claims": results,
        "n_total": len(claims), "n_attributed": n_attributed,
    }


@dataclass
class RagasResult:
    question: str
    category: str
    difficulty: str
    faithfulness_score: float
    answer_relevancy_score: float
    context_precision_score: float
    context_recall_score: float
    raw_details: dict = field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        scores = [
            self.faithfulness_score, self.answer_relevancy_score,
            self.context_precision_score, self.context_recall_score,
        ]
        return round(sum(scores) / len(scores), 4)

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "category": self.category,
            "difficulty": self.difficulty,
            "faithfulness": self.faithfulness_score,
            "answer_relevancy": self.answer_relevancy_score,
            "context_precision": self.context_precision_score,
            "context_recall": self.context_recall_score,
            "overall": self.overall_score,
        }
