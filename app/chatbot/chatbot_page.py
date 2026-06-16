"""
app/chatbot/chatbot_page.py
AI Chatbot interface using RAG pipeline with streaming response and source display.
"""
import streamlit as st
import uuid
import time
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from database.connection import db_session
from database.models import ChatSession, ChatMessage
from rag.retrieval.llm_chain import LLMChain


# ─── Session Helpers ──────────────────────────────────────────────────────────
def get_or_create_session_id() -> str:
    if "chat_session_id" not in st.session_state:
        st.session_state["chat_session_id"] = str(uuid.uuid4())
    return st.session_state["chat_session_id"]


def get_chat_history() -> list:
    return st.session_state.get("chat_history", [])


def save_message(session_id: str, role: str, content: str,
                 sources: list = None, tokens: int = 0, rt: float = 0.0):
    """Persist message to DB."""
    try:
        with db_session() as s:
            db_sess = s.query(ChatSession).filter_by(session_id=session_id).first()
            if not db_sess:
                user_id = st.session_state.get("user_id")
                db_sess = ChatSession(
                    session_id=session_id,
                    user_id=user_id,
                    title=content[:50],
                )
                s.add(db_sess)
                s.flush()
            msg = ChatMessage(
                session_id=db_sess.id,
                role=role,
                content=content,
                sources=sources,
                tokens_used=tokens,
                response_time=rt,
            )
            s.add(msg)
    except Exception as e:
        pass  # Non-blocking


def load_llm_chain():
    if "llm_chain" not in st.session_state:
        st.session_state["llm_chain"] = LLMChain()
    return st.session_state["llm_chain"]


# ─── Main Page ────────────────────────────────────────────────────────────────
def render_chatbot():
    st.markdown("""
    <style>
    .chat-msg-user {
        background: var(--bg-card2);
        border: 1px solid var(--border);
        border-radius: 16px 16px 4px 16px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        color: var(--text-main);
    }
    .chat-msg-bot {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px 16px 16px 4px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        max-width: 88%;
        color: var(--text-main);
    }
    .source-chip {
        display: inline-block;
        background: var(--bg-card2);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 0.2rem 0.7rem;
        font-size: 0.75rem;
        color: var(--gold);
        margin: 0.2rem 0.2rem;
    }
    .typing-indicator { color: var(--gold); font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    col_h, col_hist, col_btn = st.columns([5, 1, 1])
    with col_h:
        st.markdown("""
        <h2 style='color:var(--gold); font-family:Georgia,serif; margin:0;'>
            💬 Chatbot AI Pariwisata Toraja
        </h2>
        <p style='color:var(--text-muted); font-size:0.85rem; margin:0.3rem 0 0 0;'>
            Tanyakan apa saja tentang wisata, budaya, akomodasi, dan event di Toraja
        </p>
        """, unsafe_allow_html=True)
    with col_hist:
        from utils.auth import is_logged_in
        if is_logged_in():
            if st.button("🕑 Riwayat", help="Lihat riwayat percakapan"):
                st.session_state["current_page"] = "chat_history"
                st.rerun()
    with col_btn:
        if st.button("🗑️ Baru", help="Mulai percakapan baru"):
            st.session_state["chat_history"] = []
            st.session_state.pop("chat_session_id", None)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    session_id = get_or_create_session_id()
    history    = get_chat_history()

    # ── Suggested Questions ───────────────────────────────────────────────────
    if not history:
        st.markdown("**💡 Pertanyaan yang sering ditanyakan:**")
        suggestions = [
            "Apa saja destinasi wisata terbaik di Toraja?",
            "Ceritakan tentang Rambu Solo dan tradisi pemakaman Toraja",
            "Hotel dan penginapan apa yang tersedia di Toraja?",
            "Kapan festival Lovely December diadakan?",
            "Bagaimana cara menuju Toraja dari Makassar?",
            "Apa itu Tongkonan dan apa maknanya?",
        ]
        cols = st.columns(2)
        for i, q in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"❓ {q}", key=f"sugg_{i}", use_container_width=True):
                    st.session_state.setdefault("chat_history", [])
                    st.session_state["pending_question"] = q
                    st.rerun()

    # ── Chat History ──────────────────────────────────────────────────────────
    for msg in history:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-msg-user'>👤 {msg['content']}</div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-msg-bot'>🤖 {msg['content']}</div>",
                        unsafe_allow_html=True)
            # Show sources
            if msg.get("sources"):
                source_chips = "".join(
                    f"<span class='source-chip'>📄 {s['source']}</span>"
                    for s in msg["sources"]
                )
                st.markdown(
                    f"<div style='margin-top:0.3rem; margin-bottom:0.7rem;'>Sumber: {source_chips}</div>",
                    unsafe_allow_html=True
                )

    # ── Handle Pending Question (from suggestion buttons) ─────────────────────
    if "pending_question" in st.session_state:
        pending = st.session_state.pop("pending_question")
        st.session_state.setdefault("chat_history", [])
        st.session_state["chat_history"].append({"role": "user", "content": pending})
        st.session_state["pending_answer"] = pending
        st.rerun()

    # ── Process Answer ────────────────────────────────────────────────────────
    if "pending_answer" in st.session_state:
        query = st.session_state.pop("pending_answer")
        with st.spinner("🤔 Mencari informasi dan menyusun jawaban..."):
            try:
                chain   = load_llm_chain()
                history_msgs = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.get("chat_history", [])[:-1]
                ]
                answer, chunks, tokens, rt = chain.chat(
                    query,
                    history    = history_msgs,
                    use_mmr    = st.session_state.get("mmr_enabled", True),
                    lambda_mmr = st.session_state.get("mmr_lambda",  0.5),
                )
                sources = [c.to_dict() for c in chunks]
            except Exception as e:
                answer  = f"Maaf, terjadi kesalahan: {str(e)}"
                sources = []
                tokens  = 0
                rt      = 0.0

        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })
        save_message(session_id, "user", query)
        save_message(session_id, "assistant", answer, sources, tokens, rt)
        st.rerun()

    # ── Input Box ─────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        cols_in = st.columns([8, 1])
        with cols_in[0]:
            user_input = st.text_input(
                "Pesan",
                placeholder="Tanyakan tentang pariwisata Toraja...",
                label_visibility="collapsed",
            )
        with cols_in[1]:
            submitted = st.form_submit_button("➤", use_container_width=True)

    if submitted and user_input.strip():
        st.session_state.setdefault("chat_history", [])
        st.session_state["chat_history"].append({
            "role": "user",
            "content": user_input.strip()
        })
        st.session_state["pending_answer"] = user_input.strip()
        st.rerun()

    # ── MMR controls ─────────────────────────────────────────────────────────
    with st.expander("⚙️ Pengaturan Retrieval (MMR)", expanded=False):
        st.markdown("**Maximal Marginal Relevance** — seimbangkan relevansi & keberagaman sumber")
        col_mmr1, col_mmr2 = st.columns(2)
        use_mmr = col_mmr1.toggle(
            "Aktifkan MMR",
            value=st.session_state.get("mmr_enabled", True),
            key="mmr_enabled",
            help="MMR memilih chunk yang relevan sekaligus beragam. Matikan untuk pure similarity.",
        )
        lambda_val = col_mmr2.slider(
            "λ — Relevance ↔ Diversity",
            min_value=0.0, max_value=1.0,
            value=st.session_state.get("mmr_lambda", 0.5),
            step=0.05,
            key="mmr_lambda",
            help="λ=0.0: maksimal diversity  ·  λ=0.5: seimbang  ·  λ=1.0: maksimal relevance",
            disabled=not use_mmr,
        )
        mode_label = f"MMR (λ={lambda_val:.2f})" if use_mmr else "Pure Similarity"
        st.caption(f"Mode aktif: **{mode_label}**")

    # ── Footer Info ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<p style='color:var(--text-muted); font-size:0.75rem; text-align:center;'>"
        "🤖 RAG + MMR · Provider: OpenRouter · Model: gpt-oss-120b · "
        "Embedding: paraphrase-multilingual-MiniLM-L12-v2"
        "</p>",
        unsafe_allow_html=True
    )
