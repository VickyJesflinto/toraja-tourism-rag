"""
rag/ingestion/indexer.py
Orchestrates: parse → extract structured data → chunk → embed → FAISS → save to DB

Pipeline lengkap:
  1. Parse dokumen ke teks mentah
  2. Ekstrak data terstruktur via LLM → simpan ke tabel pariwisata MySQL
     (tourist_attractions, visitor_statistics, accommodations, dst.)
  3. Chunk teks untuk RAG
  4. Embed chunks dengan sentence-transformer
  5. Simpan ke FAISS + tabel document_chunks
"""
from pathlib import Path
from typing import List
from loguru import logger
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rag.ingestion.document_parser import DocumentParser
from rag.ingestion.chunker import TextChunker
from rag.ingestion.data_extractor import extract_and_save, ExtractionResult
from rag.embeddings.embedder import Embedder
from rag.retrieval.faiss_store import FAISSStore
from database.connection import db_session
from database.models import Document, DocumentChunk


class DocumentIndexer:
    """
    Full pipeline to index a document file into the RAG system.

    Selain diindeks ke FAISS untuk chatbot, dokumen juga diproses untuk
    mengekstrak data terstruktur pariwisata (destinasi, statistik, akomodasi,
    event, infrastruktur) dan menyimpannya ke tabel MySQL sehingga otomatis
    muncul di Dashboard dan halaman Data Pariwisata.

    Usage:
        indexer = DocumentIndexer()
        n_chunks, extraction = indexer.index_document(file_path, document_id)
    """

    def __init__(self):
        self.parser   = DocumentParser()
        self.chunker  = TextChunker(chunk_size=1000, overlap=200)
        self.embedder = Embedder()
        self.store    = FAISSStore()

    def index_document(
        self,
        file_path: str | Path,
        document_id: int,
        extract_data: bool = True,
    ) -> tuple[int, ExtractionResult | None]:
        """
        Parse, ekstrak data, chunk, embed, dan simpan dokumen.

        Args:
            file_path:    Path file yang akan diindeks.
            document_id:  ID record di tabel `documents`.
            extract_data: Jika True, jalankan ekstraksi data terstruktur via LLM.

        Returns:
            (n_chunks_indexed, extraction_result)
            extraction_result adalah None jika extract_data=False.
        """
        path = Path(file_path)
        self._update_status(document_id, "processing")

        try:
            # ── 1. Parse dokumen ──────────────────────────────────────────────
            parsed_chunks = self.parser.parse(path)
            logger.info(f"Parsed {len(parsed_chunks)} raw sections from {path.name}")

            if not parsed_chunks:
                raise ValueError("No text content extracted from document.")

            # ── 2. Ekstraksi data terstruktur (opsional, via LLM) ─────────────
            extraction_result: ExtractionResult | None = None
            if extract_data:
                logger.info(f"[indexer] Menjalankan ekstraksi data terstruktur untuk: {path.name}")
                # Gabungkan semua teks sebagai konteks untuk LLM
                # Batasi total agar tidak terlalu panjang
                combined_text = "\n\n".join(pc.content for pc in parsed_chunks)
                if len(combined_text) > 12_000:
                    combined_text = combined_text[:12_000]
                    logger.warning("[indexer] Teks dipotong ke 12.000 karakter untuk ekstraksi LLM")

                try:
                    extraction_result = extract_and_save(combined_text)
                    if extraction_result.total > 0:
                        logger.success(
                            f"[indexer] Data terekstrak: {extraction_result.summary()}"
                        )
                    else:
                        logger.info("[indexer] Tidak ada data terstruktur yang ditemukan di dokumen ini.")
                except Exception as ex:
                    logger.warning(f"[indexer] Ekstraksi data gagal (non-fatal): {ex}")
                    extraction_result = ExtractionResult()
                    extraction_result.errors.append(str(ex))

            # ── 3. Chunking untuk RAG ─────────────────────────────────────────
            all_chunks = []
            for pc in parsed_chunks:
                sub = self.chunker.chunk(pc.content, pc.metadata)
                all_chunks.extend(sub)
            logger.info(f"Total text chunks after splitting: {len(all_chunks)}")

            # ── 4. Embed semua chunks ─────────────────────────────────────────
            texts   = [c.content for c in all_chunks]
            vectors = self.embedder.encode_documents(texts)

            # ── 5. Simpan chunks ke DB + FAISS ────────────────────────────────
            chunk_db_ids = []
            with db_session() as session:
                for idx, (chunk, vector) in enumerate(zip(all_chunks, vectors)):
                    db_chunk = DocumentChunk(
                        document_id=document_id,
                        chunk_index=idx,
                        content=chunk.content,
                        meta_data=chunk.metadata,
                        faiss_id=None,
                    )
                    session.add(db_chunk)
                    session.flush()
                    chunk_db_ids.append(db_chunk.id)

                import numpy as np
                faiss_positions = self.store.add_vectors(
                    np.array(vectors, dtype="float32"),
                    chunk_db_ids
                )

                for chunk_db_id, pos in zip(chunk_db_ids, faiss_positions):
                    session.query(DocumentChunk)\
                           .filter_by(id=chunk_db_id)\
                           .update({"faiss_id": pos})

                session.query(Document)\
                       .filter_by(id=document_id)\
                       .update({
                           "status":      "indexed",
                           "chunk_count": len(all_chunks),
                           "error_msg":   None,
                       })

            logger.success(
                f"Indexed {len(all_chunks)} chunks for document ID {document_id}"
            )
            return len(all_chunks), extraction_result

        except Exception as e:
            logger.error(f"Indexing failed for document {document_id}: {e}")
            self._update_status(document_id, "failed", str(e))
            raise

    def delete_document(self, document_id: int):
        """Remove document chunks from DB and FAISS."""
        with db_session() as session:
            chunks = session.query(DocumentChunk)\
                            .filter_by(document_id=document_id).all()
            chunk_ids = [c.id for c in chunks]

            if chunk_ids:
                self.store.remove_by_chunk_ids(chunk_ids)

            session.query(DocumentChunk)\
                   .filter_by(document_id=document_id).delete()
            session.query(Document)\
                   .filter_by(id=document_id).delete()

        logger.info(f"Deleted document {document_id} and {len(chunk_ids)} chunks.")

    def _update_status(self, document_id: int, status: str, error: str = None):
        with db_session() as session:
            update = {"status": status}
            if error:
                update["error_msg"] = error
            session.query(Document).filter_by(id=document_id).update(update)
