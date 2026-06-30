"""
app/admin/input_data_page.py
Admin CRUD lengkap: Tambah, Edit, Hapus untuk semua data pariwisata.
"""
import streamlit as st
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.auth import require_admin
from database.connection import db_session
from database.models import (
    TouristAttraction, VisitorStatistic, Accommodation,
    CulturalEvent, TourismInfrastructure
)

CATEGORIES  = ["budaya", "alam", "religi", "kuliner", "lainnya"]
ACC_TYPES   = ["hotel", "homestay", "villa", "resort", "cottage"]
EVENT_CATS  = ["festival", "upacara", "pertunjukan", "pameran", "lainnya"]
INFRA_TYPES = ["jalan", "toilet umum", "mushola", "loket", "restoran",
               "parkir", "pusat informasi", "lainnya"]
MONTHS      = ["Jan","Feb","Mar","Apr","Mei","Jun",
               "Jul","Agu","Sep","Okt","Nov","Des"]


# ─────────────────────────────────────────────────────────────────────────────
# DESTINASI WISATA
# ─────────────────────────────────────────────────────────────────────────────
def _tab_destinasi():
    st.markdown("#### ➕ Tambah Destinasi Baru")

    with st.form("form_attr_add", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name     = c1.text_input("Nama Destinasi *")
        category = c2.selectbox("Kategori", CATEGORIES)
        c3, c4 = st.columns(2)
        location = c3.text_input("Lokasi")
        district = c4.text_input("Kecamatan")
        c5, c6, c7 = st.columns(3)
        lat   = c5.number_input("Latitude",        value=-3.0,   format="%.6f")
        lon   = c6.number_input("Longitude",       value=119.9,  format="%.6f")
        fee   = c7.number_input("Harga Tiket (Rp)", min_value=0.0, step=1000.0)
        rating = st.slider("Rating Awal", 0.0, 5.0, 4.0, 0.1)
        desc   = st.text_area("Deskripsi")
        sub_add = st.form_submit_button("💾 Tambah Destinasi", type="primary")

    if sub_add:
        if not name.strip():
            st.error("Nama destinasi wajib diisi.")
        else:
            with db_session() as s:
                s.add(TouristAttraction(
                    name=name.strip(), category=category, description=desc,
                    location=location, district=district,
                    latitude=lat or None, longitude=lon or None,
                    entry_fee=fee, rating=rating,
                ))
            st.success(f"✅ **{name}** berhasil ditambahkan.")
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Daftar Destinasi")

    # Search / filter
    col_s, col_f = st.columns([3, 2])
    search  = col_s.text_input("🔍 Cari nama / lokasi", key="attr_search", label_visibility="collapsed",
                               placeholder="Cari nama atau lokasi...")
    cat_fil = col_f.selectbox("Filter kategori", ["Semua"] + CATEGORIES, key="attr_cat_filter")

    with db_session() as s:
        q = s.query(TouristAttraction)
        if cat_fil != "Semua":
            q = q.filter_by(category=cat_fil)
        rows = q.order_by(TouristAttraction.name).all()
        attrs = [{
            "id": r.id, "name": r.name, "category": r.category or "-",
            "location": r.location or "-", "district": r.district or "-",
            "latitude": r.latitude, "longitude": r.longitude,
            "entry_fee": r.entry_fee or 0, "rating": r.rating or 0,
            "description": r.description or "", "is_active": r.is_active,
        } for r in rows]

    if search:
        kw = search.lower()
        attrs = [a for a in attrs if kw in a["name"].lower() or kw in a["location"].lower()]

    st.caption(f"Menampilkan {len(attrs)} destinasi")

    for attr in attrs:
        aid   = attr["id"]
        label = f"{'🟢' if attr['is_active'] else '🔴'} **{attr['name']}** — {attr['category']} | {attr['location']}"

        with st.expander(label, expanded=False):
            # ── Info ringkas ──────────────────────────────────────────────
            ic1, ic2, ic3, ic4 = st.columns(4)
            ic1.metric("Rating",  f"{attr['rating']:.1f} ⭐")
            ic2.metric("Tiket",   f"Rp {int(attr['entry_fee']):,}")
            ic3.metric("Kecamatan", attr["district"])
            ic4.metric("Status",  "Aktif" if attr["is_active"] else "Nonaktif")

            # ── Tombol aksi ───────────────────────────────────────────────
            act1, act2, act3, _ = st.columns([1, 1, 1, 3])
            do_edit   = act1.button("✏️ Edit",   key=f"edit_attr_{aid}")
            do_toggle = act2.button(
                "🔴 Nonaktif" if attr["is_active"] else "🟢 Aktifkan",
                key=f"tog_attr_{aid}"
            )
            do_del    = act3.button("🗑️ Hapus",  key=f"del_attr_{aid}")

            if do_toggle:
                with db_session() as s:
                    rec = s.query(TouristAttraction).filter_by(id=aid).first()
                    if rec:
                        rec.is_active = not rec.is_active
                st.cache_data.clear()
                st.rerun()

            if do_del:
                st.session_state[f"confirm_del_attr_{aid}"] = True

            if st.session_state.get(f"confirm_del_attr_{aid}"):
                st.warning(f"⚠️ Hapus **{attr['name']}**? Semua statistik terkait juga akan terhapus.")
                dc1, dc2 = st.columns(2)
                if dc1.button("✅ Ya, Hapus", key=f"yes_del_attr_{aid}", type="primary"):
                    with db_session() as s:
                        s.query(VisitorStatistic).filter_by(attraction_id=aid).delete()
                        s.query(TouristAttraction).filter_by(id=aid).delete()
                    st.session_state.pop(f"confirm_del_attr_{aid}", None)
                    st.cache_data.clear()
                    st.success("Destinasi dihapus.")
                    st.rerun()
                if dc2.button("❌ Batal", key=f"no_del_attr_{aid}"):
                    st.session_state.pop(f"confirm_del_attr_{aid}", None)
                    st.rerun()

            # ── Form Edit (ditampilkan jika tombol Edit diklik) ───────────
            if do_edit:
                st.session_state[f"editing_attr"] = aid

            if st.session_state.get("editing_attr") == aid:
                st.markdown("##### ✏️ Edit Destinasi")
                with st.form(f"form_edit_attr_{aid}"):
                    ec1, ec2 = st.columns(2)
                    e_name     = ec1.text_input("Nama *",     value=attr["name"])
                    e_category = ec2.selectbox("Kategori",    CATEGORIES,
                                               index=CATEGORIES.index(attr["category"])
                                               if attr["category"] in CATEGORIES else 0)
                    ec3, ec4 = st.columns(2)
                    e_location = ec3.text_input("Lokasi",     value=attr["location"])
                    e_district = ec4.text_input("Kecamatan",  value=attr["district"])
                    ec5, ec6, ec7 = st.columns(3)
                    e_lat  = ec5.number_input("Latitude",     value=float(attr["latitude"] or -3.0),  format="%.6f")
                    e_lon  = ec6.number_input("Longitude",    value=float(attr["longitude"] or 119.9), format="%.6f")
                    e_fee  = ec7.number_input("Harga Tiket",  value=float(attr["entry_fee"]), min_value=0.0, step=1000.0)
                    e_rating = st.slider("Rating",            0.0, 5.0, float(attr["rating"]), 0.1)
                    e_desc = st.text_area("Deskripsi",        value=attr["description"])
                    sb1, sb2 = st.columns(2)
                    save_edit   = sb1.form_submit_button("💾 Simpan Perubahan", type="primary")
                    cancel_edit = sb2.form_submit_button("✖️ Batal")

                if save_edit:
                    if not e_name.strip():
                        st.error("Nama tidak boleh kosong.")
                    else:
                        with db_session() as s:
                            rec = s.query(TouristAttraction).filter_by(id=aid).first()
                            if rec:
                                rec.name        = e_name.strip()
                                rec.category    = e_category
                                rec.location    = e_location
                                rec.district    = e_district
                                rec.latitude    = e_lat or None
                                rec.longitude   = e_lon or None
                                rec.entry_fee   = e_fee
                                rec.rating      = e_rating
                                rec.description = e_desc
                                rec.updated_at  = datetime.utcnow()
                        st.session_state.pop("editing_attr", None)
                        st.cache_data.clear()
                        st.success(f"✅ **{e_name}** berhasil diperbarui.")
                        st.rerun()

                if cancel_edit:
                    st.session_state.pop("editing_attr", None)
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# STATISTIK KUNJUNGAN
# ─────────────────────────────────────────────────────────────────────────────
def _tab_statistik():
    st.markdown("#### ➕ Input / Update Statistik Kunjungan")

    with db_session() as s:
        attrs = s.query(TouristAttraction).filter_by(is_active=True).order_by(TouristAttraction.name).all()
        attr_options = {a.name: a.id for a in attrs}

    if not attr_options:
        st.info("Belum ada destinasi aktif. Tambah destinasi terlebih dahulu.")
        return

    with st.form("form_stats", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        attr_name = c1.selectbox("Destinasi", list(attr_options.keys()))
        year      = c2.number_input("Tahun", min_value=2000, max_value=2100, value=datetime.now().year)
        month     = c3.selectbox("Bulan", list(range(1, 13)), format_func=lambda m: MONTHS[m-1])
        c4, c5, c6 = st.columns(3)
        domestic = c4.number_input("Domestik",        min_value=0, step=1)
        foreign  = c5.number_input("Mancanegara",     min_value=0, step=1)
        revenue  = c6.number_input("Pendapatan (Rp)", min_value=0.0, step=100_000.0)
        sub_stat = st.form_submit_button("💾 Simpan", type="primary")

    if sub_stat:
        attr_id = attr_options[attr_name]
        with db_session() as s:
            existing = s.query(VisitorStatistic).filter_by(
                attraction_id=attr_id, year=int(year), month=month).first()
            if existing:
                existing.domestic    = int(domestic)
                existing.foreign_vis = int(foreign)
                existing.total       = int(domestic) + int(foreign)
                existing.revenue     = float(revenue)
                msg = "diperbarui"
            else:
                s.add(VisitorStatistic(
                    attraction_id=attr_id,
                    year=int(year), month=month,
                    domestic=int(domestic), foreign_vis=int(foreign),
                    total=int(domestic) + int(foreign),
                    revenue=float(revenue),
                ))
                msg = "ditambahkan"
        st.success(f"✅ Statistik {MONTHS[month-1]} {int(year)} untuk **{attr_name}** berhasil {msg}.")
        st.cache_data.clear()

    # ── Tabel statistik ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📋 Data Statistik Tersimpan")

    sel_attr = st.selectbox("Tampilkan untuk", ["Semua Destinasi"] + list(attr_options.keys()),
                            key="stats_view_attr")
    sel_year = st.selectbox("Tahun", sorted(
        {datetime.now().year, datetime.now().year - 1}
        | set(range(2020, datetime.now().year + 1)), reverse=True
    ), key="stats_view_year")

    with db_session() as s:
        q = s.query(VisitorStatistic).filter_by(year=sel_year)
        if sel_attr != "Semua Destinasi":
            aid = attr_options[sel_attr]
            q   = q.filter_by(attraction_id=aid)
        stat_rows = q.order_by(VisitorStatistic.attraction_id,
                               VisitorStatistic.month).all()

        # Build display
        attr_id_name = {v: k for k, v in attr_options.items()}
        rows_disp = []
        for r in stat_rows:
            rows_disp.append({
                "id": r.id,
                "Destinasi":    attr_id_name.get(r.attraction_id, f"ID {r.attraction_id}"),
                "Bulan":        MONTHS[r.month - 1],
                "Domestik":     r.domestic,
                "Mancanegara":  r.foreign_vis if hasattr(r, 'foreign_vis') else r.foreign,
                "Total":        r.total,
                "Pendapatan":   f"Rp {int(r.revenue):,}",
            })

    if not rows_disp:
        st.info("Belum ada data statistik untuk filter ini.")
        return

    import pandas as pd
    df_stat = pd.DataFrame(rows_disp).drop(columns=["id"])
    st.dataframe(df_stat, use_container_width=True, hide_index=True)

    # Edit / hapus per baris
    st.markdown("**Edit atau hapus baris statistik:**")
    edit_idx = st.selectbox("Pilih baris (Destinasi — Bulan)",
                            [f"{r['Destinasi']} — {r['Bulan']}" for r in rows_disp],
                            key="stat_edit_sel")
    sel_stat = next((r for r in rows_disp
                     if f"{r['Destinasi']} — {r['Bulan']}" == edit_idx), None)
    if sel_stat:
        with st.form("form_edit_stat"):
            sc1, sc2, sc3 = st.columns(3)
            se_dom = sc1.number_input("Domestik",    value=sel_stat["Domestik"],   min_value=0, step=1)
            se_for = sc2.number_input("Mancanegara", value=sel_stat["Mancanegara"], min_value=0, step=1)
            raw_rev = int(sel_stat["Pendapatan"].replace("Rp ", "").replace(",", ""))
            se_rev = sc3.number_input("Pendapatan",  value=float(raw_rev), min_value=0.0, step=100_000.0)
            sb1, sb2 = st.columns(2)
            save_s  = sb1.form_submit_button("💾 Update", type="primary")
            del_s   = sb2.form_submit_button("🗑️ Hapus Baris Ini")

        stat_id = rows_disp[
            [f"{r['Destinasi']} — {r['Bulan']}" for r in rows_disp].index(edit_idx)
        ]["id"] if "id" in rows_disp[0] else None

        # Ambil id asli dari DB
        with db_session() as s:
            orig = s.query(VisitorStatistic).filter_by(year=sel_year)
            if sel_attr != "Semua Destinasi":
                orig = orig.filter_by(attraction_id=attr_options[sel_attr])
            orig_list = orig.order_by(VisitorStatistic.attraction_id, VisitorStatistic.month).all()
            orig_ids  = [r.id for r in orig_list]

        sel_pos = [f"{r['Destinasi']} — {r['Bulan']}" for r in rows_disp].index(edit_idx)
        if sel_pos < len(orig_ids):
            real_id = orig_ids[sel_pos]

            if save_s:
                with db_session() as s:
                    rec = s.query(VisitorStatistic).filter_by(id=real_id).first()
                    if rec:
                        rec.domestic    = int(se_dom)
                        setattr(rec, 'foreign_vis' if hasattr(rec, 'foreign_vis') else 'foreign', int(se_for))
                        rec.total       = int(se_dom) + int(se_for)
                        rec.revenue     = float(se_rev)
                st.success("✅ Statistik diperbarui.")
                st.cache_data.clear()
                st.rerun()

            if del_s:
                with db_session() as s:
                    s.query(VisitorStatistic).filter_by(id=real_id).delete()
                st.success("Baris statistik dihapus.")
                st.cache_data.clear()
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# AKOMODASI
# ─────────────────────────────────────────────────────────────────────────────
def _tab_akomodasi():
    st.markdown("#### ➕ Tambah Akomodasi")
    with st.form("form_acc_add", clear_on_submit=True):
        c1, c2 = st.columns(2)
        acc_name = c1.text_input("Nama Akomodasi *")
        acc_type = c2.selectbox("Tipe", ACC_TYPES)
        c3, c4 = st.columns(2)
        acc_loc  = c3.text_input("Lokasi")
        acc_dist = c4.text_input("Kecamatan")
        c5, c6, c7 = st.columns(3)
        p_min = c5.number_input("Harga Min (Rp)", min_value=0.0, step=10_000.0)
        p_max = c6.number_input("Harga Maks (Rp)", min_value=0.0, step=10_000.0)
        cap   = c7.number_input("Kapasitas", min_value=0, step=1)
        c8, c9, c10 = st.columns(3)
        acc_lat = c8.number_input("Latitude",  value=-3.0,   format="%.6f", key="acc_lat_add")
        acc_lon = c9.number_input("Longitude", value=119.9,  format="%.6f", key="acc_lon_add")
        acc_rat = c10.slider("Rating", 0.0, 5.0, 4.0, 0.1, key="acc_rat_add")
        sub_acc = st.form_submit_button("💾 Tambah", type="primary")

    if sub_acc:
        if not acc_name.strip():
            st.error("Nama akomodasi wajib diisi.")
        else:
            with db_session() as s:
                s.add(Accommodation(
                    name=acc_name.strip(), type=acc_type,
                    location=acc_loc, district=acc_dist,
                    price_min=p_min, price_max=p_max,
                    capacity=int(cap), rating=acc_rat,
                    latitude=acc_lat, longitude=acc_lon,
                ))
            st.success(f"✅ **{acc_name}** berhasil ditambahkan.")
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Daftar Akomodasi")

    with db_session() as s:
        accs = [{
            "id": r.id, "name": r.name, "type": r.type or "-",
            "location": r.location or "-", "district": r.district or "-",
            "price_min": r.price_min or 0, "price_max": r.price_max or 0,
            "capacity": r.capacity or 0, "rating": r.rating or 0,
            "latitude": r.latitude, "longitude": r.longitude,
            "is_active": r.is_active,
        } for r in s.query(Accommodation).order_by(Accommodation.name).all()]

    for acc in accs:
        aid   = acc["id"]
        label = f"{'🟢' if acc['is_active'] else '🔴'} **{acc['name']}** — {acc['type']} | {acc['location']}"
        with st.expander(label, expanded=False):
            ic1, ic2, ic3 = st.columns(3)
            ic1.metric("Harga Min", f"Rp {int(acc['price_min']):,}")
            ic2.metric("Harga Maks", f"Rp {int(acc['price_max']):,}")
            ic3.metric("Rating", f"{acc['rating']:.1f} ⭐")

            bt1, bt2, bt3, _ = st.columns([1, 1, 1, 3])
            if bt1.button("✏️ Edit",  key=f"edit_acc_{aid}"):
                st.session_state["editing_acc"] = aid
            if bt2.button("🟢/🔴",   key=f"tog_acc_{aid}"):
                with db_session() as s:
                    r = s.query(Accommodation).filter_by(id=aid).first()
                    if r: r.is_active = not r.is_active
                st.cache_data.clear(); st.rerun()
            if bt3.button("🗑️ Hapus", key=f"del_acc_{aid}"):
                st.session_state[f"confirm_del_acc_{aid}"] = True

            if st.session_state.get(f"confirm_del_acc_{aid}"):
                st.warning(f"⚠️ Hapus **{acc['name']}**?")
                dc1, dc2 = st.columns(2)
                if dc1.button("✅ Ya", key=f"yes_acc_{aid}", type="primary"):
                    with db_session() as s:
                        s.query(Accommodation).filter_by(id=aid).delete()
                    st.session_state.pop(f"confirm_del_acc_{aid}", None)
                    st.cache_data.clear(); st.success("Dihapus."); st.rerun()
                if dc2.button("❌ Batal", key=f"no_acc_{aid}"):
                    st.session_state.pop(f"confirm_del_acc_{aid}", None); st.rerun()

            if st.session_state.get("editing_acc") == aid:
                st.markdown("##### ✏️ Edit Akomodasi")
                with st.form(f"form_edit_acc_{aid}"):
                    ec1, ec2 = st.columns(2)
                    en = ec1.text_input("Nama *",   value=acc["name"])
                    et = ec2.selectbox("Tipe", ACC_TYPES,
                                       index=ACC_TYPES.index(acc["type"]) if acc["type"] in ACC_TYPES else 0)
                    ec3, ec4 = st.columns(2)
                    el = ec3.text_input("Lokasi",   value=acc["location"])
                    ed = ec4.text_input("Kecamatan",value=acc["district"])
                    ec5, ec6, ec7 = st.columns(3)
                    epm = ec5.number_input("Harga Min", value=float(acc["price_min"]), min_value=0.0, step=10_000.0)
                    epx = ec6.number_input("Harga Maks",value=float(acc["price_max"]), min_value=0.0, step=10_000.0)
                    ecp = ec7.number_input("Kapasitas", value=int(acc["capacity"]), min_value=0, step=1)
                    ec8, ec9, ec10 = st.columns(3)
                    ela = ec8.number_input("Latitude",  value=float(acc["latitude"] or -3.0), format="%.6f")
                    elo = ec9.number_input("Longitude", value=float(acc["longitude"] or 119.9), format="%.6f")
                    era = ec10.slider("Rating", 0.0, 5.0, float(acc["rating"]), 0.1)
                    sb1, sb2 = st.columns(2)
                    sv = sb1.form_submit_button("💾 Simpan", type="primary")
                    cx = sb2.form_submit_button("✖️ Batal")
                if sv:
                    if not en.strip():
                        st.error("Nama tidak boleh kosong.")
                    else:
                        with db_session() as s:
                            r = s.query(Accommodation).filter_by(id=aid).first()
                            if r:
                                r.name=en.strip(); r.type=et; r.location=el; r.district=ed
                                r.price_min=epm; r.price_max=epx; r.capacity=int(ecp)
                                r.latitude=ela; r.longitude=elo; r.rating=era
                                r.updated_at=datetime.utcnow()
                        st.session_state.pop("editing_acc", None)
                        st.cache_data.clear(); st.success(f"✅ **{en}** diperbarui."); st.rerun()
                if cx:
                    st.session_state.pop("editing_acc", None); st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# EVENT BUDAYA
# ─────────────────────────────────────────────────────────────────────────────
def _tab_event():
    st.markdown("#### ➕ Tambah Event Budaya")
    with st.form("form_event_add", clear_on_submit=True):
        ev_name = st.text_input("Nama Event *")
        c1, c2  = st.columns(2)
        ev_cat  = c1.selectbox("Kategori", EVENT_CATS)
        ev_org  = c2.text_input("Penyelenggara")
        c3, c4  = st.columns(2)
        ev_s    = c3.date_input("Tanggal Mulai")
        ev_e    = c4.date_input("Tanggal Selesai")
        ev_loc  = st.text_input("Lokasi")
        ev_desc = st.text_area("Deskripsi")
        ev_rec  = st.checkbox("Event berulang tahunan")
        sub_ev  = st.form_submit_button("💾 Tambah", type="primary")

    if sub_ev:
        if not ev_name.strip():
            st.error("Nama event wajib diisi.")
        else:
            with db_session() as s:
                s.add(CulturalEvent(
                    name=ev_name.strip(), category=ev_cat, organizer=ev_org,
                    location=ev_loc, description=ev_desc, is_recurring=ev_rec,
                    event_date=datetime.combine(ev_s, datetime.min.time()),
                    end_date=datetime.combine(ev_e, datetime.min.time()),
                ))
            st.success(f"✅ **{ev_name}** berhasil ditambahkan.")
            st.cache_data.clear(); st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Daftar Event")

    with db_session() as s:
        events = [{
            "id": r.id, "name": r.name, "category": r.category or "-",
            "organizer": r.organizer or "", "location": r.location or "",
            "event_date": r.event_date, "end_date": r.end_date,
            "description": r.description or "", "is_recurring": r.is_recurring,
        } for r in s.query(CulturalEvent).order_by(CulturalEvent.event_date.desc()).all()]

    for ev in events:
        eid = ev["id"]
        dt_str = ev["event_date"].strftime("%d %b %Y") if ev["event_date"] else "-"
        with st.expander(f"🎭 **{ev['name']}** — {dt_str} | {ev['category']}", expanded=False):
            bt1, bt2, bt3, _ = st.columns([1, 1, 1, 3])
            if bt1.button("✏️ Edit",  key=f"edit_ev_{eid}"):
                st.session_state["editing_ev"] = eid
            if bt3.button("🗑️ Hapus", key=f"del_ev_{eid}"):
                st.session_state[f"confirm_del_ev_{eid}"] = True

            if st.session_state.get(f"confirm_del_ev_{eid}"):
                st.warning(f"⚠️ Hapus **{ev['name']}**?")
                dc1, dc2 = st.columns(2)
                if dc1.button("✅ Ya", key=f"yes_ev_{eid}", type="primary"):
                    with db_session() as s:
                        s.query(CulturalEvent).filter_by(id=eid).delete()
                    st.session_state.pop(f"confirm_del_ev_{eid}", None)
                    st.cache_data.clear(); st.success("Dihapus."); st.rerun()
                if dc2.button("❌ Batal", key=f"no_ev_{eid}"):
                    st.session_state.pop(f"confirm_del_ev_{eid}", None); st.rerun()

            if st.session_state.get("editing_ev") == eid:
                st.markdown("##### ✏️ Edit Event")
                with st.form(f"form_edit_ev_{eid}"):
                    en  = st.text_input("Nama *",       value=ev["name"])
                    ec1, ec2 = st.columns(2)
                    ecat = ec1.selectbox("Kategori", EVENT_CATS,
                                         index=EVENT_CATS.index(ev["category"]) if ev["category"] in EVENT_CATS else 0)
                    eorg = ec2.text_input("Penyelenggara", value=ev["organizer"])
                    ec3, ec4 = st.columns(2)
                    es  = ec3.date_input("Mulai", value=ev["event_date"].date() if ev["event_date"] else None)
                    ee  = ec4.date_input("Selesai", value=ev["end_date"].date() if ev["end_date"] else None)
                    eloc = st.text_input("Lokasi",     value=ev["location"])
                    edesc= st.text_area("Deskripsi",   value=ev["description"])
                    erec = st.checkbox("Berulang tahunan", value=ev["is_recurring"])
                    sb1, sb2 = st.columns(2)
                    sv = sb1.form_submit_button("💾 Simpan", type="primary")
                    cx = sb2.form_submit_button("✖️ Batal")
                if sv:
                    if not en.strip():
                        st.error("Nama tidak boleh kosong.")
                    else:
                        with db_session() as s:
                            r = s.query(CulturalEvent).filter_by(id=eid).first()
                            if r:
                                r.name=en.strip(); r.category=ecat; r.organizer=eorg
                                r.location=eloc; r.description=edesc; r.is_recurring=erec
                                r.event_date=datetime.combine(es, datetime.min.time()) if es else None
                                r.end_date  =datetime.combine(ee, datetime.min.time()) if ee else None
                                r.updated_at=datetime.utcnow()
                        st.session_state.pop("editing_ev", None)
                        st.cache_data.clear(); st.success(f"✅ **{en}** diperbarui."); st.rerun()
                if cx:
                    st.session_state.pop("editing_ev", None); st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# INFRASTRUKTUR
# ─────────────────────────────────────────────────────────────────────────────
def _tab_infrastruktur():
    st.markdown("#### ➕ Tambah Infrastruktur")
    with st.form("form_infra_add", clear_on_submit=True):
        c1, c2  = st.columns(2)
        inf_name = c1.text_input("Nama Fasilitas *")
        inf_type = c2.selectbox("Tipe", INFRA_TYPES)
        c3, c4  = st.columns(2)
        inf_loc  = c3.text_input("Lokasi")
        inf_cond = c4.selectbox("Kondisi", ["baik", "sedang", "rusak"])
        inf_desc = st.text_area("Keterangan")
        sub_inf  = st.form_submit_button("💾 Tambah", type="primary")

    if sub_inf:
        if not inf_name.strip():
            st.error("Nama fasilitas wajib diisi.")
        else:
            with db_session() as s:
                s.add(TourismInfrastructure(
                    name=inf_name.strip(), type=inf_type, location=inf_loc,
                    stat_condition=inf_cond, description=inf_desc, last_update=datetime.utcnow(),
                ))
            st.success(f"✅ **{inf_name}** berhasil ditambahkan.")
            st.cache_data.clear(); st.rerun()

    st.markdown("---")
    st.markdown("#### 📋 Daftar Infrastruktur")
    COND_ICON = {"baik": "🟢", "sedang": "🟡", "rusak": "🔴"}

    with db_session() as s:
        infras = [{
            "id": r.id, "name": r.name, "type": r.type or "-",
            "location": r.location or "-", "condition": r.stat_condition or "baik",
            "description": r.description or "",
        } for r in s.query(TourismInfrastructure).order_by(TourismInfrastructure.name).all()]

    for inf in infras:
        iid = inf["id"]
        icon = COND_ICON.get(inf["condition"], "⚪")
        with st.expander(f"{icon} **{inf['name']}** — {inf['type']} | {inf['location']}", expanded=False):
            bt1, bt2, _ = st.columns([1, 1, 4])
            if bt1.button("✏️ Edit",  key=f"edit_inf_{iid}"):
                st.session_state["editing_inf"] = iid
            if bt2.button("🗑️ Hapus", key=f"del_inf_{iid}"):
                st.session_state[f"confirm_del_inf_{iid}"] = True

            if st.session_state.get(f"confirm_del_inf_{iid}"):
                st.warning(f"⚠️ Hapus **{inf['name']}**?")
                dc1, dc2 = st.columns(2)
                if dc1.button("✅ Ya", key=f"yes_inf_{iid}", type="primary"):
                    with db_session() as s:
                        s.query(TourismInfrastructure).filter_by(id=iid).delete()
                    st.session_state.pop(f"confirm_del_inf_{iid}", None)
                    st.cache_data.clear(); st.success("Dihapus."); st.rerun()
                if dc2.button("❌ Batal", key=f"no_inf_{iid}"):
                    st.session_state.pop(f"confirm_del_inf_{iid}", None); st.rerun()

            if st.session_state.get("editing_inf") == iid:
                st.markdown("##### ✏️ Edit Infrastruktur")
                with st.form(f"form_edit_inf_{iid}"):
                    ec1, ec2 = st.columns(2)
                    en = ec1.text_input("Nama *",   value=inf["name"])
                    et = ec2.selectbox("Tipe", INFRA_TYPES,
                                       index=INFRA_TYPES.index(inf["type"]) if inf["type"] in INFRA_TYPES else 0)
                    ec3, ec4 = st.columns(2)
                    el = ec3.text_input("Lokasi",   value=inf["location"])
                    ec = ec4.selectbox("Kondisi", ["baik","sedang","rusak"],
                                       index=["baik","sedang","rusak"].index(inf["condition"]) if inf["condition"] in ["baik","sedang","rusak"] else 0)
                    ed = st.text_area("Keterangan", value=inf["description"])
                    sb1, sb2 = st.columns(2)
                    sv = sb1.form_submit_button("💾 Simpan", type="primary")
                    cx = sb2.form_submit_button("✖️ Batal")
                if sv:
                    if not en.strip():
                        st.error("Nama tidak boleh kosong.")
                    else:
                        with db_session() as s:
                            r = s.query(TourismInfrastructure).filter_by(id=iid).first()
                            if r:
                                r.name=en.strip(); r.type=et; r.location=el
                                r.stat_condition=ec; r.description=ed
                                r.last_update=datetime.utcnow()
                        st.session_state.pop("editing_inf", None)
                        st.cache_data.clear(); st.success(f"✅ **{en}** diperbarui."); st.rerun()
                if cx:
                    st.session_state.pop("editing_inf", None); st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def render_input_data_page():
    require_admin()

    st.markdown("""
    <h2 style='color:#DAA520; font-family:Georgia,serif;'>➕ Input &amp; Kelola Data</h2>
    <p style='color:#A89070;'>Tambah, edit, dan hapus data pariwisata Toraja.</p>
    """, unsafe_allow_html=True)

    tab_attr, tab_stats, tab_acc, tab_event, tab_infra = st.tabs([
        "🗺️ Destinasi",
        "📊 Statistik Kunjungan",
        "🏨 Akomodasi",
        "🎭 Event",
        "🏗️ Infrastruktur",
    ])

    with tab_attr:   _tab_destinasi()
    with tab_stats:  _tab_statistik()
    with tab_acc:    _tab_akomodasi()
    with tab_event:  _tab_event()
    with tab_infra:  _tab_infrastruktur()
