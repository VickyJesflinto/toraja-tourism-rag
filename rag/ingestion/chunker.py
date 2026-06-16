"""
rag/ingestion/chunker.py
Splits large text into overlapping chunks for better RAG retrieval.
"""
from typing import List
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    meta_data: Dict[str, Any] = field(default_factory=dict)


class TextChunker:
    """
    Splits text into overlapping fixed-size character windows.
    Falls back to sentence-aware splitting when possible.
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap    = overlap

    def chunk(self, text: str, base_meta_data: Dict[str, Any] = None) -> List[TextChunk]:
        """Main entry: returns list of TextChunk."""
        meta_data = base_meta_data or {}
        if len(text) <= self.chunk_size:
            return [TextChunk(content=text, chunk_index=0, meta_data=meta_data)]

        sentences = self._split_sentences(text)
        return self._merge_sentences(sentences, meta_data)

    def _split_sentences(self, text: str) -> List[str]:
        """Naive sentence splitter; handles Indonesian text well."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _merge_sentences(self, sentences: List[str], meta_data: Dict[str, Any]) -> List[TextChunk]:
        chunks = []
        current_chunk: List[str] = []
        current_len = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_len + sentence_len > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(TextChunk(
                    content=" ".join(current_chunk),
                    chunk_index=chunk_index,
                    meta_data=dict(meta_data)
                ))
                chunk_index += 1

                # Overlap: keep last N chars worth of sentences
                overlap_chunks: List[str] = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) <= self.overlap:
                        overlap_chunks.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break
                current_chunk = overlap_chunks
                current_len   = overlap_len

            current_chunk.append(sentence)
            current_len += sentence_len

        if current_chunk:
            chunks.append(TextChunk(
                content=" ".join(current_chunk),
                chunk_index=chunk_index,
                meta_data=dict(meta_data)
            ))

        return chunks
