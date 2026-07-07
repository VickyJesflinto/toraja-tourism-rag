"""
tests/test_models.py

Unit test untuk database/models.py:
- Memastikan semua model bisa di-load tanpa error (mendeteksi konflik nama
  seperti bug 'metadata' yang pernah terjadi pada SQLAlchemy Declarative API)
- Memastikan kolom-kolom penting ada dan tipe relasinya benar
- Memastikan constraint dasar (nullable, default, unique) berfungsi
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


class TestModelsLoadWithoutError:
    def test_models_module_imports_successfully(self):
        """
        Test regresi untuk bug sebelumnya: kolom bernama 'metadata' di
        DocumentChunk berkonflik dengan SQLAlchemy Base.metadata dan membuat
        SELURUH aplikasi gagal start. Test ini memastikan import tidak error.
        """
        import database.models as models
        assert models is not None

    def test_all_expected_models_exist(self):
        from database.models import (
            User, TouristAttraction, VisitorStatistic,
            Accommodation, CulturalEvent, TourismInfrastructure,
            Document, DocumentChunk, ChatSession, ChatMessage,
        )
        models = [
            User, TouristAttraction, VisitorStatistic, Accommodation,
            CulturalEvent, TourismInfrastructure, Document, DocumentChunk,
            ChatSession, ChatMessage,
        ]
        for m in models:
            assert hasattr(m, "__tablename__")

    def test_document_chunk_metadata_column_uses_safe_attribute_name(self):
        """
        Regresi spesifik: atribut Python untuk kolom 'metadata' harus
        bernama 'chunk_metadata', bukan 'metadata' (karena 'metadata' adalah
        nama yang direservasi SQLAlchemy Declarative API).
        """
        from database.models import DocumentChunk
        assert hasattr(DocumentChunk, "meta_data")
        col = DocumentChunk.__table__.columns.get("metadata")
        assert col is not None

    def test_base_metadata_still_works_normally(self):
        from database.models import Base
        assert hasattr(Base, "metadata")
        assert len(Base.metadata.tables) > 0


class TestModelTableNames:
    def test_table_names_match_expected(self):
        from database.models import (
            User, TouristAttraction, VisitorStatistic,
            Accommodation, CulturalEvent, TourismInfrastructure,
            Document, DocumentChunk, ChatSession, ChatMessage,
        )
        expected = {
            User: "users",
            TouristAttraction: "tourist_attractions",
            VisitorStatistic: "visitor_statistics",
            Accommodation: "accommodations",
            CulturalEvent: "cultural_events",
            TourismInfrastructure: "tourism_infrastructure",
            Document: "documents",
            DocumentChunk: "document_chunks",
            ChatSession: "chat_sessions",
            ChatMessage: "chat_messages",
        }
        for model, table_name in expected.items():
            assert model.__tablename__ == table_name


class TestUserModel:
    def test_create_user_with_required_fields(self, test_db):
        from database.connection import db_session
        from database.models import User

        with db_session() as s:
            s.add(User(username="testuser", email="test@test.com",
                       password="hashed", role="user"))

        with db_session() as s:
            user = s.query(User).filter_by(username="testuser").first()
            assert user is not None
            assert user.role == "user"

    def test_user_default_role_is_user(self, test_db):
        from database.connection import db_session
        from database.models import User

        with db_session() as s:
            s.add(User(username="defaultroleuser", email="d@test.com", password="x"))

        with db_session() as s:
            user = s.query(User).filter_by(username="defaultroleuser").first()
            assert user.role == "user"

    def test_user_default_is_active_true(self, test_db):
        from database.connection import db_session
        from database.models import User

        with db_session() as s:
            s.add(User(username="activeuser", email="a@test.com", password="x"))

        with db_session() as s:
            user = s.query(User).filter_by(username="activeuser").first()
            assert user.is_active is True

    def test_username_uniqueness_enforced(self, test_db):
        from database.connection import db_session
        from database.models import User
        from sqlalchemy.exc import IntegrityError

        with db_session() as s:
            s.add(User(username="uniqueuser", email="u1@test.com", password="x"))

        with pytest.raises(IntegrityError):
            with db_session() as s:
                s.add(User(username="uniqueuser", email="u2@test.com", password="x"))

    def test_email_uniqueness_enforced(self, test_db):
        from database.connection import db_session
        from database.models import User
        from sqlalchemy.exc import IntegrityError

        with db_session() as s:
            s.add(User(username="userA", email="same@test.com", password="x"))

        with pytest.raises(IntegrityError):
            with db_session() as s:
                s.add(User(username="userB", email="same@test.com", password="x"))


class TestTouristAttractionModel:
    def test_create_attraction_with_defaults(self, test_db):
        from database.connection import db_session
        from database.models import TouristAttraction

        with db_session() as s:
            s.add(TouristAttraction(name="Test Destinasi", category="budaya"))

        with db_session() as s:
            attr = s.query(TouristAttraction).filter_by(name="Test Destinasi").first()
            assert attr.entry_fee == 0.00
            assert attr.rating == 0.00
            assert attr.is_active is True

    def test_attraction_visitor_stats_relationship(self, test_db):
        from database.connection import db_session
        from database.models import TouristAttraction, VisitorStatistic

        with db_session() as s:
            s.add(TouristAttraction(name="Destinasi Relasi", category="alam"))

        with db_session() as s:
            attr = s.query(TouristAttraction).filter_by(name="Destinasi Relasi").first()
            s.add(VisitorStatistic(
                attraction_id=attr.id, year=2024, month=1,
                domestic=100, foreign_vis=10, total=110, revenue=1000000,
            ))

        with db_session() as s:
            attr = s.query(TouristAttraction).filter_by(name="Destinasi Relasi").first()
            assert len(attr.visitor_stats) == 1
            assert attr.visitor_stats[0].domestic == 100

    def test_cascade_delete_attraction_removes_visitor_stats(self, test_db):
        from database.connection import db_session
        from database.models import TouristAttraction, VisitorStatistic

        with db_session() as s:
            s.add(TouristAttraction(name="Akan Dihapus", category="budaya"))

        with db_session() as s:
            attr = s.query(TouristAttraction).filter_by(name="Akan Dihapus").first()
            attr_id = attr.id
            s.add(VisitorStatistic(
                attraction_id=attr_id, year=2024, month=1,
                domestic=50, foreign_vis=5, total=55, revenue=500000,
            ))

        with db_session() as s:
            s.query(TouristAttraction).filter_by(id=attr_id).delete()

        with db_session() as s:
            remaining_stats = s.query(VisitorStatistic).filter_by(attraction_id=attr_id).all()
            assert len(remaining_stats) == 0


class TestDocumentAndChunkModel:
    def test_create_document_with_chunks(self, test_db):
        from database.connection import db_session
        from database.models import Document, DocumentChunk

        with db_session() as s:
            s.add(Document(filename="test.pdf", file_type="pdf", status="pending"))

        with db_session() as s:
            doc = s.query(Document).filter_by(filename="test.pdf").first()
            s.add(DocumentChunk(
                document_id=doc.id, chunk_index=0, content="isi chunk pertama",
                meta_data={"page": 1},
            ))

        with db_session() as s:
            doc = s.query(Document).filter_by(filename="test.pdf").first()
            assert len(doc.chunks) == 1
            assert doc.chunks[0].content == "isi chunk pertama"
            assert doc.chunks[0].meta_data == {"page": 1}

    def test_document_default_status_pending(self, test_db):
        from database.connection import db_session
        from database.models import Document

        with db_session() as s:
            s.add(Document(filename="pending.pdf", file_type="pdf"))

        with db_session() as s:
            doc = s.query(Document).filter_by(filename="pending.pdf").first()
            assert doc.status == "pending"

    def test_cascade_delete_document_removes_chunks(self, test_db):
        from database.connection import db_session
        from database.models import Document, DocumentChunk

        with db_session() as s:
            s.add(Document(filename="todelete.pdf", file_type="pdf"))

        with db_session() as s:
            doc = s.query(Document).filter_by(filename="todelete.pdf").first()
            doc_id = doc.id
            s.add(DocumentChunk(document_id=doc_id, chunk_index=0, content="x"))

        with db_session() as s:
            s.query(Document).filter_by(id=doc_id).delete()

        with db_session() as s:
            remaining = s.query(DocumentChunk).filter_by(document_id=doc_id).all()
            assert len(remaining) == 0


class TestChatSessionAndMessageModel:
    def test_create_session_with_messages(self, test_db):
        from database.connection import db_session
        from database.models import ChatSession, ChatMessage

        with db_session() as s:
            s.add(ChatSession(session_id="sess-001", title="Tanya Toraja"))

        with db_session() as s:
            sess = s.query(ChatSession).filter_by(session_id="sess-001").first()
            s.add(ChatMessage(session_id=sess.id, role="user", content="Halo"))
            s.add(ChatMessage(session_id=sess.id, role="assistant", content="Hai!"))

        with db_session() as s:
            sess = s.query(ChatSession).filter_by(session_id="sess-001").first()
            assert len(sess.messages) == 2

    def test_chat_session_id_must_be_unique(self, test_db):
        from database.connection import db_session
        from database.models import ChatSession
        from sqlalchemy.exc import IntegrityError

        with db_session() as s:
            s.add(ChatSession(session_id="dup-session"))

        with pytest.raises(IntegrityError):
            with db_session() as s:
                s.add(ChatSession(session_id="dup-session"))

    def test_chat_session_default_title(self, test_db):
        from database.connection import db_session
        from database.models import ChatSession

        with db_session() as s:
            s.add(ChatSession(session_id="sess-default-title"))

        with db_session() as s:
            sess = s.query(ChatSession).filter_by(session_id="sess-default-title").first()
            assert sess.title == "New Chat"
