"""
tests/test_integration_auth_rbac.py

Integration Test: Autentikasi -> Session State -> Role-Based Access Control
================================================================================
Menguji alur lengkap dari proses login sampai pengecekan hak akses, yang
melibatkan database (autentikasi user) dan session state Streamlit
(login_user, is_admin, require_admin) bekerja bersama -- berbeda dari unit
test_auth.py yang menguji setiap fungsi secara terisolasi.

Skenario yang diuji meniru alur nyata pemakaian aplikasi:
1. User register -> langsung mencoba login -> berhasil
2. Login dengan akun admin -> mengakses fungsi yang memerlukan require_admin()
3. Login dengan akun user biasa -> ditolak saat mengakses fungsi admin
4. Akun yang dinonaktifkan (is_active=False) tidak bisa login sama sekali
5. Logout benar-benar membersihkan seluruh session
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


class TestRegisterThenLoginFlow:
    def test_register_then_authenticate_succeeds(self, test_db):
        from utils.auth import register_user, authenticate

        success, _ = register_user("integrationuser", "integration@test.com", "password123")
        assert success is True

        user = authenticate("integrationuser", "password123")
        assert user is not None
        assert user.username == "integrationuser"
        assert user.role == "user"

    def test_register_then_login_then_session_state_correct(self, test_db):
        from utils.auth import register_user, authenticate, login_user, is_logged_in, is_admin

        register_user("sessionuser", "session@test.com", "mypassword")
        user = authenticate("sessionuser", "mypassword")
        login_user(user)

        assert is_logged_in() is True
        assert is_admin() is False

    def test_wrong_password_after_register_fails_authentication(self, test_db):
        from utils.auth import register_user, authenticate

        register_user("wrongpwuser", "wrongpw@test.com", "correctpassword")
        result = authenticate("wrongpwuser", "incorrectpassword")
        assert result is None


class TestAdminAccessControl:
    def test_admin_login_passes_require_admin_check(self, test_db, monkeypatch):
        from utils.auth import register_user, login_user, require_admin
        from database.connection import db_session
        from database.models import User

        register_user("adminintegration", "admin_i@test.com", "adminpass123")
        with db_session() as s:
            u = s.query(User).filter_by(username="adminintegration").first()
            u.role = "admin"

        with db_session() as s:
            admin_user = s.query(User).filter_by(username="adminintegration").first()
            login_user(admin_user)

        errors = []
        import streamlit as st
        monkeypatch.setattr(st, "error", lambda msg: errors.append(msg))
        monkeypatch.setattr(st, "stop", lambda: None)

        require_admin()

        assert errors == [], "require_admin() seharusnya tidak menampilkan error untuk akun admin"

    def test_regular_user_login_blocked_by_require_admin(self, test_db, monkeypatch):
        from utils.auth import register_user, authenticate, login_user, require_admin

        register_user("biasauser", "biasa@test.com", "password123")
        user = authenticate("biasauser", "password123")
        login_user(user)

        errors = []
        import streamlit as st
        monkeypatch.setattr(st, "error", lambda msg: errors.append(msg))
        monkeypatch.setattr(st, "stop", lambda: None)

        require_admin()

        assert len(errors) > 0
        assert any("admin" in e.lower() for e in errors)

    def test_guest_not_logged_in_blocked_by_require_login(self, monkeypatch):
        import streamlit as st
        from utils.auth import require_login

        st.session_state.clear()

        errors = []
        monkeypatch.setattr(st, "error", lambda msg: errors.append(msg))
        monkeypatch.setattr(st, "stop", lambda: None)

        require_login()

        assert len(errors) > 0
        assert any("login" in e.lower() for e in errors)

    def test_guest_not_logged_in_also_blocked_by_require_admin(self, monkeypatch):
        import streamlit as st
        from utils.auth import require_admin

        st.session_state.clear()

        errors = []
        monkeypatch.setattr(st, "error", lambda msg: errors.append(msg))
        monkeypatch.setattr(st, "stop", lambda: None)

        require_admin()

        assert len(errors) > 0


class TestInactiveAccountFlow:
    def test_deactivated_account_cannot_authenticate(self, test_db):
        from utils.auth import register_user, authenticate
        from database.connection import db_session
        from database.models import User

        register_user("willbedeactivated", "deact@test.com", "stillvalidpassword")

        with db_session() as s:
            u = s.query(User).filter_by(username="willbedeactivated").first()
            u.is_active = False

        result = authenticate("willbedeactivated", "stillvalidpassword")
        assert result is None

    def test_reactivated_account_can_authenticate_again(self, test_db):
        from utils.auth import register_user, authenticate
        from database.connection import db_session
        from database.models import User

        register_user("reactivateuser", "react@test.com", "samepassword")

        with db_session() as s:
            u = s.query(User).filter_by(username="reactivateuser").first()
            u.is_active = False

        assert authenticate("reactivateuser", "samepassword") is None

        with db_session() as s:
            u = s.query(User).filter_by(username="reactivateuser").first()
            u.is_active = True

        result = authenticate("reactivateuser", "samepassword")
        assert result is not None


class TestLogoutClearsSessionCompletely:
    def test_logout_then_require_login_blocks_access(self, test_db, monkeypatch):
        from utils.auth import (
            register_user, authenticate, login_user, logout_user,
            require_login, is_logged_in,
        )
        import streamlit as st

        register_user("logoutflowuser", "logout@test.com", "password123")
        user = authenticate("logoutflowuser", "password123")
        login_user(user)
        assert is_logged_in() is True

        logout_user()
        assert is_logged_in() is False

        errors = []
        monkeypatch.setattr(st, "error", lambda msg: errors.append(msg))
        monkeypatch.setattr(st, "stop", lambda: None)

        require_login()
        assert len(errors) > 0

    def test_logout_removes_admin_privilege_from_session(self, test_db):
        from utils.auth import register_user, login_user, logout_user, is_admin
        from database.connection import db_session
        from database.models import User

        register_user("logoutadmin", "logoutadmin@test.com", "password123")
        with db_session() as s:
            u = s.query(User).filter_by(username="logoutadmin").first()
            u.role = "admin"

        with db_session() as s:
            admin_user = s.query(User).filter_by(username="logoutadmin").first()
            login_user(admin_user)
        assert is_admin() is True

        logout_user()
        assert is_admin() is False


class TestMultiUserScenario:
    def test_two_different_users_have_independent_authentication(self, test_db):
        from utils.auth import register_user, authenticate

        register_user("usera_multi", "usera@test.com", "passwordA")
        register_user("userb_multi", "userb@test.com", "passwordB")

        result_a_correct = authenticate("usera_multi", "passwordA")
        result_a_wrong_pw = authenticate("usera_multi", "passwordB")
        result_b_correct = authenticate("userb_multi", "passwordB")

        assert result_a_correct is not None
        assert result_a_wrong_pw is None
        assert result_b_correct is not None
        assert result_a_correct.id != result_b_correct.id
