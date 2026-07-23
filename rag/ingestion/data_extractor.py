"""
rag/ingestion/data_extractor.py

Mengekstrak data pariwisata terstruktur dari dokumen yang diupload
menggunakan LLM (via OpenRouter), lalu menyimpannya ke tabel MySQL.

Fitur anti-duplikat dengan Fuzzy Matching:
  - Normalisasi nama (lowercase, strip spasi, hapus tanda baca)
  - Token overlap  : cek berapa banyak kata yang sama (threshold ≥ 50%)
  - Sequence ratio : difflib.SequenceMatcher (threshold ≥ 0.75)
  - Substring check: nama baru adalah substring / superstring dari yang ada
  Jika salah satu kondisi terpenuhi → UPDATE, bukan INSERT baru.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.settings import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL,
    OPENROUTER_SITE_URL, OPENROUTER_APP_NAME, LLM_MODEL,
)
from database.connection import db_session
from database.models import (
    TouristAttraction, VisitorStatistic,
    Accommodation, CulturalEvent, TourismInfrastructure,
)


# ─── Fuzzy matching engine ────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """
    Normalisasi teks untuk perbandingan:
    - Lowercase
    - Hapus aksen/diakritik (é → e)
    - Hapus tanda baca & karakter non-alfanumerik kecuali spasi
    - Hapus kata penghubung umum (Bahasa Indonesia & Inggris)
    - Normalisasi spasi
    """
    if not text:
        return ""
    # Decode Unicode (é → e, ü → u, dst.)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    # Hapus tanda baca
    text = re.sub(r"[^\w\s]", " ", text)
    # Hapus stopwords umum yang tidak bermakna untuk matching nama
    stopwords = {
        "dan", "atau", "di", "ke", "dari", "yang", "untuk", "dengan",
        "hotel", "resort", "villa", "homestay", "cottage",  # tipe akomodasi jangan dijadikan pembeda
        "the", "and", "or", "of", "in", "at", "to",
    }
    tokens = [t for t in text.split() if t and t not in stopwords]
    return " ".join(tokens)


def _tokenize(text: str) -> set[str]:
    """Tokenisasi nama menjadi set kata (sudah dinormalisasi)."""
    return set(_normalize(text).split())


def _similarity(a: str, b: str) -> float:
    """
    Skor kemiripan gabungan antara dua nama (0.0 – 1.0).
    Menggunakan dua metode dan ambil nilai tertinggi:
      1. SequenceMatcher ratio (char-level)
      2. Token Jaccard similarity (word-level)
    """
    na = _normalize(a)
    nb = _normalize(b)
    if not na or not nb:
        return 0.0

    # 1. Character-level similarity
    seq_ratio = SequenceMatcher(None, na, nb).ratio()

    # 2. Token-level Jaccard similarity
    ta = _tokenize(a)
    tb = _tokenize(b)
    if ta and tb:
        jaccard = len(ta & tb) / len(ta | tb)
    else:
        jaccard = 0.0

    # 3. Substring bonus: jika salah satu mengandung yang lain sepenuhnya
    substring_bonus = 0.0
    if na in nb or nb in na:
        substring_bonus = 0.2

    return min(1.0, max(seq_ratio, jaccard) + substring_bonus)


def _find_duplicate(
    name: str,
    existing_names: list[tuple[int, str]],   # [(id, name), ...]
    threshold: float = 0.70,
) -> tuple[int, str, float] | None:
    """
    Cari record yang paling mirip dengan `name` dari daftar `existing_names`.

    Returns:
        (id, matched_name, score) jika ditemukan match ≥ threshold
        None jika tidak ada
    """
    if not name.strip():
        return None

    best_id    = None
    best_name  = None
    best_score = 0.0

    for rec_id, rec_name in existing_names:
        score = _similarity(name, rec_name)
        if score > best_score:
            best_score = score
            best_id    = rec_id
            best_name  = rec_name

    if best_score >= threshold:
        return best_id, best_name, best_score
    return None


# ─── Prompt templates ─────────────────────────────────────────────────────────

_SYSTEM = """Kamu adalah sistem ekstraksi data pariwisata Toraja.
Tugasmu adalah membaca teks dokumen dan mengekstrak data terstruktur ke format JSON.
Kembalikan HANYA JSON yang valid, tanpa teks lain, tanpa markdown, tanpa penjelasan."""

_PROMPT = """Baca teks berikut dan ekstrak semua data pariwisata Toraja yang ada.

TEKS:
{text}

Kembalikan JSON dengan struktur ini (kosongkan array jika tidak ada data):
{{
  "tourist_attractions": [
    {{
      "name": "...",
      "category": "budaya|alam|religi|kuliner|lainnya",
      "description": "...",
      "location": "...",
      "district": "...",
      "latitude": null,
      "longitude": null,
      "entry_fee": 0,
      "rating": 0.0
    }}
  ],
  "visitor_statistics": [
    {{
      "attraction_name": "...",
      "year": 2024,
      "month": 1,
      "domestic": 0,
      "foreign_vis": 0,
      "revenue": 0.0
    }}
  ],
  "accommodations": [
    {{
      "name": "...",
      "type": "hotel|homestay|villa|resort|cottage",
      "location": "...",
      "district": "...",
      "price_min": 0,
      "price_max": 0,
      "capacity": 0,
      "rating": 0.0,
      "contact": ""
    }}
  ],
  "cultural_events": [
    {{
      "name": "...",
      "category": "festival|upacara|pertunjukan|pameran|lainnya",
      "description": "...",
      "location": "...",
      "organizer": "",
      "event_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "is_recurring": false
    }}
  ],
  "tourism_infrastructure": [
    {{
      "name": "...",
      "type": "jalan|toilet umum|mushola|loket|restoran|parkir|pusat informasi|lainnya",
      "location": "...",
      "stat_condition": "baik|sedang|rusak",
      "description": ""
    }}
  ]
}}

Aturan penting:
- Hanya isi data yang benar-benar ada di teks, jangan mengarang
- entry_fee, price_min, price_max dalam Rupiah (angka saja, tanpa "Rp")
- Jika tidak tahu nilai numerik, gunakan 0 atau null
- rating antara 0.0-5.0, jika tidak ada gunakan 0.0
- event_date dan end_date format YYYY-MM-DD, null jika tidak ada
"""


# ─── LLM caller ───────────────────────────────────────────────────────────────

def _call_llm(text: str) -> dict:
    from openai import OpenAI
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": OPENROUTER_SITE_URL,
            "X-Title": OPENROUTER_APP_NAME,
        },
    )
    text_trimmed = text[:8000] if len(text) > 8000 else text
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": _PROMPT.format(text=text_trimmed)},
        ],
        max_tokens=3000,
        temperature=0.1,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


# ─── Value helpers ────────────────────────────────────────────────────────────

def _to_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def _to_int(val: Any, default: int = 0) -> int:
    try:
        return int(float(val)) if val is not None else default
    except (ValueError, TypeError):
        return default


def _parse_date(val: Any) -> datetime | None:
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(val), fmt)
        except ValueError:
            continue
    return None


def _clean_str(val: Any, max_len: int = 255) -> str:
    if not val:
        return ""
    return str(val).strip()[:max_len]


def _merge_fields(existing, item: dict, fields: list[str]):
    """Isi field yang masih kosong di record existing dengan nilai dari item."""
    for field in fields:
        val = item.get(field)
        if val and not getattr(existing, field, None):
            setattr(existing, field, val)


# ─── Upsert functions (dengan fuzzy dedup) ────────────────────────────────────

def _upsert_attractions(items: list[dict], session) -> tuple[dict[str, int], list[str]]:
    """
    Upsert destinasi wisata dengan fuzzy dedup.
    Returns:
        name_to_id  — mapping nama (lowercase) → db id, untuk FK statistik
        dedup_log   — log singkat setiap keputusan insert/update/skip
    """
    VALID_CATEGORIES = {"budaya", "alam", "religi", "kuliner", "lainnya"}
    name_to_id: dict[str, int] = {}
    dedup_log: list[str] = []

    # Ambil semua nama existing sekali saja (efisien)
    existing_list = [(r.id, r.name) for r in session.query(
        TouristAttraction.id, TouristAttraction.name).all()]

    for item in items:
        name = _clean_str(item.get("name"))
        if not name:
            continue

        category = _clean_str(item.get("category", "lainnya")).lower()
        if category not in VALID_CATEGORIES:
            category = "lainnya"

        match = _find_duplicate(name, existing_list)

        if match:
            match_id, match_name, score = match
            existing = session.query(TouristAttraction).filter_by(id=match_id).first()
            if existing:
                _merge_fields(existing, {
                    "description": _clean_str(item.get("description",""), 5000),
                    "location":    _clean_str(item.get("location","")),
                    "district":    _clean_str(item.get("district","")),
                    "latitude":    _to_float(item.get("latitude")) or None,
                    "longitude":   _to_float(item.get("longitude")) or None,
                    "entry_fee":   _to_float(item.get("entry_fee")) or None,
                    "rating":      min(_to_float(item.get("rating")), 5.0) or None,
                }, ["description","location","district","latitude","longitude","entry_fee","rating"])
                existing.updated_at = datetime.utcnow()
                session.flush()
                name_to_id[name.lower()]       = existing.id
                name_to_id[match_name.lower()] = existing.id
                pct = int(score * 100)
                msg = f"UPDATE destinasi '{match_name}' ← '{name}' (kemiripan {pct}%)"
                dedup_log.append(msg)
                logger.info(f"[dedup] {msg}")
        else:
            lat = _to_float(item.get("latitude")) or None
            lon = _to_float(item.get("longitude")) or None
            new_rec = TouristAttraction(
                name=name, category=category,
                description=_clean_str(item.get("description",""), 5000),
                location=_clean_str(item.get("location","")),
                district=_clean_str(item.get("district","")),
                latitude=lat, longitude=lon,
                entry_fee=_to_float(item.get("entry_fee")),
                rating=min(_to_float(item.get("rating")), 5.0),
                is_active=True,
            )
            session.add(new_rec)
            session.flush()
            name_to_id[name.lower()] = new_rec.id
            existing_list.append((new_rec.id, name))   # update cache
            msg = f"INSERT destinasi baru: '{name}'"
            dedup_log.append(msg)
            logger.info(f"[dedup] {msg}")

    return name_to_id, dedup_log


def _upsert_visitor_stats(
    items: list[dict],
    name_to_id: dict[str, int],
    session,
) -> list[str]:
    dedup_log: list[str] = []
    all_attrs  = session.query(TouristAttraction).all()
    db_name_map = {a.name.lower(): a.id for a in all_attrs}
    db_name_map.update(name_to_id)
    existing_names = list(db_name_map.items())   # [(name, id)]
    existing_names_for_fuzzy = [(v, k) for k, v in db_name_map.items()]  # [(id, name)]

    for item in items:
        attr_name_raw = _clean_str(item.get("attraction_name",""))
        attr_name     = attr_name_raw.lower()
        attr_id       = db_name_map.get(attr_name)

        if not attr_id:
            # Fuzzy match nama destinasi untuk statistik
            match = _find_duplicate(attr_name_raw, existing_names_for_fuzzy, threshold=0.60)
            if match:
                attr_id = match[0]
                logger.debug(f"[dedup] Statistik: '{attr_name_raw}' → '{match[1]}' ({int(match[2]*100)}%)")
            else:
                logger.warning(f"[dedup] Destinasi tidak ditemukan untuk statistik: '{attr_name_raw}'")
                continue

        year  = _to_int(item.get("year",  datetime.now().year))
        month = _to_int(item.get("month", 1))
        if not (1 <= month <= 12): month = 1
        if not (2000 <= year <= 2100): year = datetime.now().year

        dom = _to_int(item.get("domestic"))
        frn = _to_int(item.get("foreign_vis"))
        rev = _to_float(item.get("revenue"))

        existing = session.query(VisitorStatistic).filter_by(
            attraction_id=attr_id, year=year, month=month
        ).first()

        if existing:
            existing.domestic = dom
            existing.foreign_vis  = frn
            existing.total    = dom + frn
            existing.revenue  = rev
            msg = f"UPDATE statistik {attr_name_raw} {year}/{month:02d}"
            dedup_log.append(msg)
        else:
            session.add(VisitorStatistic(
                attraction_id=attr_id, year=year, month=month,
                domestic=dom, foreign_vis=frn, total=dom+frn, revenue=rev,
            ))
            msg = f"INSERT statistik {attr_name_raw} {year}/{month:02d}"
            dedup_log.append(msg)
        logger.debug(f"[dedup] {msg}")

    return dedup_log


def _upsert_accommodations(items: list[dict], session) -> list[str]:
    VALID_TYPES = {"hotel","homestay","villa","resort","cottage"}
    dedup_log: list[str] = []

    existing_list = [(r.id, r.name) for r in session.query(
        Accommodation.id, Accommodation.name).all()]

    for item in items:
        name = _clean_str(item.get("name"))
        if not name:
            continue

        acc_type = _clean_str(item.get("type","hotel")).lower()
        if acc_type not in VALID_TYPES:
            acc_type = "hotel"

        match = _find_duplicate(name, existing_list)

        if match:
            match_id, match_name, score = match
            existing = session.query(Accommodation).filter_by(id=match_id).first()
            if existing:
                _merge_fields(existing, {
                    "location":  _clean_str(item.get("location","")),
                    "district":  _clean_str(item.get("district","")),
                    "price_min": _to_float(item.get("price_min")) or None,
                    "price_max": _to_float(item.get("price_max")) or None,
                    "capacity":  _to_int(item.get("capacity")) or None,
                    "rating":    min(_to_float(item.get("rating")), 5.0) or None,
                    "contact":   _clean_str(item.get("contact","")),
                }, ["location","district","price_min","price_max","capacity","rating","contact"])
                existing.updated_at = datetime.utcnow()
                session.flush()
                existing_list = [(r.id, r.name) for r in session.query(
                    Accommodation.id, Accommodation.name).all()]
                pct = int(score * 100)
                msg = f"UPDATE akomodasi '{match_name}' ← '{name}' ({pct}%)"
                dedup_log.append(msg)
                logger.info(f"[dedup] {msg}")
        else:
            session.add(Accommodation(
                name=name, type=acc_type,
                location=_clean_str(item.get("location","")),
                district=_clean_str(item.get("district","")),
                price_min=_to_float(item.get("price_min")),
                price_max=_to_float(item.get("price_max")),
                capacity=_to_int(item.get("capacity")),
                rating=min(_to_float(item.get("rating")), 5.0),
                contact=_clean_str(item.get("contact","")),
                is_active=True,
            ))
            session.flush()
            existing_list.append((session.query(Accommodation).filter_by(name=name).first().id, name))
            msg = f"INSERT akomodasi baru: '{name}'"
            dedup_log.append(msg)
            logger.info(f"[dedup] {msg}")

    return dedup_log


def _upsert_events(items: list[dict], session) -> list[str]:
    VALID_CATS = {"festival","upacara","pertunjukan","pameran","lainnya"}
    dedup_log: list[str] = []

    existing_list = [(r.id, r.name) for r in session.query(
        CulturalEvent.id, CulturalEvent.name).all()]

    for item in items:
        name = _clean_str(item.get("name"))
        if not name:
            continue

        cat = _clean_str(item.get("category","lainnya")).lower()
        if cat not in VALID_CATS:
            cat = "lainnya"

        ev_date  = _parse_date(item.get("event_date"))
        end_date = _parse_date(item.get("end_date"))

        match = _find_duplicate(name, existing_list)

        if match:
            match_id, match_name, score = match
            existing = session.query(CulturalEvent).filter_by(id=match_id).first()
            if existing:
                _merge_fields(existing, {
                    "description": _clean_str(item.get("description",""), 5000),
                    "location":    _clean_str(item.get("location","")),
                    "organizer":   _clean_str(item.get("organizer","")),
                    "event_date":  ev_date,
                    "end_date":    end_date,
                }, ["description","location","organizer","event_date","end_date"])
                existing.updated_at = datetime.utcnow()
                pct = int(score * 100)
                msg = f"UPDATE event '{match_name}' ← '{name}' ({pct}%)"
                dedup_log.append(msg)
                logger.info(f"[dedup] {msg}")
        else:
            session.add(CulturalEvent(
                name=name, category=cat,
                description=_clean_str(item.get("description",""), 5000),
                location=_clean_str(item.get("location","")),
                organizer=_clean_str(item.get("organizer","")),
                event_date=ev_date, end_date=end_date,
                is_recurring=bool(item.get("is_recurring", False)),
            ))
            session.flush()
            existing_list.append((session.query(CulturalEvent).filter_by(name=name).first().id, name))
            msg = f"INSERT event baru: '{name}'"
            dedup_log.append(msg)
            logger.info(f"[dedup] {msg}")

    return dedup_log


def _upsert_infrastructure(items: list[dict], session) -> list[str]:
    VALID_COND  = {"baik","sedang","rusak"}
    VALID_TYPES = {"jalan","toilet umum","mushola","loket","restoran",
                   "parkir","pusat informasi","lainnya"}
    dedup_log: list[str] = []

    existing_list = [(r.id, r.name) for r in session.query(
        TourismInfrastructure.id, TourismInfrastructure.name).all()]

    for item in items:
        name = _clean_str(item.get("name"))
        if not name:
            continue

        cond = _clean_str(item.get("stat_condition","baik")).lower()
        if cond not in VALID_COND: cond = "baik"

        inf_type = _clean_str(item.get("type","lainnya")).lower()
        if inf_type not in VALID_TYPES: inf_type = "lainnya"

        match = _find_duplicate(name, existing_list)

        if match:
            match_id, match_name, score = match
            existing = session.query(TourismInfrastructure).filter_by(id=match_id).first()
            if existing:
                existing.stat_condition   = cond
                existing.last_update = datetime.utcnow()
                _merge_fields(existing, {
                    "description": _clean_str(item.get("description",""), 2000),
                    "location":    _clean_str(item.get("location","")),
                }, ["description","location"])
                pct = int(score * 100)
                msg = f"UPDATE infrastruktur '{match_name}' ← '{name}' ({pct}%)"
                dedup_log.append(msg)
                logger.info(f"[dedup] {msg}")
        else:
            session.add(TourismInfrastructure(
                name=name, type=inf_type,
                location=_clean_str(item.get("location","")),
                stat_condition=cond,
                description=_clean_str(item.get("description",""), 2000),
                last_update=datetime.utcnow(),
            ))
            session.flush()
            existing_list.append((
                session.query(TourismInfrastructure).filter_by(name=name).first().id, name))
            msg = f"INSERT infrastruktur baru: '{name}'"
            dedup_log.append(msg)
            logger.info(f"[dedup] {msg}")

    return dedup_log


# ─── Result class ─────────────────────────────────────────────────────────────

class ExtractionResult:
    """Ringkasan hasil ekstraksi dari satu dokumen."""
    def __init__(self):
        self.attractions    = 0
        self.visitor_stats  = 0
        self.accommodations = 0
        self.events         = 0
        self.infrastructure = 0
        self.errors:   list[str] = []
        self.dedup_log: list[str] = []   # detail setiap keputusan insert/update

    @property
    def total(self) -> int:
        return (self.attractions + self.visitor_stats +
                self.accommodations + self.events + self.infrastructure)

    def summary(self) -> str:
        parts = []
        if self.attractions:    parts.append(f"{self.attractions} destinasi")
        if self.visitor_stats:  parts.append(f"{self.visitor_stats} statistik")
        if self.accommodations: parts.append(f"{self.accommodations} akomodasi")
        if self.events:         parts.append(f"{self.events} event")
        if self.infrastructure: parts.append(f"{self.infrastructure} infrastruktur")
        return ", ".join(parts) if parts else "tidak ada data terdeteksi"

    def dedup_summary(self) -> tuple[int, int]:
        """Returns (n_inserted, n_updated)."""
        n_insert = sum(1 for l in self.dedup_log if l.startswith("INSERT"))
        n_update = sum(1 for l in self.dedup_log if l.startswith("UPDATE"))
        return n_insert, n_update


# ─── Public entry point ───────────────────────────────────────────────────────

def extract_and_save(full_text: str) -> ExtractionResult:
    """
    Ekstrak data terstruktur dari teks via LLM lalu simpan ke MySQL
    dengan fuzzy deduplication.
    """
    result = ExtractionResult()

    if not full_text.strip():
        result.errors.append("Teks dokumen kosong.")
        return result

    try:
        extracted = _call_llm(full_text)
    except json.JSONDecodeError as e:
        result.errors.append(f"LLM tidak mengembalikan JSON valid: {e}")
        return result
    except Exception as e:
        result.errors.append(f"LLM error: {str(e)[:200]}")
        return result

    try:
        with db_session() as session:
            # 1. Destinasi (harus pertama — dibutuhkan FK untuk statistik)
            attractions = extracted.get("tourist_attractions") or []
            if attractions:
                name_to_id, log = _upsert_attractions(attractions, session)
                result.attractions = len(attractions)
                result.dedup_log.extend(log)
            else:
                name_to_id = {}

            # 2. Statistik kunjungan
            stats = extracted.get("visitor_statistics") or []
            if stats:
                log = _upsert_visitor_stats(stats, name_to_id, session)
                result.visitor_stats = len(stats)
                result.dedup_log.extend(log)

            # 3. Akomodasi
            accs = extracted.get("accommodations") or []
            if accs:
                log = _upsert_accommodations(accs, session)
                result.accommodations = len(accs)
                result.dedup_log.extend(log)

            # 4. Event budaya
            events = extracted.get("cultural_events") or []
            if events:
                log = _upsert_events(events, session)
                result.events = len(events)
                result.dedup_log.extend(log)

            # 5. Infrastruktur
            infra = extracted.get("tourism_infrastructure") or []
            if infra:
                log = _upsert_infrastructure(infra, session)
                result.infrastructure = len(infra)
                result.dedup_log.extend(log)

    except Exception as e:
        result.errors.append(f"DB save error: {str(e)[:200]}")
        logger.error(f"[extractor] DB error: {e}")

    n_ins, n_upd = result.dedup_summary()
    logger.success(
        f"[extractor] Selesai: {result.summary()} | "
        f"insert={n_ins}, update={n_upd}, errors={len(result.errors)}"
    )
    return result
