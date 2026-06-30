"""
app/admin/users_page.py
Admin page: Tambah, Edit, Hapus, Nonaktifkan, Reset Password user.
"""
import streamlit as st
import re
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.auth import require_admin, hash_password
from database.connection import db_session
from database.models import User, ChatSession, ChatMessage


def _count_chats(user_id: int) -> int:
    with db_session() as s:
        return s.query(ChatSession).filter_by(user_id=user_id).count()


def render_users_page():
    require_admin()

    st.markdown("""
    <style>
    .user-card {
        background:var(--bg-card);
        border:1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.5rem;
    }
    .badge-admin { background:#8B1A1A; color:#FFD700; border-radius:6px; padding:2px 8px; font-size:0.75rem; font-weight:600; }
    .badge-user  { background:#1A3A1A; color:#90EE90; border-radius:6px; padding:2px 8px; font-size:0.75rem; font-weight:600; }
    .badge-off   { background:#333;    color:#888;    border-radius:6px; padding:2px 8px; font-size:0.75rem; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h2 style='color:var(--gold); font-family:Georgia,serif;'>👥 Kelola User</h2>
    <p style='color:var(--text-sub);'>Tambah, edit, reset password, dan kelola status akun pengguna.</p>
    """, unsafe_allow_html=True)

    tab_list, tab_add = st.tabs(["📋 Daftar User", "➕ Tambah User Baru"])

    # ── TAB TAMBAH ────────────────────────────────────────────────────────────
    with tab_add:
        st.markdown("#### Buat Akun Baru")
        with st.form("form_user_add", clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_uname = c1.text_input("Username *", placeholder="min. 3 karakter")
            new_email = c2.text_input("Email *",    placeholder="user@email.com")
            c3, c4 = st.columns(2)
            new_pw   = c3.text_input("Password *",  type="password", placeholder="min. 6 karakter")
            new_role = c4.selectbox("Role", ["user", "admin"])
            sub_add  = st.form_submit_button("➕ Buat Akun", type="primary")

        if sub_add:
            errors = []
            if not new_uname or not new_email or not new_pw:
                errors.append("Semua field wajib diisi.")
            if " " in (new_uname or ""):
                errors.append("Username tidak boleh mengandung spasi.")
            if len(new_uname or "") < 3:
                errors.append("Username minimal 3 karakter.")
            if len(new_pw or "") < 6:
                errors.append("Password minimal 6 karakter.")
            if "@" not in (new_email or "") or "." not in (new_email or "").split("@")[-1]:
                errors.append("Format email tidak valid.")

            if errors:
                for e in errors:
                    st.error(f"⛔ {e}")
            else:
                add_ok = False
                with db_session() as s:
                    if s.query(User).filter_by(username=new_uname).first():
                        st.error(f"⛔ Username '{new_uname}' sudah digunakan.")
                    elif s.query(User).filter_by(email=new_email.lower()).first():
                        st.error("⛔ Email sudah terdaftar.")
                    else:
                        s.add(User(
                            username=new_uname.strip(),
                            email=new_email.lower().strip(),
                            password=hash_password(new_pw),
                            role=new_role, is_active=True,
                        ))
                        add_ok = True
                # st.rerun() dipanggil SETELAH commit selesai (di luar with db_session()),
                # agar tidak ter-rollback oleh RerunException.
                if add_ok:
                    st.success(f"✅ Akun **{new_uname}** ({new_role}) berhasil dibuat.")
                    st.rerun()

    # ── TAB DAFTAR ────────────────────────────────────────────────────────────
    with tab_list:
        # ── Filter & Search ───────────────────────────────────────────────────
        col_s, col_r, col_st = st.columns([3, 2, 2])
        search_u   = col_s.text_input("🔍 Cari username / email",
                                      placeholder="Ketik untuk mencari...",
                                      label_visibility="collapsed")
        role_f     = col_r.selectbox("Filter Role",   ["Semua", "admin", "user"])
        status_f   = col_st.selectbox("Filter Status", ["Semua", "Aktif", "Nonaktif"])

        with db_session() as s:
            q = s.query(User)
            if role_f != "Semua":
                q = q.filter_by(role=role_f)
            if status_f == "Aktif":
                q = q.filter_by(is_active=True)
            elif status_f == "Nonaktif":
                q = q.filter_by(is_active=False)
            users_raw = q.order_by(User.role, User.username).all()
            users_data = [{
                "id":         u.id,
                "username":   u.username,
                "email":      u.email,
                "role":       u.role,
                "is_active":  u.is_active,
                "created_at": u.created_at,
                "updated_at": u.updated_at,
            } for u in users_raw]

        if search_u:
            kw = search_u.lower()
            users_data = [u for u in users_data
                          if kw in u["username"].lower() or kw in u["email"].lower()]

        # ── Summary ───────────────────────────────────────────────────────────
        total   = len(users_data)
        n_admin = sum(1 for u in users_data if u["role"] == "admin")
        n_user  = sum(1 for u in users_data if u["role"] == "user")
        n_aktif = sum(1 for u in users_data if u["is_active"])

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Total User",  total)
        mc2.metric("Admin",       n_admin)
        mc3.metric("User Biasa",  n_user)
        mc4.metric("Aktif",       n_aktif)
        st.markdown("---")

        if not users_data:
            st.info("Tidak ada user yang cocok dengan filter.")
            return

        current_uid = st.session_state.get("user_id")

        for u in users_data:
            uid = u["id"]
            is_self = uid == current_uid
            role_badge = (
                "<span class='badge-admin'>🛡️ admin</span>" if u["role"] == "admin"
                else "<span class='badge-user'>👤 user</span>"
            )
            status_badge = (
                "<span style='color:#4CAF50; font-size:0.8rem;'>● Aktif</span>" if u["is_active"]
                else "<span class='badge-off'>● Nonaktif</span>"
            )
            joined = u["created_at"].strftime("%d %b %Y") if u["created_at"] else "-"

            with st.expander(
                f"{'🛡️' if u['role']=='admin' else '👤'} {u['username']}  ·  {u['email']}",
                expanded=False
            ):
                # ── Info ─────────────────────────────────────────────────────
                st.markdown(
                    f"{role_badge} &nbsp; {status_badge} &nbsp;"
                    f"<span style='color:var(--text-muted); font-size:0.8rem;'>Bergabung: {joined}</span>",
                    unsafe_allow_html=True
                )
                n_chat = _count_chats(uid)
                st.caption(f"💬 Total sesi chat: {n_chat}")

                if is_self:
                    st.info("🔒 Ini adalah akun Anda sendiri. Edit melalui halaman Profil.")
                    continue

                # ── Aksi utama ────────────────────────────────────────────────
                bt1, bt2, bt3, bt4, _ = st.columns([1.2, 1.2, 1.5, 1.2, 2])

                if bt1.button("✏️ Edit",     key=f"edit_u_{uid}"):
                    st.session_state["editing_user"] = uid
                    st.session_state.pop(f"resetting_pw_{uid}", None)

                toggle_lbl = "🔴 Nonaktif" if u["is_active"] else "🟢 Aktifkan"
                if bt2.button(toggle_lbl, key=f"tog_u_{uid}"):
                    with db_session() as s:
                        usr = s.query(User).filter_by(id=uid).first()
                        if usr:
                            usr.is_active    = not usr.is_active
                            usr.updated_at   = datetime.utcnow()
                    st.rerun()

                if bt3.button("🔑 Reset PW",  key=f"rpw_u_{uid}"):
                    st.session_state[f"resetting_pw_{uid}"] = True
                    st.session_state.pop("editing_user", None)

                if bt4.button("🗑️ Hapus",    key=f"del_u_{uid}"):
                    st.session_state[f"confirm_del_u_{uid}"] = True

                # ── Konfirmasi hapus ──────────────────────────────────────────
                if st.session_state.get(f"confirm_del_u_{uid}"):
                    st.warning(
                        f"⚠️ Hapus akun **{u['username']}**? "
                        f"Semua data sesi chat miliknya juga akan terhapus."
                    )
                    dc1, dc2 = st.columns(2)
                    if dc1.button("✅ Ya, Hapus", key=f"yes_del_u_{uid}", type="primary"):
                        with db_session() as s:
                            # Hapus chat messages → sessions → user
                            sess_ids = [
                                sid for (sid,) in
                                s.query(ChatSession.id).filter_by(user_id=uid).all()
                            ]
                            if sess_ids:
                                s.query(ChatMessage)\
                                 .filter(ChatMessage.session_id.in_(sess_ids)).delete(synchronize_session=False)
                            s.query(ChatSession).filter_by(user_id=uid).delete()
                            s.query(User).filter_by(id=uid).delete()
                        st.session_state.pop(f"confirm_del_u_{uid}", None)
                        st.success(f"Akun **{u['username']}** dihapus.")
                        st.rerun()
                    if dc2.button("❌ Batal", key=f"no_del_u_{uid}"):
                        st.session_state.pop(f"confirm_del_u_{uid}", None)
                        st.rerun()

                # ── Form Edit Data User ───────────────────────────────────────
                if st.session_state.get("editing_user") == uid:
                    st.markdown("##### ✏️ Edit Data User")
                    with st.form(f"form_edit_user_{uid}"):
                        ec1, ec2 = st.columns(2)
                        e_uname = ec1.text_input("Username *",  value=u["username"])
                        e_email = ec2.text_input("Email *",     value=u["email"])
                        e_role  = st.selectbox("Role", ["user", "admin"],
                                               index=0 if u["role"] == "user" else 1)
                        sb1, sb2 = st.columns(2)
                        sv = sb1.form_submit_button("💾 Simpan", type="primary")
                        cx = sb2.form_submit_button("✖️ Batal")

                    if sv:
                        errors = []
                        if not e_uname.strip():
                            errors.append("Username tidak boleh kosong.")
                        if " " in e_uname:
                            errors.append("Username tidak boleh mengandung spasi.")
                        if len(e_uname) < 3:
                            errors.append("Username minimal 3 karakter.")
                        if "@" not in e_email or "." not in e_email.split("@")[-1]:
                            errors.append("Format email tidak valid.")

                        if errors:
                            for e in errors:
                                st.error(f"⛔ {e}")
                        else:
                            update_ok = False
                            with db_session() as s:
                                # Cek duplikat username/email (selain user ini sendiri)
                                dup_u = s.query(User).filter(
                                    User.username == e_uname.strip(),
                                    User.id != uid
                                ).first()
                                dup_e = s.query(User).filter(
                                    User.email == e_email.lower().strip(),
                                    User.id != uid
                                ).first()
                                if dup_u:
                                    st.error(f"⛔ Username '{e_uname}' sudah digunakan akun lain.")
                                elif dup_e:
                                    st.error("⛔ Email sudah digunakan akun lain.")
                                else:
                                    usr = s.query(User).filter_by(id=uid).first()
                                    if usr:
                                        usr.username   = e_uname.strip()
                                        usr.email      = e_email.lower().strip()
                                        usr.role       = e_role
                                        usr.updated_at = datetime.utcnow()
                                    update_ok = True
                            # st.rerun() dan st.success() dipanggil SETELAH `with db_session()`
                            # selesai (commit sudah terjadi), supaya tidak ter-rollback oleh
                            # RerunException yang dilempar st.rerun().
                            if update_ok:
                                st.session_state.pop("editing_user", None)
                                st.success(f"✅ Data user **{e_uname}** berhasil diperbarui.")
                                st.rerun()
                    if cx:
                        st.session_state.pop("editing_user", None)
                        st.rerun()

                # ── Form Reset Password ────────────────────────────────────────
                if st.session_state.get(f"resetting_pw_{uid}"):
                    st.markdown("##### 🔑 Reset Password")
                    with st.form(f"form_reset_pw_{uid}"):
                        new_pw1 = st.text_input("Password Baru *",    type="password",
                                                 placeholder="minimal 6 karakter")
                        new_pw2 = st.text_input("Konfirmasi Password *", type="password",
                                                 placeholder="ulangi password baru")
                        pb1, pb2 = st.columns(2)
                        sv_pw = pb1.form_submit_button("🔑 Reset", type="primary")
                        cx_pw = pb2.form_submit_button("✖️ Batal")

                    if sv_pw:
                        if not new_pw1 or not new_pw2:
                            st.error("⛔ Password baru dan konfirmasi wajib diisi.")
                        elif len(new_pw1) < 6:
                            st.error("⛔ Password minimal 6 karakter.")
                        elif new_pw1 != new_pw2:
                            st.error("⛔ Password dan konfirmasi tidak cocok.")
                        else:
                            with db_session() as s:
                                usr = s.query(User).filter_by(id=uid).first()
                                if usr:
                                    usr.password   = hash_password(new_pw1)
                                    usr.updated_at = datetime.utcnow()
                            st.session_state.pop(f"resetting_pw_{uid}", None)
                            st.success(f"✅ Password **{u['username']}** berhasil direset.")
                            st.rerun()
                    if cx_pw:
                        st.session_state.pop(f"resetting_pw_{uid}", None)
                        st.rerun()
