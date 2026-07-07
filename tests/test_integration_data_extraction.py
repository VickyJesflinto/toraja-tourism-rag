"""
tests/test_integration_data_extraction.py

Integration Test: Data Extraction -> Fuzzy Dedup -> Multi-Table Database
============================================================================
Menguji alur kerja gabungan: hasil ekstraksi LLM (disimulasikan/mocked karena
membutuhkan API key OpenRouter sungguhan) -> upsert ke 5 tabel pariwisata
sekaligus -> verifikasi data tersimpan dengan benar dan tidak terjadi duplikasi
saat nama yang diekstrak mirip (bukan identik) dengan data yang sudah ada.

Berbeda dengan unit test fuzzy matching (_normalize, _similarity, _find_duplicate)
yang murni menguji fungsi matematis di memory, integration test ini menguji
seluruh fungsi _upsert_* bersama database SQLite nyata, termasuk:
- Foreign Key attraction_id pada statistik kunjungan benar-benar valid
- Data yang sudah ada (existing) ikut dipertimbangkan saat fuzzy matching
- Beberapa kategori data ter-upsert dalam satu transaksi yang konsisten

Strategi mocking: hanya _call_llm() yang dipatch (mengembalikan dict statis
seolah-olah itu hasil panggilan LLM nyata). Semua logika upsert/dedup/database
di bawahnya tetap berjalan asli tanpa modifikasi.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


@pytest.fixture
def mock_llm_response(monkeypatch):
    """
    Patch data_extractor._call_llm agar mengembalikan dict statis tanpa
    benar-benar memanggil OpenRouter API.
    """
    import rag.ingestion.data_extractor as extractor_module

    state = {"response": {}}

    def fake_call_llm(text: str) -> dict:
        return state["response"]

    monkeypatch.setattr(extractor_module, "_call_llm", fake_call_llm)

    class Setter:
        def set(self, response: dict):
            state["response"] = response

    return Setter()


class TestExtractionBasicUpsert:
    def test_extract_and_save_inserts_new_attraction(self, test_db, mock_llm_response):
        from database.connection import db_session
        from database.models import TouristAttraction
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({
            "tourist_attractions": [{
                "name": "Ke'te Kesu",
                "category": "budaya",
                "description": "Desa wisata budaya Toraja",
                "location": "Kesu",
                "district": "Kesu",
                "entry_fee": 20000,
                "rating": 4.8,
            }]
        })

        result = extract_and_save("dummy text, isinya tidak relevan karena LLM di-mock")

        assert result.attractions == 1
        assert result.errors == []

        with db_session() as s:
            attr = s.query(TouristAttraction).filter_by(name="Ke'te Kesu").first()
            assert attr is not None
            assert attr.category == "budaya"
            assert attr.entry_fee == 20000

    def test_extract_and_save_inserts_multiple_categories_in_one_call(
        self, test_db, mock_llm_response
    ):
        from database.connection import db_session
        from database.models import TouristAttraction, Accommodation, CulturalEvent
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({
            "tourist_attractions": [
                {"name": "Londa", "category": "budaya"},
            ],
            "accommodations": [
                {"name": "Toraja Heritage Hotel", "type": "hotel", "price_min": 850000},
            ],
            "cultural_events": [
                {"name": "Lovely December", "category": "festival"},
            ],
        })

        result = extract_and_save("dummy text")

        assert result.attractions == 1
        assert result.accommodations == 1
        assert result.events == 1

        with db_session() as s:
            assert s.query(TouristAttraction).filter_by(name="Londa").first() is not None
            assert s.query(Accommodation).filter_by(name="Toraja Heritage Hotel").first() is not None
            assert s.query(CulturalEvent).filter_by(name="Lovely December").first() is not None

    def test_extract_and_save_handles_empty_text(self, test_db, mock_llm_response):
        from rag.ingestion.data_extractor import extract_and_save

        result = extract_and_save("")
        assert result.total == 0
        assert len(result.errors) > 0


class TestExtractionVisitorStatisticsForeignKey:
    def test_visitor_stats_linked_to_correct_attraction_id(self, test_db, mock_llm_response):
        from database.connection import db_session
        from database.models import TouristAttraction, VisitorStatistic
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({
            "tourist_attractions": [
                {"name": "Lemo", "category": "budaya"},
                {"name": "Tilanga", "category": "alam"},
            ],
            "visitor_statistics": [
                {"attraction_name": "Lemo", "year": 2024, "month": 6,
                 "domestic": 500, "foreign_vis": 50, "revenue": 11000000},
                {"attraction_name": "Tilanga", "year": 2024, "month": 6,
                 "domestic": 200, "foreign_vis": 10, "revenue": 3000000},
            ],
        })

        extract_and_save("dummy text")

        with db_session() as s:
            lemo = s.query(TouristAttraction).filter_by(name="Lemo").first()
            tilanga = s.query(TouristAttraction).filter_by(name="Tilanga").first()

            lemo_stat = s.query(VisitorStatistic).filter_by(attraction_id=lemo.id).first()
            tilanga_stat = s.query(VisitorStatistic).filter_by(attraction_id=tilanga.id).first()

            assert lemo_stat.domestic == 500
            assert tilanga_stat.domestic == 200
            assert lemo_stat.id != tilanga_stat.id

    def test_visitor_stats_for_unknown_attraction_is_skipped_not_crashed(
        self, test_db, mock_llm_response
    ):
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({
            "visitor_statistics": [
                {"attraction_name": "Destinasi Yang Tidak Ada Sama Sekali XYZ123",
                 "year": 2024, "month": 1, "domestic": 100, "foreign_vis": 5},
            ],
        })

        result = extract_and_save("dummy text")
        assert result is not None


class TestExtractionFuzzyDedupIntegration:
    """
    Pengujian inti: skenario dunia nyata di mana dokumen ke-2 yang diupload
    berisi destinasi yang sama dengan dokumen ke-1, namun dengan variasi
    penulisan nama -- harus ter-update, bukan menjadi record baru (duplikat).
    """

    def test_second_upload_with_apostrophe_variant_updates_not_duplicates(
        self, test_db, mock_llm_response
    ):
        from database.connection import db_session
        from database.models import TouristAttraction
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({
            "tourist_attractions": [{
                "name": "Ke'te Kesu'", "category": "budaya",
                "description": "", "entry_fee": 20000, "rating": 0,
            }]
        })
        extract_and_save("dokumen pertama")

        mock_llm_response.set({
            "tourist_attractions": [{
                "name": "Ke'te Kesu",
                "category": "budaya",
                "description": "Desa wisata budaya terkenal di Toraja Utara",
                "rating": 4.8,
            }]
        })
        result = extract_and_save("dokumen kedua")

        with db_session() as s:
            all_matching = s.query(TouristAttraction).filter(
                TouristAttraction.name.like("%Kesu%")
            ).all()
            assert len(all_matching) == 1

            attr = all_matching[0]
            assert attr.description != ""
            assert attr.rating == 4.8

        n_insert, n_update = result.dedup_summary()
        assert n_insert == 0
        assert n_update == 1

    def test_second_upload_with_reordered_hotel_name_updates_not_duplicates(
        self, test_db, mock_llm_response
    ):
        from database.connection import db_session
        from database.models import Accommodation
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({
            "accommodations": [{"name": "Toraja Heritage Hotel", "type": "hotel"}]
        })
        extract_and_save("dokumen pertama")

        mock_llm_response.set({
            "accommodations": [{"name": "Hotel Toraja Heritage", "type": "hotel",
                                "price_min": 850000, "price_max": 2500000}]
        })
        extract_and_save("dokumen kedua")

        with db_session() as s:
            all_hotels = s.query(Accommodation).filter(
                Accommodation.name.like("%Toraja Heritage%")
            ).all()
            assert len(all_hotels) == 1
            assert all_hotels[0].price_min == 850000

    def test_genuinely_different_attractions_both_get_inserted(
        self, test_db, mock_llm_response
    ):
        from database.connection import db_session
        from database.models import TouristAttraction
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({
            "tourist_attractions": [{"name": "Lemo", "category": "budaya"}]
        })
        extract_and_save("dokumen 1")

        mock_llm_response.set({
            "tourist_attractions": [{"name": "Londa", "category": "budaya"}]
        })
        extract_and_save("dokumen 2")

        with db_session() as s:
            count = s.query(TouristAttraction).count()
            assert count == 2

    def test_multiple_uploads_accumulate_dedup_log_correctly(self, test_db, mock_llm_response):
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({"tourist_attractions": [{"name": "Pallawa", "category": "budaya"}]})
        r1 = extract_and_save("doc1")
        assert r1.dedup_summary() == (1, 0)

        mock_llm_response.set({"tourist_attractions": [{"name": "Pallawa", "category": "budaya",
                                                          "rating": 4.5}]})
        r2 = extract_and_save("doc2")
        assert r2.dedup_summary() == (0, 1)


class TestExtractionDataIntegrity:
    def test_extracted_revenue_and_visitor_numbers_stored_as_correct_types(
        self, test_db, mock_llm_response
    ):
        from database.connection import db_session
        from database.models import TouristAttraction, VisitorStatistic
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({
            "tourist_attractions": [{"name": "Batu Tumonga", "category": "alam"}],
            "visitor_statistics": [{
                "attraction_name": "Batu Tumonga", "year": 2024, "month": 7,
                "domestic": "1500", "foreign_vis": "230", "revenue": "45000000.50",
            }],
        })
        extract_and_save("dummy")

        with db_session() as s:
            attr = s.query(TouristAttraction).filter_by(name="Batu Tumonga").first()
            stat = s.query(VisitorStatistic).filter_by(attraction_id=attr.id).first()
            assert stat.domestic == 1500
            assert stat.foreign_vis == 230
            assert isinstance(stat.domestic, int)
            assert stat.total == 1500 + 230

    def test_invalid_category_falls_back_to_default(self, test_db, mock_llm_response):
        from database.connection import db_session
        from database.models import TouristAttraction
        from rag.ingestion.data_extractor import extract_and_save

        mock_llm_response.set({
            "tourist_attractions": [{"name": "Destinasi Aneh", "category": "kategori_ngarang_bebas"}]
        })
        extract_and_save("dummy")

        with db_session() as s:
            attr = s.query(TouristAttraction).filter_by(name="Destinasi Aneh").first()
            assert attr.category == "lainnya"
