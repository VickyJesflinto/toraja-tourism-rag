"""
tests/conftest.py

Konfigurasi pytest & fixture global untuk seluruh unit test.

Strategi:
- Tidak mengubah kode sumber project sama sekali.
- database.connection.engine & SessionLocal di-monkeypatch ke SQLite
  in-memory SETELAH modul project selesai di-import, supaya test
  benar-benar terisolasi dari MySQL/Aiven asli.
- streamlit.session_state di-mock pakai dict sederhana, karena utils/auth.py
  memanggil st.session_state di luar konteks aplikasi Streamlit yang berjalan.
"""
import sys
import os
from pathlib import Path

# Pastikan root project bisa di-import sebagai package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest


# ─── Mock Streamlit session_state SEBELUM modul project di-import ────────────
# utils/auth.py melakukan `import streamlit as st` dan mengakses
# st.session_state secara langsung. Di luar runtime Streamlit asli,
# st.session_state tidak tersedia, sehingga perlu disubstitusi dengan
# objek dict-like sederhana.

class _FakeSessionState(dict):
    """Tiruan st.session_state yang mendukung akses dict & atribut."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value


@pytest.fixture(autouse=True)
def _reset_streamlit_session_state():
    """Reset session_state palsu sebelum setiap test agar tidak ada bleed antar-test."""
    import streamlit as st
    if not hasattr(st, "session_state") or not isinstance(st.session_state, _FakeSessionState):
        st.session_state = _FakeSessionState()
    else:
        st.session_state.clear()
    yield
    st.session_state.clear()


# ─── SQLite in-memory database fixture ───────────────────────────────────────

@pytest.fixture(scope="function")
def test_db():
    """
    Membuat database SQLite in-memory yang fresh untuk setiap test function,
    lalu mem-patch database.connection.engine & SessionLocal agar seluruh
    kode project (db_session(), dsb.) otomatis memakai database test ini
    tanpa perlu mengubah kode sumber sama sekali.

    Yields:
        SessionLocal (sessionmaker) — untuk membuat session manual jika perlu.
    """
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    import database.connection as conn_module
    from database.models import Base

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # SQLite TIDAK menegakkan FOREIGN KEY constraint secara default.
    # Aktifkan secara eksplisit supaya ON DELETE CASCADE / SET NULL yang
    # didefinisikan di database/models.py benar-benar diuji di level DB,
    # sama seperti yang terjadi di MySQL/Aiven produksi.
    @event.listens_for(test_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)

    # Patch global di module database.connection — ini yang membuat
    # db_session(), get_db(), health_check() di seluruh project otomatis
    # mengarah ke SQLite test, karena mereka mengacu ke `engine`/`SessionLocal`
    # pada namespace module connection.py.
    original_engine  = conn_module.engine
    original_session = conn_module.SessionLocal

    conn_module.engine       = test_engine
    conn_module.SessionLocal = TestSessionLocal

    yield TestSessionLocal

    # Cleanup — kembalikan referensi asli (jaga-jaga jika ada test lain
    # yang tidak menggunakan fixture ini dalam sesi pytest yang sama).
    conn_module.engine       = original_engine
    conn_module.SessionLocal = original_session
    test_engine.dispose()


@pytest.fixture
def db_session_test(test_db):
    """Shortcut: langsung mengembalikan context manager db_session yang sudah terhubung ke SQLite test."""
    from database.connection import db_session
    return db_session


# ─── Fake Embedder untuk Integration Testing ──────────────────────────────────
# Model sentence-transformer asli (paraphrase-multilingual-MiniLM-L12-v2, ~470MB)
# membutuhkan koneksi internet ke huggingface.co untuk diunduh, yang tidak selalu
# tersedia di lingkungan CI/CD atau sandbox. FakeEmbedder mensimulasikan interface
# yang identik dengan Embedder asli (encode_query, encode_documents) namun
# menghasilkan vektor 384-dim secara DETERMINISTIK berbasis hash dari teks input.
#
# Properti penting yang tetap dipertahankan agar pipeline RAG bisa diuji nyata:
# 1. Teks yang sama -> vektor yang SAMA (deterministik, seperti model asli)
# 2. Teks yang mirip secara leksikal -> vektor yang cenderung lebih dekat
#    (dicapai dengan bag-of-words hashing, bukan vektor acak murni)
# 3. Vektor selalu dinormalisasi (L2 norm = 1), sama seperti model asli
# 4. Dimensi output = 384, identik dengan model asli

class FakeEmbedder:
    """Pengganti Embedder asli untuk integration test tanpa dependensi internet."""

    DIMENSION = 384

    def __init__(self, model_name: str = None):
        self.model_name = model_name or "fake-embedder-for-testing"
        self.dimension  = self.DIMENSION

    def _hash_token_to_dims(self, token: str, vec):
        """Sebarkan kontribusi satu token ke beberapa dimensi vektor secara deterministik."""
        import hashlib
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        for i in range(8):   # tiap token mempengaruhi 8 dimensi
            dim = (h >> (i * 4)) % self.DIMENSION
            sign = 1.0 if (h >> (i + 20)) % 2 == 0 else -1.0
            vec[dim] += sign * (1.0 / (i + 1))

    def _encode_one(self, text: str):
        import numpy as np
        vec = np.zeros(self.DIMENSION, dtype=np.float32)
        tokens = text.lower().split()
        if not tokens:
            tokens = [""]
        for tok in tokens:
            self._hash_token_to_dims(tok, vec)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec

    def encode(self, texts, batch_size: int = 64, normalize: bool = True):
        import numpy as np
        single = isinstance(texts, str)
        if single:
            texts = [texts]
        result = np.array([self._encode_one(t) for t in texts], dtype=np.float32)
        return result[0] if single else result

    def encode_query(self, query: str):
        return self.encode(query, normalize=True)

    def encode_documents(self, docs, batch_size: int = 64):
        return self.encode(docs, batch_size=batch_size, normalize=True)


@pytest.fixture
def fake_embedder(monkeypatch):
    """
    Patch Embedder di seluruh modul yang mengimpornya secara langsung
    (rag.embeddings.embedder.Embedder) dengan FakeEmbedder, agar pipeline
    integration test (indexer, retriever) berjalan tanpa perlu mengunduh
    model sentence-transformer maupun koneksi internet.
    """
    import rag.embeddings.embedder as embedder_module

    # Reset singleton supaya instance lama (jika ada) tidak ke-cache antar-test
    embedder_module.Embedder._instance = None

    fake = FakeEmbedder()
    monkeypatch.setattr(embedder_module, "Embedder", lambda *a, **kw: fake)

    # rag/ingestion/indexer.py dan rag/retrieval/retriever.py melakukan
    # `from rag.embeddings.embedder import Embedder` di level modul, sehingga
    # referensi nama "Embedder" di namespace mereka juga harus dipatch.
    import rag.ingestion.indexer as indexer_module
    import rag.retrieval.retriever as retriever_module
    monkeypatch.setattr(indexer_module, "Embedder", lambda *a, **kw: fake)
    monkeypatch.setattr(retriever_module, "Embedder", lambda *a, **kw: fake)

    return fake


# ─── FAISS index sementara untuk Integration Testing ──────────────────────────

@pytest.fixture
def temp_faiss_store(tmp_path, monkeypatch):
    """
    Membuat FAISSStore baru yang menyimpan index-nya di direktori temporer
    unik per test (tmp_path bawaan pytest), lalu mem-patch FAISSStore di
    modul indexer & retriever agar keduanya memakai instance yang SAMA
    (penting supaya data yang di-index oleh indexer.py bisa benar-benar
    ditemukan kembali oleh retriever.py dalam test yang sama).
    """
    from rag.retrieval.faiss_store import FAISSStore

    faiss_dir = tmp_path / "faiss_index"
    faiss_dir.mkdir(parents=True, exist_ok=True)

    shared_store = FAISSStore(index_path=faiss_dir, dimension=384)

    import rag.ingestion.indexer as indexer_module
    import rag.retrieval.retriever as retriever_module
    monkeypatch.setattr(indexer_module, "FAISSStore", lambda *a, **kw: shared_store)
    monkeypatch.setattr(retriever_module, "FAISSStore", lambda *a, **kw: shared_store)

    return shared_store
