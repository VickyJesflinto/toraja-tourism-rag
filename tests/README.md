# Testing — Toraja Tourism RAG

## Cara Menjalankan

```bash
pip install -r requirements.txt --break-system-packages
pip install -r requirements-test.txt --break-system-packages

pytest                                    # jalankan semua test (unit + integration)
pytest -v                                 # mode verbose
pytest tests/test_auth.py                 # 1 file unit test saja
pytest tests/test_integration_*.py        # hanya integration test
pytest --cov=utils --cov=rag --cov=database --cov-report=term-missing
```

---

## Ringkasan Hasil — Unit Testing

| Modul Diuji | File Test | Jumlah Test | Status |
|---|---|---|---|
| `utils/auth.py` | `test_auth.py` | 26 | PASS 26/26 |
| `rag/ingestion/chunker.py` | `test_chunker.py` | 16 | PASS 16/16 |
| `rag/ingestion/data_extractor.py` | `test_data_extractor.py` | 60 | PASS 60/60 |
| `database/models.py` | `test_models.py` | 19 | PASS 19/19 |
| `rag/retrieval/retriever.py` (MMR) | `test_retriever_mmr.py` | 20 | PASS 20/20 |
| **Subtotal Unit Test** | | **141** | **PASS 141/141** |

## Ringkasan Hasil — Integration Testing

| Alur yang Diuji | File Test | Jumlah Test | Status |
|---|---|---|---|
| Document Ingestion Pipeline (Parser→Chunker→Embedder→FAISS→DB) | `test_integration_ingestion.py` | 10 | PASS 10/10 |
| RAG Retrieval Pipeline (FAISS search + MMR pada data nyata) | `test_integration_retrieval.py` | 11 | PASS 11/11 |
| Data Extraction → Fuzzy Dedup → Multi-Table DB | `test_integration_data_extraction.py` | 11 | PASS 11/11 |
| Auth → Session → Role-Based Access Control | `test_integration_auth_rbac.py` | 12 | PASS 12/12 |
| Chat History Persistence Lintas Tabel | `test_integration_chat_history.py` | 13 | PASS 13/13 |
| **Subtotal Integration Test** | | **57** | **PASS 57/57** |

## **TOTAL KESELURUHAN: 198 PASS / 198 (100%)**

---

## Strategi Integration Testing

Integration test menguji **alur kerja gabungan** antar-komponen (database +
FAISS + parser + embedder + session Streamlit bekerja bersamaan), berbeda
dari unit test yang menguji fungsi murni secara terisolasi.

### Fixture Tambahan di `conftest.py`

| Fixture | Fungsi |
|---|---|
| `fake_embedder` | Pengganti `Embedder` asli (sentence-transformer 470MB) dengan implementasi hash-deterministik 384-dim, tanpa perlu koneksi internet ke HuggingFace. Teks identik → vektor identik; vektor selalu di-normalize, sama seperti model asli. |
| `temp_faiss_store` | `FAISSStore` nyata yang menyimpan index ke direktori temporer unik per test, dipatch ke `indexer.py` DAN `retriever.py` secara bersamaan agar data yang diindeks satu komponen bisa ditemukan kembali komponen lain dalam test yang sama. |
| `test_db` | (dari tahap unit test) Database SQLite in-memory dengan `PRAGMA foreign_keys=ON`. |

### Mengapa LLM (OpenRouter) Tidak Dipanggil Sungguhan?

Dua titik integrasi yang melibatkan panggilan API eksternal (`_call_llm` di
`data_extractor.py`, dan seluruh `llm_chain.py`) di-mock pada level **fungsi
network call saja** — bukan seluruh modul. Artinya seluruh logika upsert,
fuzzy dedup, dan penyimpanan multi-tabel tetap diuji nyata dengan database,
hanya respons LLM yang disimulasikan. Ini pendekatan standar integration
testing untuk sistem yang bergantung pada API berbayar/berbatas-rate.

### Bug yang Ditemukan di Tahap Integration Testing

Tidak ditemukan bug baru pada tahap ini — seluruh perbaikan sebelumnya
(Foreign Key cascade di `models.py`, `st.rerun()` di luar `db_session()`)
tervalidasi ulang secara tidak langsung melalui skenario integrasi yang
melibatkan delete dan update lintas tabel.

---

## Yang Masih Di Luar Cakupan Otomatis

| Komponen | Alasan | Tahap Pengujian |
|---|---|---|
| `rag/retrieval/llm_chain.py` (`LLMChain.chat()`) | Membutuhkan API key OpenRouter aktif dan biaya nyata per panggilan | Manual / Blackbox Testing |
| `rag/ingestion/document_parser.py` (PDF, DOCX, XLSX, PPTX) | Membutuhkan library parsing format biner yang berat; logika ekstraksi tabel/halaman lebih cocok diuji dengan sample file nyata | Blackbox Testing |
| Seluruh `app/*.py` (Streamlit UI) | Memerlukan browser/runtime Streamlit sungguhan untuk interaksi pengguna | Blackbox Testing |
| RAGAS (kualitas jawaban RAG) | Memerlukan dataset evaluasi & embedding/LLM nyata, metrik kualitatif bukan pass/fail biner | RAGAS Evaluation (tahap berikutnya) |

---

## Struktur File Test

```
tests/
├── conftest.py                          # Fixture: SQLite, mock streamlit, fake_embedder, temp_faiss_store
├── test_auth.py                         # [Unit]        hash_password, verify_password, register_user
├── test_chunker.py                      # [Unit]        TextChunker.chunk()
├── test_data_extractor.py               # [Unit]        Fuzzy matching, value helpers
├── test_models.py                       # [Unit]        Struktur ORM, constraint, cascade
├── test_retriever_mmr.py                # [Unit]        Algoritma MMR (vektor sintetis)
├── test_integration_ingestion.py        # [Integration] Parser→Chunker→Embedder→FAISS→DB
├── test_integration_retrieval.py        # [Integration] FAISS search + MMR pada data nyata
├── test_integration_data_extraction.py  # [Integration] Ekstraksi→Dedup→Multi-table DB
├── test_integration_auth_rbac.py        # [Integration] Login→Session→RBAC
└── test_integration_chat_history.py     # [Integration] Riwayat chat lintas 3 tabel
```


## Ringkasan Hasil — RAGAS Evaluation Logic

| Modul Diuji | File Test | Jumlah Test | Status |
|---|---|---|---|
| `evaluation/ragas_metrics.py` (formula 4 metrik) | `test_ragas_metrics_logic.py` | 31 | PASS 31/31 |

## **TOTAL KESELURUHAN: 229 PASS / 229 (100%)**
(141 unit test + 57 integration test + 31 RAGAS logic test)

Lihat `evaluation/README.md` untuk detail evaluasi kualitas jawaban RAG
menggunakan metrik RAGAS (faithfulness, answer relevancy, context precision,
context recall) dan hasil simulasi evaluasi berdasarkan golden dataset.
