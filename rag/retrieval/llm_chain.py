"""
rag/retrieval/llm_chain.py
LLM chain: build prompt with retrieved context → call gpt-oss-120b via OpenRouter → return answer.

OpenRouter menggunakan OpenAI-compatible API, sehingga kita tetap pakai
library `openai` namun dengan base_url dan api_key yang diarahkan ke OpenRouter.
Dokumentasi: https://openrouter.ai/docs
"""
import time
from config.settings import FAISS_K, MMR_ENABLED, MMR_LAMBDA, MMR_FETCH_K
from typing import List, Dict, Any, Tuple
from loguru import logger
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.settings import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL,
    OPENROUTER_SITE_URL, OPENROUTER_APP_NAME,
    LLM_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE,
    MMR_ENABLED, MMR_LAMBDA, MMR_FETCH_K,
)
from rag.retrieval.retriever import RAGRetriever, RetrievedChunk


SYSTEM_PROMPT = """Kamu adalah asisten AI pariwisata Toraja yang berpengetahuan luas.
Kamu membantu pengunjung dan masyarakat mendapatkan informasi akurat tentang:
- Destinasi wisata, budaya, dan tradisi Toraja
- Akomodasi, kuliner, dan fasilitas wisata
- Event budaya dan kalender wisata
- Aksesibilitas dan transportasi

Gunakan HANYA informasi dari konteks yang diberikan.
Jika informasi tidak tersedia di konteks, katakan dengan jujur bahwa kamu tidak memiliki datanya.
Jawab dalam Bahasa Indonesia yang ramah, informatif, dan mudah dipahami.
Sertakan fakta spesifik jika tersedia (harga, lokasi, waktu, dll.)."""


class LLMChain:
    """
    Handles the full RAG chat pipeline:
    query → retrieve → build prompt → LLM (via OpenRouter) → response

    OpenRouter menerima request OpenAI-compatible.
    Header tambahan yang dikirim:
      HTTP-Referer : OPENROUTER_SITE_URL  (untuk identifikasi app di openrouter.ai)
      X-Title      : OPENROUTER_APP_NAME  (nama app yang muncul di dashboard OpenRouter)
    """

    def __init__(self):
        self.retriever = RAGRetriever(
            use_mmr    = MMR_ENABLED,
            lambda_mmr = MMR_LAMBDA,
            fetch_k    = MMR_FETCH_K,
        )
        self._client = None

    def _get_client(self):
        """Lazy-init OpenAI client yang diarahkan ke OpenRouter."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=OPENROUTER_API_KEY,
                base_url=OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": OPENROUTER_SITE_URL,
                    "X-Title":      OPENROUTER_APP_NAME,
                },
            )
            logger.info(f"OpenRouter client initialized | model: {LLM_MODEL}")
        return self._client

    def chat(
        self,
        query:      str,
        history:    List[Dict[str, str]] = None,
        k:          int   = FAISS_K,
        use_mmr:    bool  = None,
        lambda_mmr: float = None,
    ) -> Tuple[str, List[RetrievedChunk], int, float]:
        """
        Full RAG chat.
        Returns: (answer, retrieved_chunks, tokens_used, response_time_seconds)
        """
        t_start = time.time()

        # 1. Retrieve context
        chunks  = self.retriever.retrieve(query, k=k, use_mmr=use_mmr, lambda_mmr=lambda_mmr)
        context = self.retriever.format_context(chunks)

        # 2. Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Sertakan history terakhir 6 turn
        if history:
            for turn in history[-6:]:
                messages.append(turn)

        messages.append({
            "role": "user",
            "content": f"Konteks informasi:\n{context}\n\nPertanyaan: {query}",
        })

        # 3. Call LLM via OpenRouter
        try:
            client   = self._get_client()
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
            )
            answer      = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
        except Exception as e:
            logger.error(f"OpenRouter LLM call failed: {e}")
            answer      = f"Maaf, terjadi kesalahan saat menghubungi LLM: {str(e)}"
            tokens_used = 0

        elapsed = round(time.time() - t_start, 2)
        logger.info(
            f"Chat selesai | waktu: {elapsed}s | token: {tokens_used} | "
            f"chunks: {len(chunks)} | model: {LLM_MODEL}"
        )
        return answer, chunks, tokens_used, elapsed

    def stream_chat(
        self,
        query:      str,
        history:    List[Dict[str, str]] = None,
        k:          int   = FAISS_K,
        use_mmr:    bool  = None,
        lambda_mmr: float = None,
    ):
        """
        Streaming version — yields text delta sebagai generator.
        Yield pertama: dict {'sources': [...]} berisi chunk yang digunakan.
        Yield berikutnya: dict {'text': '<delta>'} untuk setiap token.
        """
        chunks  = self.retriever.retrieve(query, k=k, use_mmr=use_mmr, lambda_mmr=lambda_mmr)
        context = self.retriever.format_context(chunks)

        # Kirim sumber terlebih dahulu
        yield {"sources": [c.to_dict() for c in chunks]}

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            for turn in history[-6:]:
                messages.append(turn)

        messages.append({
            "role": "user",
            "content": f"Konteks informasi:\n{context}\n\nPertanyaan: {query}",
        })

        try:
            client = self._get_client()
            stream = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
                stream=True,
            )
            for event in stream:
                delta = event.choices[0].delta.content
                if delta:
                    yield {"text": delta}
        except Exception as e:
            logger.error(f"OpenRouter stream error: {e}")
            yield {"text": f"\n\n[Error: {str(e)}]"}
