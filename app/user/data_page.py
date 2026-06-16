"""
app/user/data_page.py
Data browsing page – read-only tables for regular users.
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from database.connection import db_session
from database.models import TouristAttraction, Accommodation, CulturalEvent, TourismInfrastructure


def render_data_page():
    st.markdown("""
    <h2 style='color:#DAA520; font-family:Georgia,serif;'>📊 Data Pariwisata Toraja</h2>
    <p style='color:#A89070;'>Jelajahi data destinasi, akomodasi, dan event budaya Toraja.</p>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Destinasi Wisata",
        "🏨 Akomodasi",
        "🎭 Event Budaya",
        "🏗️ Infrastruktur",
    ])

    # ── Destinasi ──────────────────────────────────────────────────────────────
    with tab1:
        with db_session() as s:
            rows = s.query(TouristAttraction).filter_by(is_active=True).all()
            data = [{
                "Nama": r.name, "Kategori": r.category or "-",
                "Lokasi": r.location or "-", "Kecamatan": r.district or "-",
                "Rating": f"{r.rating:.1f}" if r.rating else "-",
                "Tiket (Rp)": f"{int(r.entry_fee):,}" if r.entry_fee else "Gratis",
            } for r in rows]

        col_f, col_cat = st.columns([3, 2])
        with col_f:
            search = st.text_input("🔍 Cari destinasi", placeholder="Nama atau lokasi...")
        with col_cat:
            categories = list({d["Kategori"] for d in data} - {"-"})
            cat_filter = st.selectbox("Filter kategori", ["Semua"] + sorted(categories))

        df = pd.DataFrame(data) if data else pd.DataFrame()
        if not df.empty:
            if search:
                mask = df["Nama"].str.contains(search, case=False, na=False) | \
                       df["Lokasi"].str.contains(search, case=False, na=False)
                df   = df[mask]
            if cat_filter != "Semua":
                df   = df[df["Kategori"] == cat_filter]
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Menampilkan {len(df)} dari {len(data)} destinasi")
        else:
            st.info("Belum ada data destinasi.")

    # ── Akomodasi ──────────────────────────────────────────────────────────────
    with tab2:
        with db_session() as s:
            rows = s.query(Accommodation).filter_by(is_active=True).all()
            data_acc = [{
                "Nama": r.name, "Tipe": r.type or "-",
                "Lokasi": r.location or "-", "Kecamatan": r.district or "-",
                "Harga Min (Rp)": f"{int(r.price_min):,}" if r.price_min else "-",
                "Harga Maks (Rp)": f"{int(r.price_max):,}" if r.price_max else "-",
                "Kapasitas": r.capacity or "-",
                "Rating": f"{r.rating:.1f}" if r.rating else "-",
            } for r in rows]

        search_acc = st.text_input("🔍 Cari akomodasi", key="acc_search")
        df_acc = pd.DataFrame(data_acc) if data_acc else pd.DataFrame()
        if not df_acc.empty:
            if search_acc:
                df_acc = df_acc[df_acc["Nama"].str.contains(search_acc, case=False, na=False)]
            st.dataframe(df_acc, use_container_width=True, hide_index=True)
            st.caption(f"Menampilkan {len(df_acc)} akomodasi")
        else:
            st.info("Belum ada data akomodasi.")

    # ── Event Budaya ───────────────────────────────────────────────────────────
    with tab3:
        with db_session() as s:
            rows = s.query(CulturalEvent).order_by(CulturalEvent.event_date).all()
            data_ev = [{
                "Nama Event": r.name,
                "Kategori": r.category or "-",
                "Lokasi": r.location or "-",
                "Tanggal": r.event_date.strftime("%d %b %Y") if r.event_date else "-",
                "Penyelenggara": r.organizer or "-",
                "Berulang": "Ya" if r.is_recurring else "Tidak",
            } for r in rows]

        df_ev = pd.DataFrame(data_ev) if data_ev else pd.DataFrame()
        if not df_ev.empty:
            st.dataframe(df_ev, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data event budaya.")

    # ── Infrastruktur ──────────────────────────────────────────────────────────
    with tab4:
        with db_session() as s:
            rows = s.query(TourismInfrastructure).all()
            data_inf = [{
                "Nama": r.name, "Tipe": r.type or "-",
                "Lokasi": r.location or "-",
                "Kondisi": r.stat_condition or "-",
                "Deskripsi": (r.description or "-")[:80],
            } for r in rows]

        df_inf = pd.DataFrame(data_inf) if data_inf else pd.DataFrame()
        if not df_inf.empty:
            cond_color = {"baik": "🟢", "sedang": "🟡", "rusak": "🔴"}
            df_inf["Kondisi"] = df_inf["Kondisi"].apply(lambda x: f"{cond_color.get(x,'')} {x}")
            st.dataframe(df_inf, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data infrastruktur.")
