"""
main.py
Streamlit entry point for Toraja Tourism RAG Dashboard.

Run:
    streamlit run main.py
"""
import streamlit as st
import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── Page Config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Pariwisata Toraja",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Dashboard Monitoring Pariwisata Toraja | RAG-powered Chatbot AI",
    },
)

# ── Global CSS Theme ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+3:wght@300;400;600&display=swap');

/* Root theme — Toraja dark gold */
:root {
    --bg-primary:   #141210;
    --bg-card:      #1E1C18;
    --gold-primary: #DAA520;
    --gold-dark:    #B8860B;
    --text-main:    #E8D8B8;
    --text-muted:   #8B7355;
}

html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
    background-color: var(--bg-primary) !important;
    color: var(--text-main) !important;
}

.stApp { background-color: var(--bg-primary) !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A1610 0%, #120F0A 100%) !important;
    border-right: 1px solid #B8860B33 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #B8860B 0%, #8B6508 100%) !important;
    color: #1A1410 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(184,134,11,0.4) !important;
}

/* Forms */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: #2A2520 !important;
    color: var(--text-main) !important;
    border: 1px solid #B8860B44 !important;
    border-radius: 8px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted) !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--gold-primary) !important;
    border-bottom: 2px solid var(--gold-primary) !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #1E1C18 !important;
    border: 1px solid #B8860B22 !important;
    border-radius: 10px !important;
    padding: 0.8rem !important;
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; }
[data-testid="stMetricValue"] { color: var(--gold-primary) !important; }

/* Expander */
.streamlit-expanderHeader {
    background: #1E1C18 !important;
    border: 1px solid #B8860B33 !important;
    border-radius: 8px !important;
    color: var(--text-main) !important;
}

/* Divider */
hr { border-color: #B8860B22 !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    background: #1E1C18 !important;
    border: 2px dashed #B8860B55 !important;
    border-radius: 12px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #1A1610; }
::-webkit-scrollbar-thumb { background: #B8860B55; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Bootstrap DB ─────────────────────────────────────────────────────────────
@st.cache_resource
def bootstrap():
    from database.connection import init_db, health_check
    from utils.auth import create_default_admin
    init_db()
    create_default_admin()
    return health_check()

db_ok = bootstrap()
if not db_ok:
    st.error("⛔ Tidak dapat terhubung ke database MySQL. Periksa konfigurasi .env")
    st.stop()

# ── Import Pages ──────────────────────────────────────────────────────────────
from app.components.sidebar      import render_sidebar
from app.user.dashboard          import render_dashboard
from app.user.data_page          import render_data_page
from app.user.login_page         import render_login_page
from app.chatbot.chatbot_page    import render_chatbot
from app.chatbot.chat_history_page import render_chat_history
from app.admin.documents_page    import render_documents_page
from app.admin.input_data_page   import render_input_data_page
from app.admin.users_page        import render_users_page

# ── Routing ───────────────────────────────────────────────────────────────────
# Tangani redirect dari halaman riwayat (tombol "Lanjutkan")
if st.session_state.get("_navigate_to"):
    target = st.session_state.pop("_navigate_to")
    st.session_state["_forced_page"] = target
    st.rerun()

page = render_sidebar()

# Override page jika ada forced navigation
if st.session_state.get("_forced_page"):
    page = st.session_state.pop("_forced_page")

# Simpan page asal agar halaman tujuan bisa menyesuaikan tampilan
if page == "register":
    st.session_state["_forced_page_was"] = "register"

PAGE_MAP = {
    "dashboard":    render_dashboard,
    "data":         render_data_page,
    "chatbot":      render_chatbot,
    "chat_history": render_chat_history,
    "login":        render_login_page,
    "register":     render_login_page,   # Halaman sama, tab register dibuka via query
    "documents":    render_documents_page,
    "input_data":   render_input_data_page,
    "users":        render_users_page,
}

renderer = PAGE_MAP.get(page, render_dashboard)
renderer()
