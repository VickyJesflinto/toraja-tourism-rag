"""
app/user/dashboard.py 
Public-facing monitoring dashboard for Toraja Tourism.
Shows KPIs, visitor trends, top attractions, accommodation stats.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from database.connection import db_session
from database.models import (
    TouristAttraction, VisitorStatistic, Accommodation,
    CulturalEvent, TourismInfrastructure
)


# ─── Data Loaders ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_visitor_stats():
    with db_session() as s:
        rows = s.query(VisitorStatistic).all()
        data = [{
            "year": r.year, "month": r.month,
            "domestic": r.domestic, "foreign": r.foreign_vis,
            "total": r.total, "revenue": r.revenue,
            "attraction_id": r.attraction_id
        } for r in rows]
    return pd.DataFrame(data) if data else pd.DataFrame(
        columns=["year","month","domestic","foreign","total","revenue","attraction_id"])


@st.cache_data(ttl=300)
def load_attractions():
    with db_session() as s:
        rows = s.query(TouristAttraction).filter_by(is_active=True).all()
        data = [{
            "id": r.id, "name": r.name, "category": r.category,
            "location": r.location, "district": r.district,
            "rating": r.rating, "entry_fee": r.entry_fee,
            "latitude": r.latitude, "longitude": r.longitude
        } for r in rows]
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_accommodations():
    with db_session() as s:
        rows = s.query(Accommodation).filter_by(is_active=True).all()
        data = [{
            "name": r.name, "type": r.type,
            "district": r.district, "price_min": r.price_min,
            "price_max": r.price_max, "rating": r.rating,
            "capacity": r.capacity,
        } for r in rows]
    return pd.DataFrame(data) if data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_upcoming_events():
    now = datetime.utcnow()
    with db_session() as s:
        rows = s.query(CulturalEvent)\
                .filter(CulturalEvent.event_date >= now)\
                .order_by(CulturalEvent.event_date)\
                .limit(5).all()
        data = [{
            "name": r.name, "category": r.category,
            "location": r.location,
            "date": r.event_date.strftime("%d %b %Y") if r.event_date else "-"
        } for r in rows]
    return data


# ─── Chart Helpers ────────────────────────────────────────────────────────────
MONTH_NAMES = ["Jan","Feb","Mar","Apr","Mei","Jun",
               "Jul","Agu","Sep","Okt","Nov","Des"]

TORAJA_COLORS = {
    "primary": "#B8860B",
    "secondary": "#8B4513",
    "accent": "#DAA520",
    "domestic": "#E07B39",
    "foreign": "#5B8DB8",
    "bg": "#1C1A16",
    "card": "#2A2620",
}


def render_dashboard():
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #2A2620 0%, #1C1A16 100%);
        border: 1px solid #B8860B33;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #DAA520;
        font-family: Georgia, serif;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #A89070;
        margin-top: 0.2rem;
    }
    .metric-delta-up   { color: #4CAF50; font-size: 0.8rem; }
    .metric-delta-down { color: #F44336; font-size: 0.8rem; }
    .section-header {
        color: #DAA520;
        font-family: Georgia, serif;
        border-bottom: 2px solid #B8860B33;
        padding-bottom: 0.4rem;
        margin: 1.5rem 0 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='
        background: linear-gradient(135deg, #2A1F0A 0%, #1C1508 100%);
        border: 1px solid #B8860B55;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
    '>
        <h1 style='color:#DAA520; font-family: Georgia, serif; margin:0; font-size:2.2rem;'>
            Dashboard Pariwisata Toraja
        </h1>
        <p style='color:#A89070; margin:0.5rem 0 0 0;'>
            Monitoring real-time statistik wisata Toraja, Sulawesi Selatan
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load Data ─────────────────────────────────────────────────────────────
    df_stats  = load_visitor_stats()
    df_attr   = load_attractions()
    df_acc    = load_accommodations()
    events    = load_upcoming_events()

    # ── Year Filter ───────────────────────────────────────────────────────────
    years = sorted(df_stats["year"].unique().tolist(), reverse=True) if not df_stats.empty else [datetime.now().year]
    col_y, _ = st.columns([2, 8])
    with col_y:
        sel_year = st.selectbox("Tahun", years, index=0) if years else datetime.now().year

    df_year = df_stats[df_stats["year"] == sel_year] if not df_stats.empty else df_stats

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    total_visitors = int(df_year["total"].sum())
    total_domestic = int(df_year["domestic"].sum())
    total_foreign  = int(df_year["foreign"].sum())
    total_revenue  = float(df_year["revenue"].sum())
    num_attractions = len(df_attr)
    num_accomm      = len(df_acc)

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    def metric_card(col, icon, label, value, delta=None):
        delta_html = ""
        if delta is not None:
            cls  = "metric-delta-up" if delta >= 0 else "metric-delta-down"
            sign = "▲" if delta >= 0 else "▼"
            delta_html = f"<div class='{cls}'>{sign} {abs(delta):.1f}%</div>"
        col.markdown(f"""
        <div class='metric-card'>
            <div style='font-size:1.4rem'>{icon}</div>
            <div class='metric-value'>{value}</div>
            <div class='metric-label'>{label}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

    metric_card(c1, "👥", "Total Wisatawan",   f"{total_visitors:,}")
    metric_card(c2, "🏠", "Wisatawan Domestik", f"{total_domestic:,}")
    metric_card(c3, "✈️", "Wisatawan Mancanegara", f"{total_foreign:,}")
    metric_card(c4, "💰", "Total Pendapatan", f"Rp {total_revenue/1e9:.2f}M")
    metric_card(c5, "🗺️", "Destinasi Aktif", str(num_attractions))
    metric_card(c6, "🏨", "Akomodasi",        str(num_accomm))

    st.markdown("---")

    # ── Visitor Trend ─────────────────────────────────────────────────────────
    st.markdown("<h3 class='section-header'>📈 Tren Kunjungan Bulanan</h3>", unsafe_allow_html=True)

    if not df_year.empty:
        monthly = df_year.groupby("month")[["domestic","foreign","total"]].sum().reset_index()
        monthly["bulan"] = monthly["month"].apply(lambda m: MONTH_NAMES[m-1])

        fig = go.Figure()
        fig.add_bar(x=monthly["bulan"], y=monthly["domestic"],
                    name="Domestik", marker_color=TORAJA_COLORS["domestic"])
        fig.add_bar(x=monthly["bulan"], y=monthly["foreign"],
                    name="Mancanegara", marker_color=TORAJA_COLORS["foreign"])
        fig.add_scatter(x=monthly["bulan"], y=monthly["total"],
                        name="Total", mode="lines+markers",
                        line=dict(color=TORAJA_COLORS["accent"], width=2.5),
                        marker=dict(size=7))
        fig.update_layout(
            barmode="stack",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#A89070"),
            legend=dict(orientation="h", y=1.1),
            xaxis=dict(gridcolor="#333"),
            yaxis=dict(gridcolor="#333", title="Jumlah Wisatawan"),
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Belum ada data statistik kunjungan.")

    # ── Row 2: Category pie + Top Attractions ─────────────────────────────────
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown("<h3 class='section-header'>🗂️ Kategori Destinasi</h3>", unsafe_allow_html=True)
        if not df_attr.empty and "category" in df_attr.columns:
            cat_counts = df_attr["category"].value_counts().reset_index()
            cat_counts.columns = ["Kategori", "Jumlah"]
            fig_pie = px.pie(
                cat_counts, names="Kategori", values="Jumlah",
                color_discrete_sequence=px.colors.sequential.YlOrBr,
                hole=0.45,
            )
            fig_pie.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A89070"),
                height=320,
                showlegend=True,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Belum ada data destinasi.")

    with col_r:
        st.markdown("<h3 class='section-header'>⭐ Top Destinasi (Rating)</h3>", unsafe_allow_html=True)
        if not df_attr.empty and "rating" in df_attr.columns:
            top = df_attr.nlargest(8, "rating")[["name","rating","category"]].copy()
            fig_bar = px.bar(
                top, x="rating", y="name", orientation="h",
                color="rating",
                color_continuous_scale="YlOrBr",
                text="rating",
            )
            fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A89070"),
                coloraxis_showscale=False,
                yaxis=dict(title=""),
                xaxis=dict(range=[0, 6], title="Rating"),
                height=320,
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Belum ada data destinasi.")

    # ── Revenue Trend ─────────────────────────────────────────────────────────
    if not df_year.empty and df_year["revenue"].sum() > 0:
        st.markdown("<h3 class='section-header'>💰 Pendapatan Bulanan (IDR)</h3>", unsafe_allow_html=True)
        rev_monthly = df_year.groupby("month")["revenue"].sum().reset_index()
        rev_monthly["bulan"] = rev_monthly["month"].apply(lambda m: MONTH_NAMES[m-1])
        fig_rev = px.area(
            rev_monthly, x="bulan", y="revenue",
            color_discrete_sequence=[TORAJA_COLORS["accent"]],
            labels={"revenue": "Pendapatan (IDR)", "bulan": "Bulan"},
        )
        fig_rev.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#A89070"),
            xaxis=dict(gridcolor="#333"),
            yaxis=dict(gridcolor="#333"),
            height=280,
        )
        st.plotly_chart(fig_rev, use_container_width=True)

    # ── Row 3: Accommodation + Events ─────────────────────────────────────────
    col_a, col_e = st.columns([1, 1])

    with col_a:
        st.markdown("<h3 class='section-header'>🏨 Tipe Akomodasi</h3>", unsafe_allow_html=True)
        if not df_acc.empty and "type" in df_acc.columns:
            acc_type = df_acc["type"].value_counts().reset_index()
            acc_type.columns = ["Tipe", "Jumlah"]
            fig_acc = px.bar(
                acc_type, x="Tipe", y="Jumlah",
                color="Jumlah", color_continuous_scale="YlOrBr",
            )
            fig_acc.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A89070"),
                coloraxis_showscale=False,
                height=280,
            )
            st.plotly_chart(fig_acc, use_container_width=True)
        else:
            st.info("Belum ada data akomodasi.")

    with col_e:
        st.markdown("<h3 class='section-header'>🎭 Event Budaya Terdekat</h3>", unsafe_allow_html=True)
        if events:
            for ev in events:
                st.markdown(f"""
                <div style='
                    background:#2A2620; border-left: 3px solid #B8860B;
                    border-radius: 8px; padding: 0.7rem 1rem; margin-bottom: 0.5rem;
                '>
                    <b style='color:#DAA520'>{ev['name']}</b><br>
                    <small style='color:#A89070'>
                        📍 {ev['location']} &nbsp;|&nbsp; 📅 {ev['date']}
                        &nbsp;|&nbsp; 🏷️ {ev['category'] or '-'}
                    </small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Tidak ada event mendatang.")

    # ── Map ───────────────────────────────────────────────────────────────────
    if not df_attr.empty:
        map_df = df_attr.dropna(subset=["latitude","longitude"])
        if not map_df.empty:
            st.markdown("<h3 class='section-header'>🗺️ Peta Destinasi Wisata</h3>", unsafe_allow_html=True)
            fig_map = px.scatter_mapbox(
                map_df,
                lat="latitude", lon="longitude",
                hover_name="name",
                hover_data={"category": True, "rating": True,
                            "latitude": False, "longitude": False},
                color="category",
                size_max=15,
                zoom=9,
                mapbox_style="carto-darkmatter",
                height=450,
            )
            fig_map.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A89070"),
                margin=dict(l=0, r=0, t=0, b=0),
            )
            st.plotly_chart(fig_map, use_container_width=True)
