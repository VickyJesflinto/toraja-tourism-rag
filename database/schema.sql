-- ============================================================
-- TORAJA TOURISM RAG SYSTEM
-- Database: toraja_tourism
-- Engine: MySQL 8.0+ | Charset: utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS toraja_tourism
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE toraja_tourism;

-- ============================================================
-- 1. USERS
-- Menyimpan akun pengguna sistem (admin & user biasa)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    username    VARCHAR(100)    NOT NULL,
    email       VARCHAR(255)    NOT NULL,
    password    VARCHAR(255)    NOT NULL COMMENT 'PBKDF2-SHA256 hash',
    role        ENUM('admin','user') NOT NULL DEFAULT 'user',
    is_active   TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username),
    UNIQUE KEY uq_users_email    (email),
    KEY        idx_users_role    (role),
    KEY        idx_users_active  (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Akun pengguna sistem (admin dan user)';


-- ============================================================
-- 2. TOURIST_ATTRACTIONS
-- Master data destinasi wisata di Toraja
-- ============================================================
CREATE TABLE IF NOT EXISTS tourist_attractions (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name        VARCHAR(255)    NOT NULL                    COMMENT 'Nama destinasi wisata',
    category    VARCHAR(100)    NULL                        COMMENT 'budaya | alam | religi | kuliner | lainnya',
    description TEXT            NULL                        COMMENT 'Deskripsi lengkap destinasi',
    location    VARCHAR(255)    NULL                        COMMENT 'Alamat / nama lokasi',
    district    VARCHAR(100)    NULL                        COMMENT 'Nama kecamatan',
    latitude    DOUBLE          NULL                        COMMENT 'Koordinat lintang',
    longitude   DOUBLE          NULL                        COMMENT 'Koordinat bujur',
    entry_fee   DECIMAL(15,2)   NOT NULL DEFAULT 0.00       COMMENT 'Harga tiket masuk (IDR)',
    rating      DECIMAL(3,2)    NOT NULL DEFAULT 0.00       COMMENT 'Rating 0.00 - 5.00',
    image_url   VARCHAR(512)    NULL                        COMMENT 'URL foto utama',
    is_active   TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_attraction_category (category),
    KEY idx_attraction_district (district),
    KEY idx_attraction_active   (is_active),
    KEY idx_attraction_rating   (rating DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Master data destinasi wisata Toraja';


-- ============================================================
-- 3. VISITOR_STATISTICS
-- Statistik kunjungan wisatawan per destinasi per bulan
-- ============================================================
CREATE TABLE IF NOT EXISTS visitor_statistics (
    id            INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    attraction_id INT UNSIGNED    NOT NULL                  COMMENT 'FK → tourist_attractions',
    year          SMALLINT UNSIGNED NOT NULL                COMMENT 'Tahun (contoh: 2024)',
    month         TINYINT UNSIGNED  NOT NULL                COMMENT 'Bulan 1-12',
    domestic      INT UNSIGNED    NOT NULL DEFAULT 0        COMMENT 'Jumlah wisatawan domestik',
    foreign_vis   INT UNSIGNED    NOT NULL DEFAULT 0        COMMENT 'Jumlah wisatawan mancanegara',
    total         INT UNSIGNED    NOT NULL DEFAULT 0        COMMENT 'Total = domestic + foreign',
    revenue       DECIMAL(18,2)   NOT NULL DEFAULT 0.00     COMMENT 'Total pendapatan (IDR)',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_visitor_stat (attraction_id, year, month)  COMMENT 'Satu record per destinasi per bulan',
    KEY idx_vs_year_month      (year, month),
    KEY idx_vs_attraction      (attraction_id),

    CONSTRAINT fk_vs_attraction
        FOREIGN KEY (attraction_id)
        REFERENCES tourist_attractions (id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Statistik kunjungan wisatawan bulanan per destinasi';


-- ============================================================
-- 4. ACCOMMODATIONS
-- Data penginapan dan akomodasi wisata
-- ============================================================
CREATE TABLE IF NOT EXISTS accommodations (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name        VARCHAR(255)    NOT NULL                    COMMENT 'Nama akomodasi',
    type        VARCHAR(100)    NULL                        COMMENT 'hotel | homestay | villa | resort | cottage',
    location    VARCHAR(255)    NULL                        COMMENT 'Alamat lengkap',
    district    VARCHAR(100)    NULL                        COMMENT 'Nama kecamatan',
    latitude    DOUBLE          NULL,
    longitude   DOUBLE          NULL,
    price_min   DECIMAL(15,2)   NULL                        COMMENT 'Harga terendah per malam (IDR)',
    price_max   DECIMAL(15,2)   NULL                        COMMENT 'Harga tertinggi per malam (IDR)',
    capacity    SMALLINT UNSIGNED NULL                      COMMENT 'Jumlah kamar / kapasitas',
    rating      DECIMAL(3,2)    NOT NULL DEFAULT 0.00,
    contact     VARCHAR(255)    NULL                        COMMENT 'Nomor telepon / email',
    is_active   TINYINT(1)      NOT NULL DEFAULT 1,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_acc_type     (type),
    KEY idx_acc_district (district),
    KEY idx_acc_active   (is_active),
    KEY idx_acc_rating   (rating DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Data penginapan dan akomodasi wisata Toraja';


-- ============================================================
-- 5. CULTURAL_EVENTS
-- Kalender event dan festival budaya Toraja
-- ============================================================
CREATE TABLE IF NOT EXISTS cultural_events (
    id           INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name         VARCHAR(255)    NOT NULL                   COMMENT 'Nama event / festival',
    description  TEXT            NULL,
    location     VARCHAR(255)    NULL,
    event_date   DATETIME        NULL                       COMMENT 'Tanggal/waktu mulai',
    end_date     DATETIME        NULL                       COMMENT 'Tanggal/waktu selesai',
    category     VARCHAR(100)    NULL                       COMMENT 'festival | upacara | pertunjukan | pameran',
    organizer    VARCHAR(255)    NULL,
    contact      VARCHAR(255)    NULL,
    is_recurring TINYINT(1)      NOT NULL DEFAULT 0         COMMENT '1 = event tahunan berulang',
    created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_event_date     (event_date),
    KEY idx_event_category (category),
    KEY idx_event_recurring(is_recurring)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Kalender event dan festival budaya Toraja';


-- ============================================================
-- 6. TOURISM_INFRASTRUCTURE
-- Kondisi infrastruktur dan fasilitas pendukung wisata
-- ============================================================
CREATE TABLE IF NOT EXISTS tourism_infrastructure (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name        VARCHAR(255)    NOT NULL                    COMMENT 'Nama fasilitas',
    type        VARCHAR(100)    NULL                        COMMENT 'jalan | toilet | mushola | loket | restoran | parkir | pusat_informasi',
    location    VARCHAR(255)    NULL,
    stat_condition   ENUM('baik','sedang','rusak') NOT NULL DEFAULT 'baik'
                                              COMMENT 'Kondisi fisik fasilitas',
    description TEXT            NULL,
    last_update DATETIME        NULL                        COMMENT 'Tanggal pemeriksaan terakhir',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_infra_type      (type),
    KEY idx_infra_condition (stat_ condition)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Data infrastruktur dan fasilitas pendukung wisata';


-- ============================================================
-- 7. DOCUMENTS
-- Metadata file yang diupload admin untuk RAG indexing
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id            INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    filename      VARCHAR(512)    NOT NULL                  COMMENT 'Nama file di storage',
    original_name VARCHAR(512)    NULL                      COMMENT 'Nama file asli saat upload',
    file_type     VARCHAR(50)     NULL                      COMMENT 'pdf | csv | json | docx | xlsx | pptx | html | xml | txt',
    file_size     BIGINT UNSIGNED NOT NULL DEFAULT 0        COMMENT 'Ukuran file dalam bytes',
    file_path     VARCHAR(1024)   NULL                      COMMENT 'Path absolut di server',
    status        ENUM('pending','processing','indexed','failed')
                  NOT NULL DEFAULT 'pending'                COMMENT 'Status indexing RAG',
    chunk_count   INT UNSIGNED    NOT NULL DEFAULT 0        COMMENT 'Jumlah chunk setelah diproses',
    error_msg     TEXT            NULL                      COMMENT 'Pesan error jika gagal',
    uploaded_by   INT UNSIGNED    NULL                      COMMENT 'FK → users (admin)',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                                  ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_doc_status      (status),
    KEY idx_doc_file_type   (file_type),
    KEY idx_doc_uploaded_by (uploaded_by),

    CONSTRAINT fk_doc_user
        FOREIGN KEY (uploaded_by)
        REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Metadata dokumen yang diupload untuk RAG knowledge base';


-- ============================================================
-- 8. DOCUMENT_CHUNKS
-- Potongan teks dari dokumen yang telah diindeks ke FAISS
-- ============================================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id          BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    document_id INT UNSIGNED     NOT NULL                   COMMENT 'FK → documents',
    chunk_index INT UNSIGNED     NOT NULL                   COMMENT 'Urutan chunk dalam dokumen (0-based)',
    content     MEDIUMTEXT       NOT NULL                   COMMENT 'Isi teks chunk (maks ~1000 karakter)',
    metadata    JSON             NULL                       COMMENT 'Info tambahan: page, sheet, slide, row, dll',
    faiss_id    BIGINT UNSIGNED  NULL                       COMMENT 'Posisi vektor di FAISS index',
    created_at  DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_chunk_faiss_id (faiss_id),
    KEY idx_chunk_document  (document_id),
    KEY idx_chunk_index     (chunk_index),

    CONSTRAINT fk_chunk_document
        FOREIGN KEY (document_id)
        REFERENCES documents (id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Chunk teks dokumen yang telah diproses dan diindeks ke FAISS';


-- ============================================================
-- 9. CHAT_SESSIONS
-- Sesi percakapan chatbot per pengguna
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id         INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id    INT UNSIGNED    NULL                         COMMENT 'FK → users (NULL = guest)',
    session_id VARCHAR(64)     NOT NULL                     COMMENT 'UUID unik sesi (dari Streamlit state)',
    title      VARCHAR(255)    NOT NULL DEFAULT 'New Chat'  COMMENT 'Judul sesi (dari pesan pertama)',
    created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_session_id  (session_id),
    KEY idx_cs_user_id        (user_id),
    KEY idx_cs_created        (created_at DESC),

    CONSTRAINT fk_cs_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Sesi percakapan chatbot AI';


-- ============================================================
-- 10. CHAT_MESSAGES
-- Riwayat pesan dalam setiap sesi chatbot
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id            BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
    session_id    INT UNSIGNED     NOT NULL                 COMMENT 'FK → chat_sessions',
    role          ENUM('user','assistant','system')
                  NOT NULL                                  COMMENT 'Pengirim pesan',
    content       MEDIUMTEXT       NOT NULL                 COMMENT 'Isi pesan',
    sources       JSON             NULL                     COMMENT 'Array chunk yang digunakan sebagai sumber RAG',
    tokens_used   INT UNSIGNED     NOT NULL DEFAULT 0       COMMENT 'Jumlah token LLM yang dipakai',
    response_time DECIMAL(8,3)     NOT NULL DEFAULT 0.000   COMMENT 'Waktu respons dalam detik',
    created_at    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_cm_session    (session_id),
    KEY idx_cm_role       (role),
    KEY idx_cm_created    (created_at DESC),

    CONSTRAINT fk_cm_session
        FOREIGN KEY (session_id)
        REFERENCES chat_sessions (id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Riwayat pesan chatbot AI (user & assistant)';


-- ============================================================
-- VIEWS (opsional — untuk kemudahan query di dashboard)
-- ============================================================

-- View: total kunjungan per tahun
CREATE OR REPLACE VIEW vw_yearly_summary AS
SELECT
    year,
    SUM(domestic)    AS total_domestic,
    SUM(foreign_vis) AS total_foreign,
    SUM(total)       AS grand_total,
    SUM(revenue)     AS total_revenue
FROM visitor_statistics
GROUP BY year
ORDER BY year DESC;


-- View: top destinasi berdasarkan total kunjungan
CREATE OR REPLACE VIEW vw_top_attractions AS
SELECT
    ta.id,
    ta.name,
    ta.category,
    ta.district,
    ta.rating,
    COALESCE(SUM(vs.total), 0)   AS total_visitors,
    COALESCE(SUM(vs.revenue), 0) AS total_revenue
FROM tourist_attractions ta
LEFT JOIN visitor_statistics vs ON vs.attraction_id = ta.id
WHERE ta.is_active = 1
GROUP BY ta.id, ta.name, ta.category, ta.district, ta.rating
ORDER BY total_visitors DESC;


-- View: statistik penggunaan chatbot
CREATE OR REPLACE VIEW vw_chatbot_stats AS
SELECT
    DATE(cm.created_at)           AS chat_date,
    COUNT(DISTINCT cs.id)          AS total_sessions,
    COUNT(CASE WHEN cm.role = 'user' THEN 1 END)      AS user_messages,
    COUNT(CASE WHEN cm.role = 'assistant' THEN 1 END) AS bot_responses,
    SUM(cm.tokens_used)            AS total_tokens,
    AVG(cm.response_time)          AS avg_response_time_sec
FROM chat_messages cm
JOIN chat_sessions cs ON cs.id = cm.session_id
GROUP BY DATE(cm.created_at)
ORDER BY chat_date DESC;


-- View: ringkasan dokumen RAG
CREATE OR REPLACE VIEW vw_document_summary AS
SELECT
    d.id,
    d.original_name,
    d.file_type,
    ROUND(d.file_size / 1024, 1)  AS size_kb,
    d.chunk_count,
    d.status,
    u.username                     AS uploaded_by,
    d.created_at
FROM documents d
LEFT JOIN users u ON u.id = d.uploaded_by
ORDER BY d.created_at DESC;


-- ============================================================
-- SAMPLE DATA — Default Admin
-- Password: admin123  (PBKDF2-SHA256, ganti setelah deploy!)
-- ============================================================
INSERT INTO users (username, email, password, role) VALUES
('admin', 'admin@torajapariwisata.id',
 -- Hash ini dibuat oleh utils/auth.py::hash_password('admin123')
 -- Ganti dengan hash yang benar saat production
 'REPLACE_WITH_HASH_FROM_scripts/init_db.py',
 'admin')
ON DUPLICATE KEY UPDATE username = username;
