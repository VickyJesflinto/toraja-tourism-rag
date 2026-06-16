"""
scripts/init_db.py
Initialize database tables and seed sample Toraja tourism data.

Usage:
    python scripts/init_db.py
    python scripts/init_db.py --seed   # also insert sample data
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database.connection import init_db, db_session
from database.models import TouristAttraction, Accommodation, CulturalEvent
from utils.auth import create_default_admin


SAMPLE_ATTRACTIONS = [
    {"name": "Ke'te Kesu'", "category": "budaya",
     "location": "Ke'te Kesu', Rantepao", "district": "Kesu'",
     "latitude": -2.9731, "longitude": 119.9394, "entry_fee": 20000, "rating": 4.8,
     "description": "Desa adat Toraja yang masih mempertahankan arsitektur Tongkonan asli. "
                    "Terdapat kuburan batu kuno, tau-tau (patung kayu), dan lumbung padi tradisional."},
    {"name": "Londa", "category": "budaya",
     "location": "Londa, Sanggalangi", "district": "Sanggalangi",
     "latitude": -2.9950, "longitude": 119.9183, "entry_fee": 20000, "rating": 4.7,
     "description": "Situs pemakaman tebing batu yang terkenal dengan tau-tau berusia ratusan tahun "
                    "dan terowongan gua yang menyimpan peti mati leluhur."},
    {"name": "Batu Tumonga", "category": "alam",
     "location": "Batu Tumonga, Sesean", "district": "Sesean",
     "latitude": -2.8710, "longitude": 119.9050, "entry_fee": 10000, "rating": 4.6,
     "description": "Hamparan sawah bertingkat dan batu menhir prasejarah di ketinggian sekitar 1300 mdpl. "
                    "Pemandangan Rantepao dari ketinggian sangat memukau."},
    {"name": "Pasar Bolu", "category": "budaya",
     "location": "Rantepao", "district": "Rantepao",
     "latitude": -2.9641, "longitude": 119.8983, "entry_fee": 0, "rating": 4.4,
     "description": "Pasar tradisional terbesar di Toraja yang diadakan setiap 6 hari sekali. "
                    "Terkenal sebagai pasar kerbau terbesar di Indonesia."},
    {"name": "Lemo", "category": "budaya",
     "location": "Lemo, Makale Utara", "district": "Makale Utara",
     "latitude": -3.0500, "longitude": 119.8700, "entry_fee": 20000, "rating": 4.7,
     "description": "Tebing makam dengan barisan tau-tau yang menghadap ke luar dari lubang-lubang batu. "
                    "Salah satu situs pemakaman paling ikonik di Toraja."},
    {"name": "Batutumonga Viewpoint", "category": "alam",
     "location": "Batutumonga", "district": "Sesean",
     "latitude": -2.8600, "longitude": 119.9100, "entry_fee": 5000, "rating": 4.5,
     "description": "Titik pandang terbaik untuk melihat keindahan lembah Toraja, ladang hijau, "
                    "dan perkampungan tradisional yang tersebar di lereng bukit."},
]

SAMPLE_ACCOMMODATIONS = [
    {"name": "Toraja Heritage Hotel", "type": "hotel",
     "location": "Jl. Poros Makale, Rantepao", "district": "Rantepao",
     "price_min": 850000, "price_max": 2500000, "capacity": 56, "rating": 4.6},
    {"name": "Mentirotiku Hotel", "type": "hotel",
     "location": "Jl. Landorundun, Rantepao", "district": "Rantepao",
     "price_min": 350000, "price_max": 900000, "capacity": 40, "rating": 4.2},
    {"name": "Tongkonan Homestay Ke'te Kesu'", "type": "homestay",
     "location": "Ke'te Kesu'", "district": "Kesu'",
     "price_min": 150000, "price_max": 300000, "capacity": 8, "rating": 4.5},
    {"name": "Toraja Villa Batutumonga", "type": "villa",
     "location": "Batutumonga", "district": "Sesean",
     "price_min": 500000, "price_max": 1200000, "capacity": 12, "rating": 4.7},
]

SAMPLE_EVENTS = [
    {"name": "Lovely December Toraja",
     "category": "festival",
     "location": "Rantepao & Makale",
     "event_date": datetime(datetime.now().year, 12, 1),
     "end_date": datetime(datetime.now().year, 12, 31),
     "organizer": "Dinas Pariwisata Toraja Utara",
     "is_recurring": True,
     "description": "Festival pariwisata terbesar Toraja yang diadakan setiap Desember. "
                    "Menampilkan upacara adat, pesta rakyat, pertunjukan budaya, dan wisata kuliner."},
    {"name": "Rambu Solo' (Upacara Pemakaman)",
     "category": "upacara",
     "location": "Berbagai desa adat",
     "event_date": datetime(datetime.now().year, 7, 15),
     "end_date": datetime(datetime.now().year, 7, 20),
     "organizer": "Komunitas Adat",
     "is_recurring": False,
     "description": "Upacara pemakaman adat Toraja yang sakral dan megah. "
                    "Berlangsung selama beberapa hari dengan penyembelihan kerbau dan babi."},
    {"name": "Toraja International Festival",
     "category": "festival",
     "location": "Rantepao",
     "event_date": datetime(datetime.now().year, 6, 15),
     "end_date": datetime(datetime.now().year, 6, 18),
     "organizer": "Pemkab Toraja Utara",
     "is_recurring": True,
     "description": "Festival internasional yang menampilkan seni budaya Toraja, "
                    "pertunjukan musik, dan pameran kerajinan tangan."},
]


def seed_data():
    print("Seeding sample data...")
    with db_session() as s:
        # Attractions
        for a in SAMPLE_ATTRACTIONS:
            exists = s.query(TouristAttraction).filter_by(name=a["name"]).first()
            if not exists:
                s.add(TouristAttraction(**a))
        # Accommodations
        for ac in SAMPLE_ACCOMMODATIONS:
            exists = s.query(Accommodation).filter_by(name=ac["name"]).first()
            if not exists:
                s.add(Accommodation(**ac))
        # Events
        for ev in SAMPLE_EVENTS:
            exists = s.query(CulturalEvent).filter_by(name=ev["name"]).first()
            if not exists:
                s.add(CulturalEvent(**ev))
    print("✅ Sample data seeded.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Toraja Tourism DB")
    parser.add_argument("--seed", action="store_true", help="Insert sample data")
    args = parser.parse_args()

    print("Initializing database...")
    init_db()
    print("✅ Tables created.")

    create_default_admin()
    print("✅ Default admin created.")

    if args.seed:
        seed_data()

    print("\n🏔️ Database ready! Run: streamlit run main.py")
