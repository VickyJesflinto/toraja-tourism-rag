"""
database/models.py
SQLAlchemy ORM models for Toraja Tourism RAG System
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    Boolean, ForeignKey, JSON, BigInteger, Enum
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ─── User & Auth ──────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    username   = Column(String(100), unique=True, nullable=False)
    email      = Column(String(255), unique=True, nullable=False)
    password   = Column(String(255), nullable=False)          # bcrypt hash
    role       = Column(Enum("admin", "user"), default="user")
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chat_sessions = relationship("ChatSession", back_populates="user")


# ─── Tourism Data ─────────────────────────────────────────────────────────────
class TouristAttraction(Base):
    __tablename__ = "tourist_attractions"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(255), nullable=False)
    category    = Column(String(100))           # budaya, alam, religi, kuliner
    description = Column(Text)
    location    = Column(String(255))
    district    = Column(String(100))           # kecamatan
    latitude    = Column(Float)
    longitude   = Column(Float)
    entry_fee   = Column(Float, default=0)
    rating      = Column(Float, default=0.0)
    image_url   = Column(String(512))
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    visitor_stats = relationship("VisitorStatistic", back_populates="attraction")


class VisitorStatistic(Base):
    __tablename__ = "visitor_statistics"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    attraction_id = Column(Integer, ForeignKey("tourist_attractions.id"), nullable=False)
    year          = Column(Integer, nullable=False)
    month         = Column(Integer, nullable=False)   # 1-12
    domestic      = Column(Integer, default=0)
    foreign_vis   = Column(Integer, default=0)
    total         = Column(Integer, default=0)
    revenue       = Column(Float, default=0.0)        # IDR
    created_at    = Column(DateTime, default=datetime.utcnow)

    attraction = relationship("TouristAttraction", back_populates="visitor_stats")


class Accommodation(Base):
    __tablename__ = "accommodations"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    name         = Column(String(255), nullable=False)
    type         = Column(String(100))                # hotel, homestay, villa, resort
    location     = Column(String(255))
    district     = Column(String(100))
    latitude     = Column(Float)
    longitude    = Column(Float)
    price_min    = Column(Float)
    price_max    = Column(Float)
    capacity     = Column(Integer)
    rating       = Column(Float, default=0.0)
    contact      = Column(String(255))
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CulturalEvent(Base):
    __tablename__ = "cultural_events"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(255), nullable=False)
    description = Column(Text)
    location    = Column(String(255))
    event_date  = Column(DateTime)
    end_date    = Column(DateTime)
    category    = Column(String(100))                 # festival, upacara, pertunjukan
    organizer   = Column(String(255))
    contact     = Column(String(255))
    is_recurring = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TourismInfrastructure(Base):
    __tablename__ = "tourism_infrastructure"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(255), nullable=False)
    type        = Column(String(100))   # jalan, toilet, mushola, loket, resto
    location    = Column(String(255))
    stat_condition   = Column(Enum("baik", "sedang", "rusak"), default="baik")
    description = Column(Text)
    last_update = Column(DateTime)
    created_at  = Column(DateTime, default=datetime.utcnow)


# ─── RAG Documents ────────────────────────────────────────────────────────────
class Document(Base):
    __tablename__ = "documents"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    filename     = Column(String(512), nullable=False)
    original_name = Column(String(512))
    file_type    = Column(String(50))                  # pdf, csv, json, docx, ...
    file_size    = Column(BigInteger, default=0)       # bytes
    file_path    = Column(String(1024))
    status       = Column(
        Enum("pending", "processing", "indexed", "failed"),
        default="pending"
    )
    chunk_count  = Column(Integer, default=0)
    error_msg    = Column(Text)
    uploaded_by  = Column(Integer, ForeignKey("users.id"))
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("DocumentChunk", back_populates="document",
                          cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content     = Column(Text, nullable=False)
    meta_data    = Column(JSON)                         # page, row, sheet, etc.
    faiss_id    = Column(BigInteger, unique=True)      # index in FAISS
    created_at  = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")


# ─── Chat ─────────────────────────────────────────────────────────────────────
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(64), unique=True, nullable=False)
    title      = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user     = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session",
                            cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    session_id     = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role           = Column(Enum("user", "assistant", "system"), nullable=False)
    content        = Column(Text, nullable=False)
    sources        = Column(JSON)                      # retrieved chunks info
    tokens_used    = Column(Integer, default=0)
    response_time  = Column(Float, default=0.0)        # seconds
    created_at     = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
