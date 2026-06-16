# 🏔️ Toraja Tourism RAG — Dashboard & Chatbot AI

Sistem monitoring pariwisata **Toraja** berbasis **Streamlit** dengan kemampuan **RAG (Retrieval-Augmented Generation)** menggunakan:
- **Embedding**: `paraphrase-multilingual-MiniLM-L12-v2` (mendukung Bahasa Indonesia)
- **LLM**: `gpt-oss-120b`
- **Vector Store**: FAISS (K=5 nearest neighbors)
- **Database**: MySQL
- **Frontend**: Streamlit

---

## 📁 Struktur Folder

```
toraja-tourism-rag/
├── main.py                         # Entry point Streamlit
├── requirements.txt
├── .env.example
│
├── config/
│   ├── __init__.py
│   └── settings.py                 # Semua konfigurasi & env vars
│
├── database/
│   ├── __init__.py
│   ├── models.py                   # SQLAlchemy ORM models
│   ├── connection.py               # Engine, session, helpers
│   └── migrations/
│
├── rag/
│   ├── ingestion/
│   │   ├── document_parser.py      # Parser: PDF, CSV, JSON, DOCX, XLSX, PPTX, HTML, XML
│   │   ├── chunker.py              # Text chunker dengan overlap
│   │   └── indexer.py              # Orchestrator: parse→chunk→embed→FAISS→DB
│   ├── embeddings/
│   │   └── embedder.py             # Sentence Transformer wrapper (singleton)
│   └── retrieval/
│       ├── faiss_store.py          # FAISS index manager
│       ├── retriever.py            # RAG retriever (FAISS + DB lookup)
│       └── llm_chain.py            # LLM chain: RAG prompt + gpt-oss-120b
│
├── app/
│   ├── components/
│   │   └── sidebar.py              # Navigasi sidebar
│   ├── user/
│   │   ├── dashboard.py            # Dashboard monitoring (KPI, chart, peta)
│   │   ├── data_page.py            # Tabel data pariwisata (read-only)
│   │   └── login_page.py           # Halaman login
│   ├── chatbot/
│   │   └── chatbot_page.py         # Chatbot AI dengan RAG
│   └── admin/
│       ├── documents_page.py       # Upload & kelola dokumen RAG
│       ├── input_data_page.py      # CRUD data pariwisata
│       └── users_page.py           # Kelola user
│
├── utils/
│   └── auth.py                     # Autentikasi, hashing, session helpers
│
├── scripts/
│   └── init_db.py                  # Inisialisasi DB & seed data
│
├── data/
│   ├── uploads/                    # File yang diupload admin
│   └── faiss_index/                # FAISS index files
│
└── logs/
```

---

## ⚡ Quick Start

### 1. Prasyarat

- Python 3.10+
- MySQL 8.0+
- (Opsional) CUDA GPU untuk embedding lebih cepat

### 2. Clone & Setup

```bash
git clone <repo>
cd toraja-tourism-rag

python -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

### 3. Konfigurasi

```bash
cp .env.example .env
# Edit .env: isi DB credentials dan OpenAI API key
```

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=toraja_tourism
DB_USER=root
DB_PASSWORD=yourpassword

OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-oss-120b

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 4. Buat Database MySQL

```sql
CREATE DATABASE toraja_tourism CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Inisialisasi Database

```bash
# Buat tabel saja
python scripts/init_db.py

# Buat tabel + data contoh Toraja
python scripts/init_db.py --seed
```

### 6. Jalankan Aplikasi

```bash
streamlit run main.py
```

Buka browser: **http://localhost:8501**

---

## 🔐 Akun Default

| Role  | Username | Password  |
|-------|----------|-----------|
| Admin | `admin`  | `admin123` |

> ⚠️ Ganti password admin setelah login pertama!

---

## 🎭 Fitur per Role

| Fitur                        | User/Guest | Admin |
|------------------------------|:----------:|:-----:|
| Lihat Dashboard               | ✅          | ✅    |
| Lihat Data Pariwisata         | ✅          | ✅    |
| Gunakan Chatbot AI            | ✅          | ✅    |
| Upload Dokumen RAG            | ❌          | ✅    |
| Input/Edit Data Pariwisata    | ❌          | ✅    |
| Kelola User                   | ❌          | ✅    |
| Re-index / Hapus Dokumen      | ❌          | ✅    |

---

## 📂 Format Dokumen yang Didukung

| Format | Ekstensi | Keterangan |
|--------|----------|------------|
| PDF    | `.pdf`   | Text + tabel per halaman |
| CSV    | `.csv`   | Chunked per 50 baris |
| JSON   | `.json`  | Flatten nested objects |
| Word   | `.docx`  | Paragraf + tabel |
| Excel  | `.xlsx`  | Multi-sheet support |
| PowerPoint | `.pptx` | Per slide |
| HTML   | `.html`  | Strip tags, extract text |
| XML    | `.xml`   | Tag-based extraction |
| Text   | `.txt`   | Paragraph splitting |

---

## 🧠 Arsitektur RAG

```
Upload File
    ↓
DocumentParser  →  ekstrak teks per halaman/baris/slide
    ↓
TextChunker     →  potong jadi chunk 1000 char, overlap 200
    ↓
Embedder        →  paraphrase-multilingual-MiniLM-L12-v2 → vector[384]
    ↓
FAISSStore      →  IndexFlatIP (cosine similarity)
    ↓ (tersimpan)
MySQL           →  document_chunks (content, metadata, faiss_id)

━━━━━━━━━━━━━━━━━━━━━━━━ Query Time ━━━━━━━━━━━━━━━━━━━━━━━━

User Query
    ↓
Embedder        →  encode query → vector[384]
    ↓
FAISSStore      →  search top-5 (K=5)
    ↓
DB Lookup       →  ambil chunk content dari MySQL
    ↓
LLMChain        →  sistem prompt + konteks + query → gpt-oss-120b
    ↓
Answer + Sources → tampil di Chatbot UI
```

---

## 🛠️ Troubleshooting

**DB Connection Error:**
- Pastikan MySQL berjalan dan credentials di `.env` benar
- Pastikan database `toraja_tourism` sudah dibuat

**Model Loading Slow (pertama kali):**
- Embedding model ~90MB, akan didownload otomatis dari HuggingFace
- Selanjutnya menggunakan cache lokal

**FAISS Empty (chatbot bilang tidak ada data):**
- Admin perlu upload dokumen via menu "Kelola Dokumen"
- Atau jalankan `--seed` lalu upload file teks tentang Toraja

**OpenAI API Error:**
- Pastikan `OPENAI_API_KEY` valid
- Pastikan model `gpt-oss-120b` tersedia di endpoint Anda

