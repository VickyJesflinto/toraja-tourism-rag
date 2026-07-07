"""
tests/test_integration_retrieval.py

Integration Test: RAG Retrieval Pipeline
===========================================
Menguji alur PENCARIAN ujung-ke-ujung: dokumen diindeks lebih dulu (memakai
DocumentIndexer, sama seperti test_integration_ingestion.py), kemudian
RAGRetriever dipakai untuk mencari kembali chunk yang relevan terhadap
sebuah query -- baik dengan FAISS similarity murni maupun dengan algoritma
MMR (Maximal Marginal Relevance) yang sudah diuji unit-test-nya secara
matematis terpisah di test_retriever_mmr.py.

Bedanya dengan unit test MMR sebelumnya: di sana vektor dibuat sintetis
secara manual di memory. Di sini vektor benar-benar berasal dari pipeline
nyata (FakeEmbedder -> FAISSStore -> database), sehingga turut menguji
bahwa data yang mengalir antar-komponen konsisten dan retrieval benar-benar
mengembalikan chunk yang sesuai isi aslinya dari database.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


def _index_text(tmp_path, db_session, indexer, filename: str, content: str) -> int:
    from database.models import Document

    file_path = tmp_path / filename
    file_path.write_text(content, encoding="utf-8")

    with db_session() as s:
        doc = Document(filename=filename, file_type="txt", status="pending")
        s.add(doc)
        s.flush()
        doc_id = doc.id

    indexer.index_document(file_path, doc_id, extract_data=False)
    return doc_id


@pytest.fixture
def indexed_corpus(test_db, fake_embedder, temp_faiss_store, tmp_path):
    """
    Fixture yang menyiapkan korpus dokumen kecil sudah-terindeks tentang
    beberapa destinasi wisata Toraja, dipakai bersama oleh banyak test
    retrieval di file ini.
    """
    from database.connection import db_session
    from rag.ingestion.indexer import DocumentIndexer

    indexer = DocumentIndexer()

    _index_text(tmp_path, db_session, indexer, "ketekesu.txt",
        "Ke'te Kesu adalah desa wisata budaya dengan rumah adat Tongkonan "
        "yang sudah berusia ratusan tahun. Terdapat juga kuburan batu kuno "
        "dan ukiran kayu khas Toraja di kawasan ini.")

    _index_text(tmp_path, db_session, indexer, "londa.txt",
        "Londa adalah situs pemakaman tebing batu dengan gua alami yang "
        "menyimpan peti mati leluhur Toraja. Terdapat tau-tau atau patung "
        "kayu yang menggambarkan orang yang telah meninggal.")

    _index_text(tmp_path, db_session, indexer, "hotel.txt",
        "Toraja Heritage Hotel adalah penginapan bintang tiga di Rantepao "
        "dengan harga mulai 850 ribu rupiah per malam. Hotel ini memiliki "
        "kolam renang dan restoran yang menyajikan kuliner khas Toraja.")

    _index_text(tmp_path, db_session, indexer, "festival.txt",
        "Lovely December adalah festival tahunan terbesar di Toraja yang "
        "diselenggarakan setiap bulan Desember. Festival ini menampilkan "
        "pertunjukan budaya, pameran kuliner, dan upacara adat Rambu Solo.")

    return indexer


class TestRetrievalBasic:
    def test_retriever_finds_relevant_chunk_for_matching_keyword_query(self, indexed_corpus):
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=2, use_mmr=False)
        results = retriever.retrieve("Tongkonan rumah adat")

        assert len(results) > 0
        sources = [r.source for r in results]
        assert "ketekesu.txt" in sources

    def test_retriever_returns_empty_list_when_no_documents_indexed(
        self, test_db, fake_embedder, temp_faiss_store
    ):
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=5)
        results = retriever.retrieve("query apa saja")
        assert results == []

    def test_retriever_respects_k_parameter(self, indexed_corpus):
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=2, use_mmr=False)
        results = retriever.retrieve("Toraja wisata budaya", k=2)
        assert len(results) <= 2

    def test_retrieved_chunk_content_matches_database(self, indexed_corpus):
        from database.connection import db_session
        from database.models import DocumentChunk
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=3, use_mmr=False)
        results = retriever.retrieve("Tongkonan")

        assert len(results) > 0
        for r in results:
            with db_session() as s:
                db_chunk = s.query(DocumentChunk).filter_by(id=r.chunk_id).first()
                assert db_chunk is not None
                assert db_chunk.content == r.content

    def test_retriever_source_attribution_correct(self, indexed_corpus):
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=4, use_mmr=False)
        results = retriever.retrieve("hotel penginapan Rantepao")

        sources = {r.source for r in results}
        assert "Unknown" not in sources
        assert sources.issubset({"ketekesu.txt", "londa.txt", "hotel.txt", "festival.txt"})


class TestRetrievalWithMMR:
    def test_mmr_retrieval_returns_results(self, indexed_corpus):
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=3, use_mmr=True, lambda_mmr=0.5)
        results = retriever.retrieve("destinasi wisata Toraja")

        assert len(results) > 0
        assert len(results) <= 3

    def test_mmr_vs_standard_may_select_different_chunks(self, indexed_corpus):
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=3)
        standard_results = retriever.retrieve("Toraja", use_mmr=False)
        mmr_results = retriever.retrieve("Toraja", use_mmr=True, lambda_mmr=0.3)

        assert all(r.source for r in standard_results)
        assert all(r.source for r in mmr_results)

    def test_mmr_lambda_1_equals_standard_on_real_pipeline(self, indexed_corpus):
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=3)
        standard_results = retriever.retrieve("budaya Toraja", use_mmr=False)
        mmr_lambda1_results = retriever.retrieve("budaya Toraja", use_mmr=True, lambda_mmr=1.0)

        standard_ids = [r.chunk_id for r in standard_results]
        mmr_ids = [r.chunk_id for r in mmr_lambda1_results]
        assert set(standard_ids) == set(mmr_ids)

    def test_mmr_format_context_produces_readable_string(self, indexed_corpus):
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=2, use_mmr=True)
        results = retriever.retrieve("upacara adat Toraja")
        context = retriever.format_context(results)

        assert isinstance(context, str)
        if results:
            assert "Sumber" in context

    def test_format_context_handles_empty_results_gracefully(
        self, test_db, fake_embedder, temp_faiss_store
    ):
        from rag.retrieval.retriever import RAGRetriever

        retriever = RAGRetriever(k=5)
        context = retriever.format_context([])
        assert "tidak ada" in context.lower() or "relevan" in context.lower()


class TestRetrievalEndToEndWithDeletion:
    def test_deleted_document_chunks_not_retrievable_anymore(self, indexed_corpus, tmp_path):
        """
        Skenario integrasi penting: setelah sebuah dokumen dihapus melalui
        DocumentIndexer.delete_document(), chunk-nya tidak boleh lagi muncul
        di hasil pencarian retriever manapun.
        """
        from database.connection import db_session
        from database.models import Document
        from rag.retrieval.retriever import RAGRetriever

        with db_session() as s:
            doc = s.query(Document).filter_by(filename="hotel.txt").first()
            doc_id = doc.id

        indexed_corpus.delete_document(doc_id)

        retriever = RAGRetriever(k=4, use_mmr=False)
        results = retriever.retrieve("hotel penginapan Rantepao harga kamar")

        sources = [r.source for r in results]
        assert "hotel.txt" not in sources
