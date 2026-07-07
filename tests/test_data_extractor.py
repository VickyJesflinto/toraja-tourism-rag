"""
tests/test_data_extractor.py

Unit test untuk rag/ingestion/data_extractor.py:
- _normalize()       : normalisasi teks (lowercase, hapus diakritik/tanda baca/stopwords)
- _similarity()      : skor kemiripan gabungan (SequenceMatcher + Jaccard + substring bonus)
- _find_duplicate()  : pencarian fuzzy-match terbaik dari daftar nama existing
- _to_float/_to_int/_parse_date/_clean_str : helper konversi nilai dari hasil ekstraksi LLM
- ExtractionResult   : kelas ringkasan hasil ekstraksi
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from rag.ingestion.data_extractor import (
    _normalize, _similarity, _find_duplicate,
    _to_float, _to_int, _parse_date, _clean_str,
    ExtractionResult,
)


# ─── _normalize() ──────────────────────────────────────────────────────────────

class TestNormalize:
    def test_lowercase_conversion(self):
        assert _normalize("TORAJA") == "toraja"

    def test_removes_diacritics(self):
        assert "e" in _normalize("Café")
        assert "é" not in _normalize("Café")

    def test_removes_punctuation(self):
        result = _normalize("Ke'te Kesu'!")
        assert "'" not in result
        assert "!" not in result

    def test_removes_stopwords(self):
        result = _normalize("Toraja Heritage Hotel")
        assert "hotel" not in result.split()

    def test_removes_indonesian_stopwords(self):
        result = _normalize("Wisata dan Budaya di Toraja")
        tokens = result.split()
        assert "dan" not in tokens
        assert "di" not in tokens

    def test_empty_string_returns_empty(self):
        assert _normalize("") == ""

    def test_normalizes_multiple_spaces(self):
        result = _normalize("Toraja    Utara")
        assert "  " not in result

    def test_apostrophe_variants_normalize_same(self):
        a = _normalize("Ke'te Kesu'")
        b = _normalize("Ke te kesu")
        assert a == b


# ─── _similarity() ─────────────────────────────────────────────────────────────

class TestSimilarity:
    def test_identical_strings_score_1(self):
        assert _similarity("Londa", "Londa") == 1.0

    def test_apostrophe_difference_scores_high(self):
        score = _similarity("Ke'te Kesu'", "Ke'te Kesu")
        assert score >= 0.90

    def test_substring_relationship_scores_high(self):
        score = _similarity("Londa", "Londa Toraja")
        assert score >= 0.70

    def test_word_order_difference_scores_high(self):
        score = _similarity("Hotel Toraja Heritage", "Toraja Heritage Hotel")
        assert score >= 0.90

    def test_substring_event_name_scores_high(self):
        score = _similarity("Lovely December", "Lovely December Toraja")
        assert score >= 0.70

    def test_completely_different_names_score_low(self):
        score = _similarity("Ke'te Kesu'", "Lemo")
        assert score < 0.30

    def test_different_hotels_score_low(self):
        score = _similarity("Mentirotiku Hotel", "Toraja Heritage Hotel")
        assert score < 0.30

    def test_different_attractions_score_low(self):
        score = _similarity("Lemo", "Londa")
        assert score < 0.60

    def test_empty_string_scores_zero(self):
        assert _similarity("", "Londa") == 0.0
        assert _similarity("Londa", "") == 0.0
        assert _similarity("", "") == 0.0

    def test_similarity_is_symmetric(self):
        score_ab = _similarity("Ke'te Kesu'", "Ke'te Kesu")
        score_ba = _similarity("Ke'te Kesu", "Ke'te Kesu'")
        assert abs(score_ab - score_ba) < 0.01

    def test_score_never_exceeds_one(self):
        score = _similarity("Londa", "Londa")
        assert score <= 1.0


# ─── _find_duplicate() ─────────────────────────────────────────────────────────

class TestFindDuplicate:
    EXISTING = [
        (1, "Ke'te Kesu'"),
        (2, "Lemo"),
        (3, "Toraja Heritage Hotel"),
        (4, "Lovely December Toraja"),
        (5, "Londa"),
    ]

    def test_finds_exact_match(self):
        result = _find_duplicate("Lemo", self.EXISTING)
        assert result is not None
        assert result[0] == 2

    def test_finds_fuzzy_match_apostrophe_diff(self):
        result = _find_duplicate("Ke'te Kesu", self.EXISTING)
        assert result is not None
        assert result[0] == 1

    def test_finds_fuzzy_match_word_reorder(self):
        result = _find_duplicate("Hotel Toraja Heritage", self.EXISTING)
        assert result is not None
        assert result[0] == 3

    def test_finds_fuzzy_match_substring(self):
        result = _find_duplicate("Lovely December", self.EXISTING)
        assert result is not None
        assert result[0] == 4

    def test_returns_none_for_genuinely_new_name(self):
        result = _find_duplicate("Pallawa", self.EXISTING)
        assert result is None

    def test_returns_none_for_empty_name(self):
        result = _find_duplicate("", self.EXISTING)
        assert result is None

    def test_returns_none_for_whitespace_only_name(self):
        result = _find_duplicate("   ", self.EXISTING)
        assert result is None

    def test_empty_existing_list_returns_none(self):
        result = _find_duplicate("Apapun", [])
        assert result is None

    def test_does_not_confuse_different_attractions(self):
        result = _find_duplicate("Lond", self.EXISTING, threshold=0.70)
        if result is not None:
            assert result[1] != "Lemo"

    def test_returns_best_match_among_multiple_candidates(self):
        existing = [
            (1, "Toraja Heritage Hotel"),
            (2, "Toraja Heritage"),
            (3, "Hotel Heritage"),
        ]
        result = _find_duplicate("Toraja Heritage Hotel", existing, threshold=0.70)
        assert result is not None
        assert result[0] == 1


# ─── Value helpers ─────────────────────────────────────────────────────────────

class TestToFloat:
    def test_converts_valid_string_number(self):
        assert _to_float("123.5") == 123.5

    def test_converts_int_to_float(self):
        assert _to_float(100) == 100.0

    def test_none_returns_default(self):
        assert _to_float(None) == 0.0

    def test_none_returns_custom_default(self):
        assert _to_float(None, default=99.0) == 99.0

    def test_invalid_string_returns_default(self):
        assert _to_float("bukan angka") == 0.0

    def test_negative_number_preserved(self):
        assert _to_float(-50.5) == -50.5

    def test_string_with_currency_format_fails_safely(self):
        assert _to_float("Rp 20000") == 0.0


class TestToInt:
    def test_converts_valid_string_number(self):
        assert _to_int("150") == 150

    def test_converts_float_string_truncated(self):
        assert _to_int("150.7") == 150

    def test_none_returns_default(self):
        assert _to_int(None) == 0

    def test_invalid_string_returns_default(self):
        assert _to_int("abc") == 0

    def test_custom_default(self):
        assert _to_int(None, default=1) == 1


class TestParseDate:
    def test_parses_iso_format(self):
        result = _parse_date("2024-12-25")
        assert result == datetime(2024, 12, 25)

    def test_parses_dd_mm_yyyy_with_dash(self):
        result = _parse_date("25-12-2024")
        assert result == datetime(2024, 12, 25)

    def test_parses_dd_mm_yyyy_with_slash(self):
        result = _parse_date("25/12/2024")
        assert result == datetime(2024, 12, 25)

    def test_none_returns_none(self):
        assert _parse_date(None) is None

    def test_empty_string_returns_none(self):
        assert _parse_date("") is None

    def test_invalid_date_format_returns_none(self):
        assert _parse_date("tanggal tidak valid") is None

    def test_invalid_date_value_returns_none(self):
        assert _parse_date("2024-13-99") is None


class TestCleanStr:
    def test_strips_whitespace(self):
        assert _clean_str("  Toraja  ") == "Toraja"

    def test_truncates_to_max_length(self):
        long_text = "a" * 500
        result = _clean_str(long_text, max_len=100)
        assert len(result) == 100

    def test_none_returns_empty_string(self):
        assert _clean_str(None) == ""

    def test_zero_value_returns_empty_string(self):
        assert _clean_str(0) == ""

    def test_converts_non_string_to_string(self):
        assert _clean_str(12345) == "12345"

    def test_default_max_length_255(self):
        long_text = "x" * 300
        result = _clean_str(long_text)
        assert len(result) == 255


# ─── ExtractionResult ──────────────────────────────────────────────────────────

class TestExtractionResult:
    def test_total_is_zero_when_empty(self):
        result = ExtractionResult()
        assert result.total == 0

    def test_total_sums_all_categories(self):
        result = ExtractionResult()
        result.attractions = 3
        result.visitor_stats = 5
        result.accommodations = 2
        result.events = 1
        result.infrastructure = 4
        assert result.total == 15

    def test_summary_lists_nonzero_categories_only(self):
        result = ExtractionResult()
        result.attractions = 2
        result.accommodations = 1
        summary = result.summary()
        assert "2 destinasi" in summary
        assert "1 akomodasi" in summary
        assert "statistik" not in summary

    def test_summary_when_empty(self):
        result = ExtractionResult()
        assert "tidak ada data" in result.summary().lower()

    def test_dedup_summary_counts_insert_and_update(self):
        result = ExtractionResult()
        result.dedup_log = [
            "INSERT destinasi baru: 'A'",
            "INSERT destinasi baru: 'B'",
            "UPDATE destinasi 'C' <- 'C2' (90%)",
        ]
        n_insert, n_update = result.dedup_summary()
        assert n_insert == 2
        assert n_update == 1

    def test_dedup_summary_empty_log(self):
        result = ExtractionResult()
        n_insert, n_update = result.dedup_summary()
        assert n_insert == 0
        assert n_update == 0
