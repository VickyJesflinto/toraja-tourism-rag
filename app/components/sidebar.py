"""
app/components/sidebar.py
Reusable sidebar navigation component for the Streamlit app.
"""
import streamlit as st
from utils.auth import is_logged_in, is_admin, logout_user


def render_sidebar():
    """Render navigation sidebar. Returns selected page name."""
    with st.sidebar:
        # Branding
        st.markdown("""
        <div style='text-align:center; padding: 1rem 0;'>
            <h2 style='color:#B8860B; font-family: Georgia, serif; margin:0;'>Toraja</h2>
            <p style='color:#8B7355; font-size:0.8rem; margin:0;'>Sistem Informasi Pariwisata</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        if is_logged_in():
            username = st.session_state.get("username", "User")
            role     = st.session_state.get("role", "user")
            st.markdown(f"👤 **{username}** `{role}`")
            st.divider()

        # Navigation
        if is_admin():
            pages = {
                "Dashboard":        "dashboard",
                "Data Pariwisata":  "data",
                "Chatbot AI":       "chatbot",
                "Riwayat Chat":     "chat_history",
                "Kelola Dokumen":   "documents",
                "Input Data":       "input_data",
                "Kelola User":      "users",
            }
        elif is_logged_in():
            pages = {
                "Dashboard":        "dashboard",
                "Data Pariwisata":  "data",
                "Chatbot AI":       "chatbot",
                "Riwayat Chat":     "chat_history",
            }
        else:
            pages = {
                "Dashboard":  "dashboard",
                "Chatbot AI": "chatbot",
                "Login":      "login",
            }

        selection = st.radio(
            "Navigasi",
            list(pages.keys()),
            label_visibility="collapsed",
        )

        if is_logged_in():
            st.divider()
            if st.button("Logout", use_container_width=True):
                logout_user()
                st.rerun()

        st.divider()
        st.markdown(
            "<p style='font-size:0.7rem; color:#999; text-align:center;'>"
            "© 2026 Skripsi SI | Pariwisata Toraja</p>",
            unsafe_allow_html=True
        )

        return pages[selection]
