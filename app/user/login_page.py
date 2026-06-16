"""
app/user/login_page.py
Halaman autentikasi: Login dan Daftar Akun (tab).
"""
import streamlit as st
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.auth import authenticate, login_user, register_user


_CSS = """
<style>
.auth-card {
    background: linear-gradient(160deg, #1E1B14 0%, #151210 100%);
    border: 1px solid #B8860B44;
    border-radius: 18px;
    padding: 2.2rem 2.5rem 2rem 2.5rem;
    margin-top: 1rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}
.auth-logo { text-align: center; padding-bottom: 0.8rem; }
.auth-logo h1 { font-size: 3rem; margin: 0; }
.auth-logo h2 { color: #DAA520; font-family: Georgia, serif; margin: 0.2rem 0 0.1rem 0; font-size: 1.6rem; }
.auth-logo p  { color: #8B7355; font-size: 0.85rem; margin: 0; }
.auth-divider { border: none; border-top: 1px solid #B8860B22; margin: 1.2rem 0; }
.rule-ok   { color: #4CAF50; font-size: 0.8rem; }
.rule-fail { color: #F44336; font-size: 0.8rem; }
.rule-neu  { color: #888;    font-size: 0.8rem; }
</style>
"""


def _password_rules(password: str):
    return [
        ("Minimal 6 karakter",          len(password) >= 6                    if password else None),
        ("Mengandung huruf besar (A-Z)", bool(re.search(r"[A-Z]", password))  if password else None),
        ("Mengandung huruf kecil (a-z)", bool(re.search(r"[a-z]", password))  if password else None),
        ("Mengandung angka (0-9)",       bool(re.search(r"\d",    password))  if password else None),
    ]


def _render_password_rules(password: str):
    rules = _password_rules(password)
    cols  = st.columns(2)
    for i, (text, ok) in enumerate(rules):
        with cols[i % 2]:
            if ok is None:
                st.markdown(f"<span class='rule-neu'>○ {text}</span>", unsafe_allow_html=True)
            elif ok:
                st.markdown(f"<span class='rule-ok'>✔ {text}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span class='rule-fail'>✘ {text}</span>", unsafe_allow_html=True)


def render_login_page():
    st.markdown(_CSS, unsafe_allow_html=True)

    _, col_c, _ = st.columns([1, 2, 1])

    with col_c:
        st.markdown("""
        <div class='auth-logo'>
            <h1>🏔️</h1>
            <h2>Pariwisata Toraja</h2>
            <p>Sistem Informasi &amp; Chatbot AI Wisata Toraja</p>
        </div>
        """, unsafe_allow_html=True)

        # Jika datang dari menu "📝 Daftar" di sidebar, aktifkan tab register
        import sys as _sys
        _active_tab = 1 if st.session_state.get("_forced_page_was") == "register" else 0
        st.session_state.pop("_forced_page_was", None)

        tab_login, tab_register = st.tabs(["🔑 Masuk", "📝 Daftar Akun"])

        # ── LOGIN ─────────────────────────────────────────────────────────────
        with tab_login:
            with st.form("login_form"):
                username  = st.text_input("Username",  placeholder="Masukkan username")
                password  = st.text_input("Password",  type="password", placeholder="Masukkan password")
                submitted = st.form_submit_button("🔑 Masuk", use_container_width=True, type="primary")

            if submitted:
                if not username or not password:
                    st.error("Username dan password wajib diisi.")
                else:
                    user = authenticate(username, password)
                    if user:
                        login_user(user)
                        st.success(f"Selamat datang kembali, **{user.username}**! 👋")
                        st.rerun()
                    else:
                        st.error("⛔ Username atau password salah, atau akun tidak aktif.")

            st.markdown("""
            <hr class='auth-divider'>
            <p style='text-align:center; color:#666; font-size:0.78rem;'>
                Belum punya akun? Klik tab <b>📝 Daftar Akun</b> di atas.<br>
                Pengunjung dapat melihat dashboard tanpa login.
            </p>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ── REGISTER ──────────────────────────────────────────────────────────
        with tab_register:
            st.markdown("""
            <div class='auth-card'>
            <p style='color:#A89070; font-size:0.85rem; margin:0 0 1rem 0;'>
                Buat akun untuk mengakses chatbot AI dan menyimpan riwayat percakapan.
            </p>
            """, unsafe_allow_html=True)

            # Ambil nilai live untuk indikator password (di luar form)
            reg_pw_live = st.session_state.get("_reg_pw", "")

            with st.form("register_form", clear_on_submit=False):
                reg_username = st.text_input(
                    "Username *", placeholder="Minimal 3 karakter, tanpa spasi",
                    key="_reg_uname",
                )
                reg_email = st.text_input(
                    "Email *", placeholder="contoh@email.com",
                    key="_reg_email",
                )
                reg_password = st.text_input(
                    "Password *", type="password", placeholder="Minimal 6 karakter",
                    key="_reg_pw",
                )
                reg_confirm = st.text_input(
                    "Konfirmasi Password *", type="password", placeholder="Ulangi password",
                    key="_reg_confirm",
                )
                agree = st.checkbox(
                    "Saya setuju data saya digunakan untuk keperluan sistem pariwisata Toraja.",
                    key="_reg_agree",
                )
                reg_submitted = st.form_submit_button(
                    "📝 Buat Akun", use_container_width=True, type="primary"
                )

            # Indikator kekuatan password (di luar form agar live)
            pw_val = st.session_state.get("_reg_pw", "")
            if pw_val:
                st.markdown("**Kekuatan password:**")
                _render_password_rules(pw_val)

            if reg_submitted:
                errors = []
                if not reg_username or not reg_email or not reg_password or not reg_confirm:
                    errors.append("Semua field bertanda * wajib diisi.")
                if " " in (reg_username or ""):
                    errors.append("Username tidak boleh mengandung spasi.")
                if len(reg_username or "") < 3:
                    errors.append("Username minimal 3 karakter.")
                if reg_password != reg_confirm:
                    errors.append("Password dan konfirmasi tidak cocok.")
                if len(reg_password or "") < 6:
                    errors.append("Password minimal 6 karakter.")
                if not agree:
                    errors.append("Anda harus menyetujui pernyataan di atas.")

                if errors:
                    for err in errors:
                        st.error(f"⛔ {err}")
                else:
                    success, msg = register_user(reg_username, reg_email, reg_password)
                    if success:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        st.info("👆 Silakan klik tab **🔑 Masuk** untuk login dengan akun baru Anda.")
                    else:
                        st.error(f"⛔ {msg}")

            st.markdown("""
            <hr class='auth-divider'>
            <p style='text-align:center; color:#666; font-size:0.78rem;'>
                Akun baru otomatis mendapat role <b>User</b>.<br>
                Sudah punya akun? Klik tab <b>🔑 Masuk</b>.
            </p>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
