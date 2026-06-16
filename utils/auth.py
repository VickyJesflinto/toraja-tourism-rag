"""
utils/auth.py
Password hashing, session management, and role-based access helpers.
"""
import hashlib
import hmac
import uuid
from typing import Optional
import streamlit as st
from loguru import logger
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.settings import APP_SECRET_KEY
from database.connection import db_session
from database.models import User


def hash_password(password: str) -> str:
    """Return bcrypt-like hash using PBKDF2."""
    import hashlib
    salt = APP_SECRET_KEY.encode()
    dk   = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return dk.hex()


def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)


def authenticate(username: str, password: str) -> Optional[User]:
    """Return User if credentials valid, else None."""
    with db_session() as session:
        user = session.query(User).filter_by(username=username, is_active=True).first()
        if user and verify_password(password, user.password):
            session.expunge(user)
            return user
    return None


# ─── Streamlit Session Helpers ────────────────────────────────────────────────
def login_user(user: User):
    st.session_state["logged_in"]  = True
    st.session_state["user_id"]    = user.id
    st.session_state["username"]   = user.username
    st.session_state["role"]       = user.role
    st.session_state["session_id"] = str(uuid.uuid4())


def logout_user():
    for key in ["logged_in", "user_id", "username", "role", "session_id"]:
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"


def require_login():
    if not is_logged_in():
        st.error("⛔ Anda harus login untuk mengakses halaman ini.")
        st.stop()


def require_admin():
    require_login()
    if not is_admin():
        st.error("⛔ Halaman ini hanya untuk Admin.")
        st.stop()


def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """
    Daftarkan user baru dengan role 'user'.
    Returns (success: bool, message: str).
    """
    # Validasi panjang
    if len(username) < 3:
        return False, "Username minimal 3 karakter."
    if len(username) > 100:
        return False, "Username maksimal 100 karakter."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    if "@" not in email or "." not in email.split("@")[-1]:
        return False, "Format email tidak valid."

    try:
        with db_session() as session:
            if session.query(User).filter_by(username=username).first():
                return False, f"Username '{username}' sudah digunakan."
            if session.query(User).filter_by(email=email.lower()).first():
                return False, "Email sudah terdaftar."
            new_user = User(
                username=username.strip(),
                email=email.lower().strip(),
                password=hash_password(password),
                role="user",
                is_active=True,
            )
            session.add(new_user)
            session.flush()
            # Return plain object sebelum session close
            uid  = new_user.id
            uname = new_user.username
        logger.info(f"New user registered: '{uname}' (id={uid})")
        return True, "Akun berhasil dibuat! Silakan login."
    except Exception as e:
        logger.error(f"Register error: {e}")
        return False, f"Terjadi kesalahan sistem: {str(e)}"


def create_default_admin():
    """Create default admin if none exists."""
    with db_session() as session:
        existing = session.query(User).filter_by(role="admin").first()
        if not existing:
            from config.settings import ADMIN_USERNAME, ADMIN_PASSWORD
            admin = User(
                username=ADMIN_USERNAME,
                email="admin@torajapariwisata.id",
                password=hash_password(ADMIN_PASSWORD),
                role="admin",
            )
            session.add(admin)
            logger.info(f"Default admin '{ADMIN_USERNAME}' created.")
