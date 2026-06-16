"""
app/admin/documents_page.py
Admin page: upload, index, dan kelola dokumen RAG.
Kini dilengkapi ekstraksi data terstruktur otomatis ke tabel pariwisata.
"""
import streamlit as st
import os
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.auth import require_admin
from database.connection import db_session
from database.models import Document, DocumentChunk
from rag.ingestion.indexer import DocumentIndexer
from config.settings import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_MB


STATUS_COLOR = {
    "pending":    "🟡",
    "processing": "🔵",
    "indexed":    "🟢",
    "failed":     "🔴",
}


def render_documents_page():
    require_admin()

    st.markdown("""
    <h2 style='color:#DAA520; font-family:Georgia,serif;'>📁 Kelola Dokumen RAG</h2>
    <p style='color:#A89070;'>
        Upload dokumen untuk chatbot AI. Data pariwisata di dalamnya akan
        otomatis diekstrak dan disimpan ke dashboard &amp; halaman Data Pariwisata.
    </p>
    """, unsafe_allow_html=True)

    tab_upload, tab_manage = st.tabs(["⬆️ Upload Dokumen", "📋 Daftar Dokumen"])

    # ── UPLOAD ────────────────────────────────────────────────────────────────
    with tab_upload:
        st.markdown("#### Upload file untuk diindeks ke RAG")

        # Info box
        st.info(
            f"**Format didukung:** {', '.join(sorted(ALLOWED_EXTENSIONS))}  |  "
            f"**Maks ukuran:** {MAX_UPLOAD_MB} MB per file"
        )

        # Penjelasan fitur ekstraksi
        with st.expander("ℹ️ Tentang Ekstraksi Data Otomatis", expanded=False):
            st.markdown("""
            Saat dokumen diupload, sistem akan:

            1. **Mengindeks ke RAG** — teks dipotong-potong dan disimpan ke FAISS
               agar Chatbot AI bisa menjawab pertanyaan berdasarkan isi dokumen.

            2. **Mengekstrak data terstruktur** *(opsional)* — LLM membaca isi
               dokumen dan mencari data seperti:
               - 🗺️ **Destinasi wisata** → tabel `tourist_attractions`
               - 📊 **Statistik kunjungan** → tabel `visitor_statistics`
               - 🏨 **Akomodasi** → tabel `accommodations`
               - 🎭 **Event budaya** → tabel `cultural_events`
               - 🏗️ **Infrastruktur** → tabel `tourism_infrastructure`

               Data yang berhasil diekstrak otomatis muncul di **Dashboard** dan
               halaman **Data Pariwisata** tanpa perlu input manual.

            **Format yang paling baik untuk ekstraksi data:**
            CSV / Excel dengan kolom yang jelas, atau JSON terstruktur.
            PDF/DOCX naratif tetap bisa diekstrak tapi hasilnya mungkin tidak lengkap.
            """)

        uploaded_files = st.file_uploader(
            "Pilih file",
            type=[e.lstrip(".") for e in ALLOWED_EXTENSIONS],
            accept_multiple_files=True,
        )

        if uploaded_files:
            col_opt1, col_opt2 = st.columns(2)
            do_extract = col_opt1.toggle(
                "🔍 Ekstrak data ke Dashboard",
                value=True,
                help="Aktifkan agar data pariwisata dalam dokumen otomatis masuk ke dashboard",
            )

            if col_opt2.button("⚡ Proses & Indeks Semua File", type="primary"):
                indexer = DocumentIndexer()
                user_id = st.session_state.get("user_id")
                results = []

                progress    = st.progress(0)
                status_area = st.empty()

                for i, uf in enumerate(uploaded_files):
                    progress.progress(i / len(uploaded_files))
                    status_area.info(f"🔄 Memproses: **{uf.name}**...")

                    content = uf.read()
                    size_mb = len(content) / (1024 * 1024)

                    if size_mb > MAX_UPLOAD_MB:
                        results.append(("❌", uf.name, f"Ukuran {size_mb:.1f}MB melebihi batas {MAX_UPLOAD_MB}MB", None))
                        continue

                    ext = Path(uf.name).suffix.lower()
                    if ext not in ALLOWED_EXTENSIONS:
                        results.append(("❌", uf.name, "Format tidak didukung", None))
                        continue

                    save_path = UPLOAD_DIR / uf.name
                    with open(save_path, "wb") as f:
                        f.write(content)

                    try:
                        with db_session() as session:
                            doc = Document(
                                filename=uf.name,
                                original_name=uf.name,
                                file_type=ext.lstrip("."),
                                file_size=len(content),
                                file_path=str(save_path),
                                status="pending",
                                uploaded_by=user_id,
                            )
                            session.add(doc)
                            session.flush()
                            doc_id = doc.id

                        n_chunks, extraction = indexer.index_document(
                            save_path, doc_id,
                            extract_data=do_extract,
                        )

                        results.append(("✅", uf.name, f"{n_chunks} chunks diindeks", extraction))

                    except Exception as e:
                        results.append(("❌", uf.name, str(e)[:120], None))

                progress.progress(1.0)
                status_area.empty()
                st.cache_data.clear()

                # ── Tampilkan hasil ───────────────────────────────────────────
                st.markdown("#### ✅ Hasil Proses")
                for icon, fname, msg, extraction in results:
                    if icon == "✅":
                        st.success(f"**{fname}** — {msg}")
                        if extraction and extraction.total > 0:
                            n_ins, n_upd = extraction.dedup_summary()
                            st.markdown(
                                f"&nbsp;&nbsp;&nbsp;📦 **Data terekstrak:** {extraction.summary()}"
                            )
                            st.markdown(
                                f"&nbsp;&nbsp;&nbsp;"
                                f"🆕 {n_ins} record baru &nbsp;·&nbsp; "
                                f"♻️ {n_upd} record diperbarui (tidak duplikat)"
                            )
                            if extraction.dedup_log:
                                with st.expander("🔍 Detail dedup log", expanded=False):
                                    for log_line in extraction.dedup_log:
                                        icon = "🆕" if log_line.startswith("INSERT") else "♻️"
                                        st.markdown(f"- {icon} {log_line}")
                            if extraction.errors:
                                for err in extraction.errors:
                                    st.caption(f"⚠️ {err}")
                        elif extraction and extraction.total == 0 and do_extract:
                            st.caption("&nbsp;&nbsp;&nbsp;ℹ️ Tidak ada data terstruktur terdeteksi di dokumen ini.")
                    else:
                        st.error(f"**{fname}** — {msg}")

    # ── DAFTAR DOKUMEN ────────────────────────────────────────────────────────
    with tab_manage:
        with db_session() as s:
            docs = s.query(Document).order_by(Document.created_at.desc()).all()
            doc_data = [{
                "id":       d.id,
                "Nama File": d.original_name or d.filename,
                "Tipe":     d.file_type or "-",
                "Ukuran":   f"{d.file_size / 1024:.1f} KB" if d.file_size else "-",
                "Chunks":   d.chunk_count or 0,
                "Status":   f"{STATUS_COLOR.get(d.status,'⚪')} {d.status}",
                "Upload":   d.created_at.strftime("%d %b %Y %H:%M") if d.created_at else "-",
                "Error":    (d.error_msg or "")[:80],
                "_path":    d.file_path,
            } for d in docs]

        if not doc_data:
            st.info("Belum ada dokumen yang diupload.")
            return

        # Summary
        total_chunks = sum(d["Chunks"] for d in doc_data)
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Total Dokumen", len(doc_data))
        mc2.metric("Total Chunks",  total_chunks)
        mc3.metric("Indexed",       sum(1 for d in doc_data if "indexed" in d["Status"]))

        st.markdown("---")

        for doc in doc_data:
            status_key = doc["Status"].split()[-1] if doc["Status"] else "pending"
            with st.expander(
                f"{STATUS_COLOR.get(status_key,'⚪')} **{doc['Nama File']}**"
                f" — {doc['Chunks']} chunks | {doc['Tipe']} | {doc['Upload']}",
                expanded=False,
            ):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Tipe",   doc["Tipe"])
                c2.metric("Ukuran", doc["Ukuran"])
                c3.metric("Chunks", doc["Chunks"])
                c4.metric("Status", doc["Status"])

                if doc["Error"]:
                    st.error(f"Error: {doc['Error']}")

                col_re, col_re_ext, col_del = st.columns(3)

                # Re-index saja (tanpa ekstraksi ulang)
                with col_re:
                    if st.button("🔄 Re-index RAG", key=f"reindex_{doc['id']}",
                                 help="Indeks ulang ke FAISS tanpa ekstraksi data"):
                        try:
                            indexer = DocumentIndexer()
                            with db_session() as s:
                                s.query(DocumentChunk)\
                                 .filter_by(document_id=doc["id"]).delete()
                            n, _ = indexer.index_document(
                                doc["_path"], doc["id"], extract_data=False
                            )
                            st.success(f"Re-indexed: {n} chunks")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                # Re-index + ekstraksi ulang data
                with col_re_ext:
                    if st.button("🔍 Re-index + Ekstrak", key=f"reindex_ext_{doc['id']}",
                                 help="Indeks ulang dan ekstrak data ke dashboard"):
                        try:
                            indexer = DocumentIndexer()
                            with db_session() as s:
                                s.query(DocumentChunk)\
                                 .filter_by(document_id=doc["id"]).delete()
                            n, extraction = indexer.index_document(
                                doc["_path"], doc["id"], extract_data=True
                            )
                            msg = f"Re-indexed: {n} chunks"
                            if extraction and extraction.total > 0:
                                msg += f" | Terekstrak: {extraction.summary()}"
                            st.success(msg)
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                with col_del:
                    if st.button("🗑️ Hapus", key=f"del_{doc['id']}", type="secondary"):
                        try:
                            indexer = DocumentIndexer()
                            indexer.delete_document(doc["id"])
                            if doc["_path"] and os.path.exists(doc["_path"]):
                                os.remove(doc["_path"])
                            st.success("Dokumen dihapus.")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
