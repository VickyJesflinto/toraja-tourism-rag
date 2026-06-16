"""
app/chatbot/chat_history_page.py
Halaman riwayat percakapan chatbot.

Fitur:
- Daftar semua sesi chat (judul, tanggal, jumlah pesan)
- Klik sesi → lihat seluruh percakapan lengkap beserta sumber RAG
- Lanjutkan percakapan dari sesi lama
- Hapus sesi (oleh pemilik atau admin)
- Pencarian berdasarkan kata kunci di dalam pesan
- Statistik ringkas: total sesi, total pesan, rata-rata token
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.auth import require_login, is_admin
from database.connection import db_session
from database.models import ChatSession, ChatMessage, User


# ─── Data helpers ─────────────────────────────────────────────────────────────
def load_sessions(user_id: int, is_admin_user: bool) -> list[dict]:
    """
    Admin  → semua sesi semua user.
    User   → hanya sesi miliknya sendiri.
    """
    with db_session() as s:
        q = s.query(ChatSession)
        if not is_admin_user:
            q = q.filter(ChatSession.user_id == user_id)
        sessions = q.order_by(ChatSession.updated_at.desc()).all()

        result = []
        for sess in sessions:
            msg_count = (
                s.query(ChatMessage)
                .filter_by(session_id=sess.id)
                .count()
            )
            # Total token untuk sesi ini
            from sqlalchemy import func
            total_tokens = (
                s.query(func.sum(ChatMessage.tokens_used))
                .filter_by(session_id=sess.id)
                .scalar() or 0
            )
            owner = None
            if sess.user_id:
                u = s.query(User).filter_by(id=sess.user_id).first()
                owner = u.username if u else "Guest"
            else:
                owner = "Guest"

            result.append({
                "id":           sess.id,
                "session_id":   sess.session_id,
                "title":        sess.title or "Percakapan",
                "owner":        owner,
                "msg_count":    msg_count,
                "total_tokens": int(total_tokens),
                "created_at":   sess.created_at,
                "updated_at":   sess.updated_at,
            })
    return result


def load_messages(session_db_id: int) -> list[dict]:
    """Ambil semua pesan dari satu sesi, urut dari awal."""
    with db_session() as s:
        msgs = (
            s.query(ChatMessage)
            .filter_by(session_id=session_db_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        return [{
            "id":            m.id,
            "role":          m.role,
            "content":       m.content,
            "sources":       m.sources or [],
            "tokens_used":   m.tokens_used,
            "response_time": m.response_time,
            "created_at":    m.created_at,
        } for m in msgs]


def delete_session(session_db_id: int):
    with db_session() as s:
        s.query(ChatMessage).filter_by(session_id=session_db_id).delete()
        s.query(ChatSession).filter_by(id=session_db_id).delete()


def search_sessions(sessions: list[dict], keyword: str) -> list[dict]:
    """Filter sesi berdasarkan judul atau cari keyword di dalam pesan."""
    kw = keyword.lower().strip()
    if not kw:
        return sessions

    matched = []
    for sess in sessions:
        # Cek judul dulu (cepat)
        if kw in sess["title"].lower():
            matched.append(sess)
            continue
        # Cek isi pesan
        msgs = load_messages(sess["id"])
        if any(kw in m["content"].lower() for m in msgs):
            matched.append(sess)
    return matched


# ─── UI helpers ───────────────────────────────────────────────────────────────
def fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return "-"
    now = datetime.utcnow()
    diff = now - dt
    if diff < timedelta(minutes=1):
        return "Baru saja"
    if diff < timedelta(hours=1):
        return f"{int(diff.total_seconds() // 60)} menit lalu"
    if diff < timedelta(days=1):
        return f"{int(diff.total_seconds() // 3600)} jam lalu"
    if diff < timedelta(days=7):
        return f"{diff.days} hari lalu"
    return dt.strftime("%d %b %Y %H:%M")


def render_message_bubble(msg: dict):
    """Render satu bubble pesan beserta sumber RAG-nya."""
    role    = msg["role"]
    content = msg["content"]
    ts      = fmt_dt(msg.get("created_at"))

    if role == "user":
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #2D2418 0%, #251E12 100%);
            border: 1px solid #B8860B44;
            border-radius: 16px 16px 4px 16px;
            padding: 0.9rem 1.1rem;
            margin: 0.4rem 0 0.4rem 15%;
            color: #E8D5A3;
        '>
            <div style='font-size:0.72rem; color:#8B7355; margin-bottom:0.3rem;'>
                👤 Pengguna &nbsp;·&nbsp; {ts}
            </div>
            {content}
        </div>
        """, unsafe_allow_html=True)

    elif role == "assistant":
        sources_html = ""
        if msg.get("sources"):
            chips = "".join(
                f"<span style='"
                f"display:inline-block; background:#2A2010; border:1px solid #B8860B55;"
                f"border-radius:20px; padding:0.15rem 0.6rem; font-size:0.72rem;"
                f"color:#DAA520; margin:0.15rem 0.15rem;'>"
                f"📄 {src.get('source','?')}"
                f"</span>"
                for src in msg["sources"]
            )
            sources_html = (
                f"<div style='margin-top:0.5rem; padding-top:0.4rem;"
                f"border-top:1px solid #B8860B22;'>"
                f"<span style='font-size:0.72rem; color:#8B7355;'>Sumber RAG:</span> {chips}"
                f"</div>"
            )

        meta = ""
        if msg.get("tokens_used"):
            meta += f"🔢 {msg['tokens_used']} token"
        if msg.get("response_time"):
            meta += f" &nbsp;·&nbsp; ⏱️ {msg['response_time']:.1f}s"

        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #1E2530 0%, #161D28 100%);
            border: 1px solid #4A7BA744;
            border-radius: 16px 16px 16px 4px;
            padding: 0.9rem 1.1rem;
            margin: 0.4rem 15% 0.4rem 0;
            color: #C8D8E8;
        '>
            <div style='font-size:0.72rem; color:#8B7355; margin-bottom:0.3rem;'>
                🤖 Asisten AI &nbsp;·&nbsp; {ts}
                {(" &nbsp;·&nbsp; " + meta) if meta else ""}
            </div>
            {content}
            {sources_html}
        </div>
        """, unsafe_allow_html=True)


# ─── Main Page ────────────────────────────────────────────────────────────────
def render_chat_history():
    require_login()

    st.markdown("""
    <style>
    .hist-card {
        background: linear-gradient(135deg, #1E1C18 0%, #181510 100%);
        border: 1px solid #B8860B33;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        cursor: pointer;
        transition: border-color 0.2s;
    }
    .hist-card:hover { border-color: #B8860B99; }
    .hist-title { color: #DAA520; font-weight: 600; font-size: 1rem; }
    .hist-meta  { color: #8B7355; font-size: 0.78rem; margin-top: 0.2rem; }
    .stat-pill  {
        display: inline-block;
        background: #2A2010;
        border: 1px solid #B8860B44;
        border-radius: 20px;
        padding: 0.25rem 0.8rem;
        font-size: 0.8rem;
        color: #DAA520;
        margin: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    user_id       = st.session_state.get("user_id")
    admin_mode    = is_admin()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <h2 style='color:#DAA520; font-family:Georgia,serif; margin:0;'>
        🕑 Riwayat Percakapan
    </h2>
    <p style='color:#8B7355; font-size:0.85rem; margin:0.3rem 0 1rem 0;'>
        Lihat kembali percakapan yang pernah dilakukan dengan Chatbot AI
    </p>
    """, unsafe_allow_html=True)

    # ── Load sessions ─────────────────────────────────────────────────────────
    all_sessions = load_sessions(user_id, admin_mode)

    if not all_sessions:
        st.info("Belum ada riwayat percakapan. Mulai chat di menu **💬 Chatbot AI**!")
        return

    # ── Summary stats ─────────────────────────────────────────────────────────
    total_msg    = sum(s["msg_count"]    for s in all_sessions)
    total_tokens = sum(s["total_tokens"] for s in all_sessions)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='stat-pill'>💬 {len(all_sessions)} Sesi</div>",      unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-pill'>📨 {total_msg} Pesan</div>",             unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-pill'>🔢 {total_tokens:,} Token</div>",         unsafe_allow_html=True)
    c4.markdown(f"<div class='stat-pill'>👥 {'Semua User' if admin_mode else 'Milik Saya'}</div>",
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Search ────────────────────────────────────────────────────────────────
    col_s, col_f = st.columns([4, 2])
    with col_s:
        keyword = st.text_input("🔍 Cari percakapan",
                                placeholder="Kata kunci dalam judul atau isi pesan...")
    with col_f:
        sort_by = st.selectbox("Urutkan", ["Terbaru", "Terlama", "Pesan Terbanyak", "Token Terbanyak"])

    # Filter & sort
    sessions = search_sessions(all_sessions, keyword) if keyword else all_sessions[:]

    sort_map = {
        "Terbaru":         lambda x: x["updated_at"] or datetime.min,
        "Terlama":         lambda x: x["updated_at"] or datetime.min,
        "Pesan Terbanyak": lambda x: x["msg_count"],
        "Token Terbanyak": lambda x: x["total_tokens"],
    }
    reverse = sort_by != "Terlama"
    sessions = sorted(sessions, key=sort_map[sort_by], reverse=reverse)

    if not sessions:
        st.warning(f"Tidak ada percakapan yang cocok dengan kata kunci **'{keyword}'**.")
        return

    st.markdown(f"<p style='color:#8B7355; font-size:0.82rem;'>Menampilkan {len(sessions)} sesi</p>",
                unsafe_allow_html=True)
    st.markdown("---")

    # ── Session list + detail ─────────────────────────────────────────────────
    # Jika ada sesi yang sedang dibuka detail-nya
    open_id = st.session_state.get("open_history_id")

    for sess in sessions:
        sid = sess["id"]
        is_open = open_id == sid

        # ── Session card header ───────────────────────────────────────────────
        col_info, col_acts = st.columns([6, 2])

        with col_info:
            owner_label = f" &nbsp;·&nbsp; 👤 {sess['owner']}" if admin_mode else ""
            st.markdown(f"""
            <div class='hist-card'>
                <div class='hist-title'>💬 {sess['title']}</div>
                <div class='hist-meta'>
                    📅 {fmt_dt(sess['updated_at'])}
                    &nbsp;·&nbsp; 📨 {sess['msg_count']} pesan
                    &nbsp;·&nbsp; 🔢 {sess['total_tokens']:,} token
                    {owner_label}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_acts:
            st.markdown("<div style='margin-top:0.5rem;'>", unsafe_allow_html=True)
            btn_col1, btn_col2, btn_col3 = st.columns(3)

            # Tombol Buka / Tutup
            label_toggle = "🔼 Tutup" if is_open else "🔽 Buka"
            if btn_col1.button(label_toggle, key=f"toggle_{sid}", use_container_width=True):
                if is_open:
                    st.session_state.pop("open_history_id", None)
                else:
                    st.session_state["open_history_id"] = sid
                st.rerun()

            # Tombol Lanjutkan chat
            if btn_col2.button("▶️ Lanjut", key=f"cont_{sid}",
                               help="Lanjutkan percakapan ini",
                               use_container_width=True):
                _resume_session(sess)
                st.rerun()

            # Tombol Hapus (pemilik atau admin)
            can_delete = admin_mode or (sess["owner"] != "Guest" and
                                        sess["owner"] == st.session_state.get("username"))
            if can_delete:
                if btn_col3.button("🗑️", key=f"del_{sid}",
                                   help="Hapus sesi ini",
                                   use_container_width=True):
                    st.session_state[f"confirm_del_{sid}"] = True

            st.markdown("</div>", unsafe_allow_html=True)

        # Konfirmasi hapus
        if st.session_state.get(f"confirm_del_{sid}"):
            st.warning(f"⚠️ Yakin ingin menghapus sesi **'{sess['title']}'**? Tindakan ini tidak bisa dibatalkan.")
            cc1, cc2 = st.columns(2)
            if cc1.button("✅ Ya, Hapus", key=f"yes_del_{sid}", type="primary"):
                delete_session(sid)
                st.session_state.pop(f"confirm_del_{sid}", None)
                if open_id == sid:
                    st.session_state.pop("open_history_id", None)
                st.success("Sesi berhasil dihapus.")
                st.rerun()
            if cc2.button("❌ Batal", key=f"no_del_{sid}"):
                st.session_state.pop(f"confirm_del_{sid}", None)
                st.rerun()

        # ── Detail percakapan (expanded) ──────────────────────────────────────
        if is_open:
            messages = load_messages(sid)
            if not messages:
                st.info("Sesi ini tidak memiliki pesan.")
            else:
                with st.container():
                    st.markdown(f"""
                    <div style='
                        background: #111009;
                        border: 1px solid #B8860B22;
                        border-radius: 12px;
                        padding: 1rem 1.2rem;
                        margin: 0 0 1rem 0;
                    '>
                        <p style='color:#8B7355; font-size:0.8rem; margin:0 0 0.8rem 0;'>
                            📋 {len(messages)} pesan &nbsp;·&nbsp;
                            📅 Dimulai {fmt_dt(messages[0]['created_at'])}
                        </p>
                    """, unsafe_allow_html=True)

                    for msg in messages:
                        render_message_bubble(msg)

                    st.markdown("</div>", unsafe_allow_html=True)

                    # Export tombol
                    export_col, _ = st.columns([2, 4])
                    with export_col:
                        if st.button("📥 Export sebagai teks", key=f"export_{sid}"):
                            text = _export_session_text(sess, messages)
                            st.download_button(
                                label="💾 Download .txt",
                                data=text,
                                file_name=f"chat_{sess['session_id'][:8]}.txt",
                                mime="text/plain",
                                key=f"dl_{sid}",
                            )

        st.markdown("<hr style='border-color:#B8860B11; margin: 0.3rem 0;'>",
                    unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _resume_session(sess: dict):
    """Load sesi lama ke st.session_state agar bisa dilanjutkan di chatbot page."""
    messages = load_messages(sess["id"])
    history  = []
    for m in messages:
        if m["role"] in ("user", "assistant"):
            history.append({
                "role":    m["role"],
                "content": m["content"],
                "sources": m.get("sources", []),
            })
    st.session_state["chat_history"]   = history
    st.session_state["chat_session_id"] = sess["session_id"]
    # Arahkan ke halaman chatbot
    st.session_state["_navigate_to"]   = "chatbot"


def _export_session_text(sess: dict, messages: list[dict]) -> str:
    lines = [
        f"=== Riwayat Percakapan: {sess['title']} ===",
        f"Sesi ID : {sess['session_id']}",
        f"Tanggal : {sess['created_at'].strftime('%d %b %Y %H:%M') if sess['created_at'] else '-'}",
        f"Pengguna: {sess['owner']}",
        f"Total   : {len(messages)} pesan",
        "=" * 60,
        "",
    ]
    for m in messages:
        label = "👤 PENGGUNA" if m["role"] == "user" else "🤖 ASISTEN"
        ts    = fmt_dt(m.get("created_at"))
        lines.append(f"[{ts}] {label}")
        lines.append(m["content"])
        if m.get("sources"):
            srcs = ", ".join(s.get("source","?") for s in m["sources"])
            lines.append(f"  Sumber: {srcs}")
        lines.append("")
    return "\n".join(lines)
