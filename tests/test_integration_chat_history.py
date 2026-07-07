"""
tests/test_integration_chat_history.py

Integration Test: Persistensi & Pencarian Riwayat Chat Lintas Tabel
========================================================================
Menguji fungsi-fungsi di app/chatbot/chat_history_page.py yang menggabungkan
3 tabel sekaligus (ChatSession, ChatMessage, User) untuk satu kebutuhan
fungsional: menampilkan riwayat percakapan chatbot.

Skenario integrasi yang diuji:
1. Membuat sesi + beberapa pesan -> load_sessions() menghitung msg_count
   dan total_tokens dengan benar (agregasi lintas tabel)
2. RBAC pada riwayat chat: admin melihat semua sesi semua user, user biasa
   hanya melihat sesi miliknya sendiri (filter berdasarkan user_id)
3. load_messages() mengembalikan pesan terurut kronologis
4. search_sessions() mencari baik di judul maupun isi pesan
5. delete_session() menghapus dari kedua tabel secara konsisten
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid


def _create_session_with_messages(db_session, user_id, title, messages):
    """
    Helper: buat satu ChatSession + sejumlah ChatMessage.
    messages: list of (role, content, tokens_used)
    Returns: session db id
    """
    from database.models import ChatSession, ChatMessage

    with db_session() as s:
        sess = ChatSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
        )
        s.add(sess)
        s.flush()
        sess_id = sess.id

        for role, content, tokens in messages:
            s.add(ChatMessage(
                session_id=sess_id, role=role, content=content, tokens_used=tokens,
            ))

    return sess_id


class TestLoadSessionsAggregation:
    def test_load_sessions_counts_messages_correctly(self, test_db):
        from database.connection import db_session
        from database.models import User
        from app.chatbot.chat_history_page import load_sessions

        with db_session() as s:
            s.add(User(username="chatuser1", email="cu1@test.com", password="x", role="user"))
        with db_session() as s:
            user = s.query(User).filter_by(username="chatuser1").first()
            user_id = user.id

        _create_session_with_messages(db_session, user_id, "Tanya Toraja", [
            ("user", "Apa itu Tongkonan?", 0),
            ("assistant", "Tongkonan adalah rumah adat Toraja.", 50),
            ("user", "Terima kasih", 0),
        ])

        sessions = load_sessions(user_id, is_admin_user=False)
        assert len(sessions) == 1
        assert sessions[0]["msg_count"] == 3

    def test_load_sessions_sums_tokens_correctly(self, test_db):
        from database.connection import db_session
        from database.models import User
        from app.chatbot.chat_history_page import load_sessions

        with db_session() as s:
            s.add(User(username="chatuser2", email="cu2@test.com", password="x", role="user"))
        with db_session() as s:
            user_id = s.query(User).filter_by(username="chatuser2").first().id

        _create_session_with_messages(db_session, user_id, "Sesi Token", [
            ("user", "Pertanyaan 1", 0),
            ("assistant", "Jawaban 1", 100),
            ("user", "Pertanyaan 2", 0),
            ("assistant", "Jawaban 2", 150),
        ])

        sessions = load_sessions(user_id, is_admin_user=False)
        assert sessions[0]["total_tokens"] == 250

    def test_load_sessions_resolves_owner_username_correctly(self, test_db):
        from database.connection import db_session
        from database.models import User
        from app.chatbot.chat_history_page import load_sessions

        with db_session() as s:
            s.add(User(username="ownertest", email="owner@test.com", password="x", role="user"))
        with db_session() as s:
            user_id = s.query(User).filter_by(username="ownertest").first().id

        _create_session_with_messages(db_session, user_id, "Sesi Owner", [
            ("user", "Halo", 0),
        ])

        sessions = load_sessions(user_id, is_admin_user=True)
        assert sessions[0]["owner"] == "ownertest"

    def test_load_sessions_guest_session_owner_is_guest_label(self, test_db):
        from database.connection import db_session
        from app.chatbot.chat_history_page import load_sessions

        _create_session_with_messages(db_session, None, "Sesi Guest", [
            ("user", "Halo dari guest", 0),
        ])

        sessions = load_sessions(user_id=None, is_admin_user=True)
        guest_sessions = [s for s in sessions if s["title"] == "Sesi Guest"]
        assert len(guest_sessions) == 1
        assert guest_sessions[0]["owner"] == "Guest"


class TestRoleBasedAccessToHistory:
    def test_regular_user_sees_only_own_sessions(self, test_db):
        """
        Skenario kunci RBAC: user biasa membuka halaman riwayat chat hanya
        boleh melihat sesi miliknya sendiri, meskipun ada banyak sesi user
        lain tersimpan di database yang sama.
        """
        from database.connection import db_session
        from database.models import User
        from app.chatbot.chat_history_page import load_sessions

        with db_session() as s:
            s.add(User(username="rbacuser_a", email="rbac_a@test.com", password="x", role="user"))
            s.add(User(username="rbacuser_b", email="rbac_b@test.com", password="x", role="user"))
        with db_session() as s:
            user_a_id = s.query(User).filter_by(username="rbacuser_a").first().id
            user_b_id = s.query(User).filter_by(username="rbacuser_b").first().id

        _create_session_with_messages(db_session, user_a_id, "Sesi Milik A", [("user", "halo", 0)])
        _create_session_with_messages(db_session, user_b_id, "Sesi Milik B", [("user", "hai", 0)])

        sessions_for_a = load_sessions(user_a_id, is_admin_user=False)

        titles = [s["title"] for s in sessions_for_a]
        assert "Sesi Milik A" in titles
        assert "Sesi Milik B" not in titles

    def test_admin_sees_all_sessions_from_all_users(self, test_db):
        from database.connection import db_session
        from database.models import User
        from app.chatbot.chat_history_page import load_sessions

        with db_session() as s:
            s.add(User(username="rbacadmin", email="rbacadmin@test.com", password="x", role="admin"))
            s.add(User(username="rbacuser_c", email="rbac_c@test.com", password="x", role="user"))
        with db_session() as s:
            admin_id = s.query(User).filter_by(username="rbacadmin").first().id
            user_c_id = s.query(User).filter_by(username="rbacuser_c").first().id

        _create_session_with_messages(db_session, admin_id, "Sesi Admin", [("user", "halo", 0)])
        _create_session_with_messages(db_session, user_c_id, "Sesi User C", [("user", "hai", 0)])

        sessions_for_admin = load_sessions(admin_id, is_admin_user=True)

        titles = [s["title"] for s in sessions_for_admin]
        assert "Sesi Admin" in titles
        assert "Sesi User C" in titles


class TestLoadMessagesOrdering:
    def test_messages_returned_in_chronological_order(self, test_db):
        from database.connection import db_session
        from app.chatbot.chat_history_page import load_messages

        sess_id = _create_session_with_messages(db_session, None, "Urutan Test", [
            ("user", "Pesan pertama", 0),
            ("assistant", "Balasan pertama", 30),
            ("user", "Pesan kedua", 0),
            ("assistant", "Balasan kedua", 40),
        ])

        messages = load_messages(sess_id)
        contents = [m["content"] for m in messages]
        assert contents == [
            "Pesan pertama", "Balasan pertama", "Pesan kedua", "Balasan kedua"
        ]

    def test_messages_include_sources_field(self, test_db):
        from database.connection import db_session
        from database.models import ChatSession, ChatMessage

        with db_session() as s:
            sess = ChatSession(session_id=str(uuid.uuid4()), title="Sesi Sumber")
            s.add(sess)
            s.flush()
            sess_id = sess.id
            s.add(ChatMessage(
                session_id=sess_id, role="assistant", content="Jawaban dengan sumber",
                sources=[{"source": "ketekesu.txt", "score": 0.85}],
            ))

        from app.chatbot.chat_history_page import load_messages
        messages = load_messages(sess_id)

        assert len(messages) == 1
        assert messages[0]["sources"] == [{"source": "ketekesu.txt", "score": 0.85}]


class TestSearchSessionsAcrossTables:
    def test_search_matches_session_title(self, test_db):
        from database.connection import db_session
        from app.chatbot.chat_history_page import load_sessions, search_sessions

        _create_session_with_messages(db_session, None, "Percakapan Tentang Rambu Solo",
                                       [("user", "test", 0)])
        _create_session_with_messages(db_session, None, "Percakapan Tentang Hotel",
                                       [("user", "test", 0)])

        all_sessions = load_sessions(None, is_admin_user=True)
        result = search_sessions(all_sessions, "Rambu Solo")

        titles = [s["title"] for s in result]
        assert "Percakapan Tentang Rambu Solo" in titles
        assert "Percakapan Tentang Hotel" not in titles

    def test_search_matches_message_content_not_just_title(self, test_db):
        """
        Kemampuan kunci search_sessions(): pencarian harus menemukan kata kunci
        yang hanya ada di isi pesan, bahkan jika judul sesi sama sekali tidak
        memuat kata kunci tersebut.
        """
        from database.connection import db_session
        from app.chatbot.chat_history_page import load_sessions, search_sessions

        _create_session_with_messages(db_session, None, "Percakapan Umum", [
            ("user", "Apa itu upacara Ma'Nene?", 0),
            ("assistant", "Ma'Nene adalah ritual membersihkan jenazah leluhur.", 60),
        ])
        _create_session_with_messages(db_session, None, "Percakapan Lain", [
            ("user", "Bagaimana cuaca di Toraja?", 0),
        ])

        all_sessions = load_sessions(None, is_admin_user=True)
        result = search_sessions(all_sessions, "Ma'Nene")

        titles = [s["title"] for s in result]
        assert "Percakapan Umum" in titles
        assert "Percakapan Lain" not in titles

    def test_search_empty_keyword_returns_all_sessions_unfiltered(self, test_db):
        from database.connection import db_session
        from app.chatbot.chat_history_page import load_sessions, search_sessions

        _create_session_with_messages(db_session, None, "Sesi A", [("user", "x", 0)])
        _create_session_with_messages(db_session, None, "Sesi B", [("user", "y", 0)])

        all_sessions = load_sessions(None, is_admin_user=True)
        result = search_sessions(all_sessions, "")
        assert len(result) == len(all_sessions)


class TestDeleteSessionConsistency:
    def test_delete_session_removes_both_session_and_messages(self, test_db):
        """
        Pengujian integritas data paling penting di modul ini: delete_session()
        harus menghapus baris di kedua tabel (ChatSession dan ChatMessage),
        tidak menyisakan pesan yatim di ChatMessage setelah ChatSession-nya hilang.
        """
        from database.connection import db_session
        from database.models import ChatSession, ChatMessage
        from app.chatbot.chat_history_page import delete_session

        sess_id = _create_session_with_messages(db_session, None, "Akan Dihapus", [
            ("user", "Pesan 1", 0),
            ("assistant", "Balasan 1", 20),
        ])

        delete_session(sess_id)

        with db_session() as s:
            remaining_session = s.query(ChatSession).filter_by(id=sess_id).first()
            remaining_messages = s.query(ChatMessage).filter_by(session_id=sess_id).all()
            assert remaining_session is None
            assert len(remaining_messages) == 0

    def test_delete_one_session_does_not_affect_other_sessions(self, test_db):
        from database.connection import db_session
        from app.chatbot.chat_history_page import delete_session, load_sessions

        _create_session_with_messages(db_session, None, "Sesi A Tetap Ada",
                                       [("user", "halo", 0)])
        sess_b = _create_session_with_messages(db_session, None, "Sesi B Dihapus",
                                                [("user", "hai", 0)])

        delete_session(sess_b)

        remaining = load_sessions(None, is_admin_user=True)
        titles = [s["title"] for s in remaining]
        assert "Sesi A Tetap Ada" in titles
        assert "Sesi B Dihapus" not in titles
