"""
tests/test_auth.py

Unit test untuk utils/auth.py:
- hash_password()      : hashing PBKDF2-SHA256
- verify_password()     : verifikasi password terhadap hash
- register_user()       : registrasi user baru + validasi + duplikasi
- is_logged_in / is_admin / login_user / logout_user : session helpers
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ─── hash_password() ──────────────────────────────────────────────────────────

class TestHashPassword:
    def test_hash_is_deterministic(self):
        """Password yang sama harus menghasilkan hash yang sama (penting untuk verifikasi login)."""
        from utils.auth import hash_password
        h1 = hash_password("rahasia123")
        h2 = hash_password("rahasia123")
        assert h1 == h2

    def test_different_passwords_produce_different_hashes(self):
        from utils.auth import hash_password
        h1 = hash_password("rahasia123")
        h2 = hash_password("rahasia124")
        assert h1 != h2

    def test_hash_is_not_plaintext(self):
        """Hash tidak boleh mengandung password asli secara verbatim."""
        from utils.auth import hash_password
        password = "MyS3cretPassword"
        hashed = hash_password(password)
        assert password not in hashed

    def test_hash_output_is_hex_string(self):
        from utils.auth import hash_password
        hashed = hash_password("test123")
        # PBKDF2-SHA256 -> 32 bytes -> 64 karakter hex
        assert len(hashed) == 64
        assert all(c in "0123456789abcdef" for c in hashed)

    def test_empty_password_still_produces_hash(self):
        """Edge case: password kosong (idealnya divalidasi sebelum dipanggil, tapi fungsi tidak boleh crash)."""
        from utils.auth import hash_password
        hashed = hash_password("")
        assert isinstance(hashed, str)
        assert len(hashed) == 64


# ─── verify_password() ────────────────────────────────────────────────────────

class TestVerifyPassword:
    def test_correct_password_verifies_true(self):
        from utils.auth import hash_password, verify_password
        hashed = hash_password("correctpassword")
        assert verify_password("correctpassword", hashed) is True

    def test_wrong_password_verifies_false(self):
        from utils.auth import hash_password, verify_password
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_case_sensitive(self):
        """Password harus case-sensitive."""
        from utils.auth import hash_password, verify_password
        hashed = hash_password("Password123")
        assert verify_password("password123", hashed) is False

    def test_empty_password_against_real_hash_fails(self):
        from utils.auth import hash_password, verify_password
        hashed = hash_password("realpassword")
        assert verify_password("", hashed) is False


# ─── register_user() ──────────────────────────────────────────────────────────

class TestRegisterUser:
    def test_register_success_with_valid_data(self, test_db):
        from utils.auth import register_user
        success, msg = register_user("johndoe", "john@example.com", "password123")
        assert success is True
        assert "berhasil" in msg.lower()

    def test_registered_user_exists_in_db(self, test_db):
        from utils.auth import register_user
        from database.connection import db_session
        from database.models import User

        register_user("janedoe", "jane@example.com", "password123")

        with db_session() as s:
            user = s.query(User).filter_by(username="janedoe").first()
            assert user is not None
            assert user.email == "jane@example.com"
            assert user.role == "user"          # role default harus 'user'
            assert user.is_active is True

    def test_password_is_hashed_not_plaintext_in_db(self, test_db):
        from utils.auth import register_user
        from database.connection import db_session
        from database.models import User

        register_user("secureuser", "secure@example.com", "mypassword")

        with db_session() as s:
            user = s.query(User).filter_by(username="secureuser").first()
            assert user.password != "mypassword"
            assert len(user.password) == 64   # hex SHA-256

    def test_reject_duplicate_username(self, test_db):
        from utils.auth import register_user
        register_user("duplicateuser", "first@example.com", "password123")
        success, msg = register_user("duplicateuser", "second@example.com", "password456")
        assert success is False
        assert "sudah digunakan" in msg.lower()

    def test_reject_duplicate_email(self, test_db):
        from utils.auth import register_user
        register_user("user1", "same@example.com", "password123")
        success, msg = register_user("user2", "same@example.com", "password456")
        assert success is False
        assert "sudah terdaftar" in msg.lower()

    def test_reject_username_too_short(self, test_db):
        from utils.auth import register_user
        success, msg = register_user("ab", "ab@example.com", "password123")
        assert success is False
        assert "minimal 3 karakter" in msg.lower()

    def test_reject_username_too_long(self, test_db):
        from utils.auth import register_user
        long_username = "a" * 101
        success, msg = register_user(long_username, "long@example.com", "password123")
        assert success is False
        assert "maksimal 100 karakter" in msg.lower()

    def test_reject_password_too_short(self, test_db):
        from utils.auth import register_user
        success, msg = register_user("validuser", "valid@example.com", "12345")
        assert success is False
        assert "minimal 6 karakter" in msg.lower()

    def test_reject_invalid_email_no_at_sign(self, test_db):
        from utils.auth import register_user
        success, msg = register_user("validuser2", "notanemail", "password123")
        assert success is False
        assert "email tidak valid" in msg.lower()

    def test_reject_invalid_email_no_domain_dot(self, test_db):
        from utils.auth import register_user
        success, msg = register_user("validuser3", "user@nodot", "password123")
        assert success is False
        assert "email tidak valid" in msg.lower()

    def test_email_is_lowercased_on_save(self, test_db):
        """Email harus disimpan dalam lowercase agar tidak terjadi duplikasi case-sensitive."""
        from utils.auth import register_user
        from database.connection import db_session
        from database.models import User

        register_user("caseuser", "John.Doe@EXAMPLE.com", "password123")

        with db_session() as s:
            user = s.query(User).filter_by(username="caseuser").first()
            assert user.email == "john.doe@example.com"

    def test_username_and_email_whitespace_stripped(self, test_db):
        from utils.auth import register_user
        from database.connection import db_session
        from database.models import User

        register_user("  spaceduser  ", "  spaced@example.com  ", "password123")

        with db_session() as s:
            user = s.query(User).filter(User.username.like("%spaceduser%")).first()
            assert user is not None
            assert user.username == user.username.strip()
            assert user.email == "spaced@example.com"


# ─── Session state helpers (login_user, logout_user, is_logged_in, is_admin) ──

class TestSessionHelpers:
    def test_login_user_sets_session_state(self, test_db):
        from utils.auth import login_user, is_logged_in, is_admin
        from database.models import User

        fake_user = User(id=1, username="admin", role="admin")
        login_user(fake_user)

        assert is_logged_in() is True
        assert is_admin() is True

    def test_login_user_with_regular_role(self, test_db):
        from utils.auth import login_user, is_admin
        from database.models import User

        fake_user = User(id=2, username="biasa", role="user")
        login_user(fake_user)

        assert is_admin() is False

    def test_logout_user_clears_session(self, test_db):
        from utils.auth import login_user, logout_user, is_logged_in
        from database.models import User

        fake_user = User(id=3, username="temp", role="user")
        login_user(fake_user)
        assert is_logged_in() is True

        logout_user()
        assert is_logged_in() is False

    def test_is_logged_in_false_by_default(self):
        from utils.auth import is_logged_in
        assert is_logged_in() is False

    def test_is_admin_false_when_not_logged_in(self):
        from utils.auth import is_admin
        assert is_admin() is False
