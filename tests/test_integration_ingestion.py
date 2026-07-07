"""
tests/test_integration_ingestion.py

Integration Test: Document Ingestion Pipeline
================================================
Menguji alur kerja GABUNGAN beberapa komponen sekaligus, berbeda dari unit
test yang menguji fungsi murni secara terisolasi:

    File fisik (.txt/.csv/.json)
        -> DocumentParser   (baca & ekstrak teks mentah)
        -> TextChunker      (potong jadi chunk + overlap)
        -> Embedder         (encode ke vektor 384-dim)  [FakeEmbedder]
        -> FAISSStore       (index vektor untuk similarity search) [temp dir]
        -> Database         (simpan record Document + DocumentChunk) [SQLite]

Komponen LLM (OpenRouter, untuk ekstraksi data terstruktur) dimatikan
(extract_data=False) di tahap ini karena membutuhkan API key & koneksi
eksternal sungguhan -- diuji terpisah dengan mocking di
test_integration_data_extraction.py.

Fixture yang dipakai (didefinisikan di conftest.py):
- test_db          : Database SQLite in-memory per test
- fake_embedder    : Pengganti model sentence-transformer (deterministik, offline)
- temp_faiss_store : FAISS index di direktori temporer, dipakai bersama oleh
                      DocumentIndexer DAN RAGRetriever dalam test yang sama
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


def _create_text_file(tmp_path, filename: str, content: str) -> Path:
    file_path = tmp_path / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _create_csv_file(tmp_path, filename: str, content: str) -> Path:
    file_path = tmp_path / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


class TestIngestionPipelineTxt:
    def test_full_pipeline_creates_document_record(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document
        from rag.ingestion.indexer import DocumentIndexer

        content = (
            "Ke'te Kesu adalah destinasi wisata budaya terkenal di Toraja Utara. "
            "Situs ini memiliki rumah adat Tongkonan yang sudah berusia ratusan tahun. "
            "Selain itu terdapat juga kuburan batu kuno dan tau-tau di tebing."
        )
        file_path = _create_text_file(tmp_path, "ketekesu.txt", content)

        with db_session() as s:
            doc = Document(filename="ketekesu.txt", file_type="txt", status="pending")
            s.add(doc)
            s.flush()
            doc_id = doc.id

        indexer = DocumentIndexer()
        n_chunks, extraction = indexer.index_document(file_path, doc_id, extract_data=False)

        assert n_chunks > 0
        assert extraction is None

        with db_session() as s:
            saved_doc = s.query(Document).filter_by(id=doc_id).first()
            assert saved_doc.status == "indexed"
            assert saved_doc.chunk_count == n_chunks
            assert saved_doc.error_msg is None

    def test_full_pipeline_creates_chunks_in_db(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document, DocumentChunk
        from rag.ingestion.indexer import DocumentIndexer

        content = "Toraja memiliki banyak destinasi wisata budaya yang menarik. " * 20
        file_path = _create_text_file(tmp_path, "toraja.txt", content)

        with db_session() as s:
            doc = Document(filename="toraja.txt", file_type="txt", status="pending")
            s.add(doc)
            s.flush()
            doc_id = doc.id

        indexer = DocumentIndexer()
        n_chunks, _ = indexer.index_document(file_path, doc_id, extract_data=False)

        with db_session() as s:
            chunks = s.query(DocumentChunk).filter_by(document_id=doc_id).all()
            assert len(chunks) == n_chunks
            for chunk in chunks:
                assert chunk.content != ""
                assert chunk.faiss_id is not None

    def test_full_pipeline_indexes_vectors_into_faiss(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document
        from rag.ingestion.indexer import DocumentIndexer

        content = "Lemo adalah situs pemakaman tebing batu yang terkenal di Toraja."
        file_path = _create_text_file(tmp_path, "lemo.txt", content)

        assert temp_faiss_store.total_vectors == 0

        with db_session() as s:
            doc = Document(filename="lemo.txt", file_type="txt", status="pending")
            s.add(doc)
            s.flush()
            doc_id = doc.id

        indexer = DocumentIndexer()
        n_chunks, _ = indexer.index_document(file_path, doc_id, extract_data=False)

        assert temp_faiss_store.total_vectors == n_chunks

    def test_faiss_id_matches_correct_chunk(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document, DocumentChunk
        from rag.ingestion.indexer import DocumentIndexer

        content = "Satu paragraf pendek saja untuk diuji."
        file_path = _create_text_file(tmp_path, "single.txt", content)

        with db_session() as s:
            doc = Document(filename="single.txt", file_type="txt", status="pending")
            s.add(doc)
            s.flush()
            doc_id = doc.id

        indexer = DocumentIndexer()
        indexer.index_document(file_path, doc_id, extract_data=False)

        with db_session() as s:
            chunk = s.query(DocumentChunk).filter_by(document_id=doc_id).first()
            faiss_id = chunk.faiss_id
            chunk_db_id = chunk.id

        assert temp_faiss_store._id_map[faiss_id] == chunk_db_id


class TestIngestionPipelineCsv:
    def test_csv_file_produces_header_and_row_chunks(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document
        from rag.ingestion.indexer import DocumentIndexer

        csv_content = (
            "nama,kategori,harga_tiket\n"
            "Ke'te Kesu,budaya,20000\n"
            "Londa,budaya,20000\n"
            "Tilanga,alam,15000\n"
        )
        file_path = _create_csv_file(tmp_path, "destinasi.csv", csv_content)

        with db_session() as s:
            doc = Document(filename="destinasi.csv", file_type="csv", status="pending")
            s.add(doc)
            s.flush()
            doc_id = doc.id

        indexer = DocumentIndexer()
        n_chunks, _ = indexer.index_document(file_path, doc_id, extract_data=False)

        assert n_chunks >= 1

        with db_session() as s:
            saved_doc = s.query(Document).filter_by(id=doc_id).first()
            assert saved_doc.status == "indexed"


class TestIngestionPipelineErrorHandling:
    def test_unsupported_format_marks_document_as_failed(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document
        from rag.ingestion.indexer import DocumentIndexer

        file_path = tmp_path / "data.xyz"
        file_path.write_text("dummy content")

        with db_session() as s:
            doc = Document(filename="data.xyz", file_type="xyz", status="pending")
            s.add(doc)
            s.flush()
            doc_id = doc.id

        indexer = DocumentIndexer()
        with pytest.raises(ValueError):
            indexer.index_document(file_path, doc_id, extract_data=False)

        with db_session() as s:
            saved_doc = s.query(Document).filter_by(id=doc_id).first()
            assert saved_doc.status == "failed"
            assert saved_doc.error_msg is not None

    def test_empty_file_marks_document_as_failed(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document
        from rag.ingestion.indexer import DocumentIndexer

        file_path = _create_text_file(tmp_path, "empty.txt", "")

        with db_session() as s:
            doc = Document(filename="empty.txt", file_type="txt", status="pending")
            s.add(doc)
            s.flush()
            doc_id = doc.id

        indexer = DocumentIndexer()
        with pytest.raises(ValueError):
            indexer.index_document(file_path, doc_id, extract_data=False)

        with db_session() as s:
            saved_doc = s.query(Document).filter_by(id=doc_id).first()
            assert saved_doc.status == "failed"


class TestIngestionPipelineDelete:
    def test_delete_document_removes_chunks_from_db(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document, DocumentChunk
        from rag.ingestion.indexer import DocumentIndexer

        content = "Konten yang akan dihapus setelah diindeks untuk pengujian."
        file_path = _create_text_file(tmp_path, "todelete.txt", content)

        with db_session() as s:
            doc = Document(filename="todelete.txt", file_type="txt", status="pending")
            s.add(doc)
            s.flush()
            doc_id = doc.id

        indexer = DocumentIndexer()
        indexer.index_document(file_path, doc_id, extract_data=False)

        indexer.delete_document(doc_id)

        with db_session() as s:
            remaining_doc = s.query(Document).filter_by(id=doc_id).first()
            remaining_chunks = s.query(DocumentChunk).filter_by(document_id=doc_id).all()
            assert remaining_doc is None
            assert len(remaining_chunks) == 0

    def test_delete_document_removes_vectors_from_faiss(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document
        from rag.ingestion.indexer import DocumentIndexer

        content = "Konten kedua untuk diuji penghapusan vektor FAISS secara nyata."
        file_path = _create_text_file(tmp_path, "todelete2.txt", content)

        with db_session() as s:
            doc = Document(filename="todelete2.txt", file_type="txt", status="pending")
            s.add(doc)
            s.flush()
            doc_id = doc.id

        indexer = DocumentIndexer()
        n_chunks, _ = indexer.index_document(file_path, doc_id, extract_data=False)
        assert temp_faiss_store.total_vectors == n_chunks

        indexer.delete_document(doc_id)

        assert temp_faiss_store.total_vectors == 0

    def test_delete_one_document_keeps_other_documents_intact(
        self, test_db, fake_embedder, temp_faiss_store, tmp_path
    ):
        from database.connection import db_session
        from database.models import Document, DocumentChunk
        from rag.ingestion.indexer import DocumentIndexer

        file_a = _create_text_file(tmp_path, "a.txt", "Dokumen A berisi info tentang Londa.")
        file_b = _create_text_file(tmp_path, "b.txt", "Dokumen B berisi info tentang Lemo.")

        with db_session() as s:
            doc_a = Document(filename="a.txt", file_type="txt", status="pending")
            doc_b = Document(filename="b.txt", file_type="txt", status="pending")
            s.add(doc_a)
            s.add(doc_b)
            s.flush()
            doc_a_id, doc_b_id = doc_a.id, doc_b.id

        indexer = DocumentIndexer()
        indexer.index_document(file_a, doc_a_id, extract_data=False)
        n_chunks_b, _ = indexer.index_document(file_b, doc_b_id, extract_data=False)

        indexer.delete_document(doc_a_id)

        with db_session() as s:
            doc_b_check = s.query(Document).filter_by(id=doc_b_id).first()
            chunks_b = s.query(DocumentChunk).filter_by(document_id=doc_b_id).all()
            assert doc_b_check is not None
            assert doc_b_check.status == "indexed"
            assert len(chunks_b) == n_chunks_b
