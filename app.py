"""
KMV Colombia — Dashboard Ejecutivo
Modelo Merton–KMV · 5 Emisores Colombianos · 2017–2022
"""

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

# ── Rutas ────────────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent

# ── Paleta y estilos ─────────────────────────────────────────────────────────
BG        = "#0d1117"
BG2       = "#161b22"
BORDER    = "#30363d"
TEXT      = "#e6edf3"
MUTED     = "#8b949e"
GREEN     = "#2ea043"
ORANGE    = "#f0883e"
BLUE      = "#58a6ff"
RED       = "#f85149"
YELLOW    = "#e3b341"
PURPLE    = "#bc8cff"

COLORES_EMISOR = {
    "ECOPETROL":    "#2ca02c",
    "BANCOLOMBIA":  "#ff7f0e",
    "BANCOBOGOTA":  "#9e9e9e",
    "CEMARGOS":     "#e3b341",
    "GRUPONUTRESA": "#ffffff",
}

NOMBRES = {
    "ECOPETROL":    "Ecopetrol",
    "BANCOLOMBIA":  "Bancolombia",
    "BANCOBOGOTA":  "Banco de Bogotá",
    "CEMARGOS":     "Cementos Argos",
    "GRUPONUTRESA": "Grupo Nutresa",
}

RATING_SCORE = {
    "AAA":1,"AA+":2,"AA":3,"AA-":4,
    "A+":5,"A":6,"A-":7,
    "BBB+":8,"BBB":9,"BBB-":10,
}
RATING_INV = {v: k for k, v in RATING_SCORE.items()}

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="KMV Colombia | Dashboard Ejecutivo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  /* Fondo general */
  .stApp {{ background-color: {BG}; color: {TEXT}; }}
  [data-testid="stSidebar"] {{
      background-color: {BG2};
      border-right: 1px solid {BORDER};
  }}
  /* Tarjetas KPI */
  .kpi-card {{
      background: {BG2};
      border: 1px solid {BORDER};
      border-radius: 10px;
      padding: 20px 24px;
      text-align: center;
  }}
  .kpi-label {{ font-size: 12px; color: {MUTED}; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }}
  .kpi-value {{ font-size: 28px; font-weight: 700; color: {TEXT}; }}
  .kpi-delta {{ font-size: 12px; margin-top: 4px; }}
  /* Sección título */
  .section-header {{
      border-left: 3px solid {ORANGE};
      padding-left: 12px;
      margin: 28px 0 16px 0;
  }}
  .section-header h2 {{ color: {TEXT}; font-size: 20px; margin: 0; }}
  .section-header p  {{ color: {MUTED}; font-size: 13px; margin: 4px 0 0 0; }}
  /* Insight box */
  .insight-box {{
      background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
      border: 1px solid {ORANGE};
      border-radius: 8px;
      padding: 16px 20px;
      margin: 12px 0;
  }}
  .insight-box p {{ margin: 0; font-size: 14px; color: {TEXT}; }}
  /* Badge emisor */
  .badge {{
      display: inline-block;
      background: {BG2};
      border: 1px solid {BORDER};
      border-radius: 20px;
      padding: 4px 12px;
      font-size: 12px;
      margin: 3px;
      color: {TEXT};
  }}
  /* Ocultar elementos Streamlit por defecto */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 1.5rem; }}
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG2,
    font=dict(color=TEXT, family="Inter, sans-serif", size=12),
    legend=dict(bgcolor=BG, bordercolor=BORDER, borderwidth=1),
    hovermode="x unified",
)

def apply_layout(fig, **kwargs):
    # Merge base layout with per-chart overrides (kwargs win)
    layout = {**PLOTLY_LAYOUT, **kwargs}
    # Always enforce grid colors on all axes
    fig.update_xaxes(gridcolor=BORDER, zeroline=False)
    fig.update_yaxes(gridcolor=BORDER, zeroline=False)
    if "margin" not in layout:
        layout["margin"] = dict(l=40, r=20, t=40, b=40)
    fig.update_layout(**layout)
    return fig

def kpi_card(label, value, delta=None, delta_color=GREEN):
    delta_html = f'<div class="kpi-delta" style="color:{delta_color}">{delta}</div>' if delta else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>"""

def section_header(title, subtitle=""):
    st.markdown(f"""
    <div class="section-header">
        <h2>{title}</h2>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>""", unsafe_allow_html=True)

def insight(text):
    st.markdown(f'<div class="insight-box"><p>💡 {text}</p></div>', unsafe_allow_html=True)

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    kmv = pd.read_csv(HERE / "parte_1" / "kmv_resultados.csv", parse_dates=["fecha"])
    kmv = kmv[kmv["PD"].notna() & (kmv["PD"] >= 0) & (kmv["PD"] <= 1)].copy()
    kmv["PD_pct"] = kmv["PD"] * 100
    kmv["nombre"] = kmv["emisor_key"].map(NOMBRES).fillna(kmv["emisor_key"])

    metricas = pd.read_csv(HERE / "parte_1" / "punto2_ecopetrol_analisis.csv", parse_dates=["fecha"])

    rating = pd.read_csv(HERE / "parte_1" / "rating_ecopetrol_historico.csv")
    rating["fecha"] = pd.to_datetime(rating["fecha"], dayfirst=True, errors="coerce")
    rating = rating.dropna(subset=["fecha", "rating_label"])
    rating["rating_label"] = rating["rating_label"].str.upper().str.strip()
    rating["score"] = rating["rating_label"].map(RATING_SCORE)
    rating = rating.dropna(subset=["score"]).sort_values("fecha")

    return kmv, metricas, rating

kmv, metricas, rating = load_data()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 16px 0 24px 0;">
        <div style="font-size:28px">📊</div>
        <div style="font-size:16px; font-weight:700; color:{TEXT};">KMV Colombia</div>
        <div style="font-size:11px; color:{MUTED};">Modelo Merton · 5 Emisores · 2017–2022</div>
    </div>""", unsafe_allow_html=True)

    pagina = st.radio(
        "Navegación",
        ["🏠  Contexto & Modelo", "📈  Punto 1 — Evolución PD", "🏆  Literal b — PD vs Rating", "🔬  Punto 2 — EEFF vs PD"],
        label_visibility="collapsed",
    )

    st.markdown(f'<hr style="border-color:{BORDER}; margin: 16px 0"/>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:11px; color:{MUTED}; padding: 0 4px;">Fuentes: SIMEV · RNVE · Yahoo Finance · Banco de la República</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — CONTEXTO & MODELO
# ══════════════════════════════════════════════════════════════════════════════
if "Contexto" in pagina:

    st.markdown(f"""
    <div style="padding: 8px 0 24px 0;">
        <div style="font-size:13px; color:{ORANGE}; letter-spacing:2px; text-transform:uppercase;">Prueba Técnica · Mercados Financieros</div>
        <div style="font-size:36px; font-weight:800; color:{TEXT}; line-height:1.2; margin: 8px 0;">
            Modelo KMV — Probabilidad de<br>Incumplimiento Histórica
        </div>
        <div style="font-size:15px; color:{MUTED}; max-width: 600px;">
            Implementación del modelo Merton–KMV para medir el riesgo de crédito estructural
            de cinco emisores colombianos listados en <strong style="color:{TEXT};">Nuam Exchange</strong>.
        </div>
    </div>""", unsafe_allow_html=True)

    # Badges emisores
    badges = "".join([f'<span class="badge">🏢 {n}</span>' for n in NOMBRES.values()])
    st.markdown(f'<div style="margin-bottom:28px">{badges}</div>', unsafe_allow_html=True)

    # ── KPIs globales ────────────────────────────────────────────────────────
    periodos     = kmv["fecha"].nunique()
    emisor_pico  = kmv.loc[kmv["PD_pct"].idxmax()]
    pd_promedio  = kmv.groupby("emisor_key")["PD_pct"].mean().mean()
    max_dd       = kmv["DD"].max()

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Períodos analizados", f"{periodos}", "Cortes trimestrales 2017–2022"), unsafe_allow_html=True)
    c2.markdown(kpi_card("PD pico registrada", f"{emisor_pico['PD_pct']:.2f}%", f"{NOMBRES.get(emisor_pico['emisor_key'], emisor_pico['emisor_key'])} · {emisor_pico['fecha'].strftime('%Y-%m')}", RED), unsafe_allow_html=True)
    c3.markdown(kpi_card("PD promedio (5 emisores)", f"{pd_promedio:.3f}%", "Media histórica"), unsafe_allow_html=True)
    c4.markdown(kpi_card("DD máximo observado", f"{max_dd:.1f}σ", "Distance to Default"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Pipeline del modelo ──────────────────────────────────────────────────
    section_header("Pipeline Metodológico", "De los datos públicos a la probabilidad de incumplimiento")

    col_pipe, col_param = st.columns([3, 1])

    with col_pipe:
        steps = [
            (BLUE,   "① XBRL / SIMEV",     "Extracción automatizada de EEFF en formato IFRS desde la RNVE. Parser: Arelle. Tags: pasivos corriente/no corriente, patrimonio, activo, utilidad."),
            (ORANGE, "② Precios & σ_E",     "Precios de cierre Yahoo Finance 2016–2022. ADR EC (×20) y CIB (×4) convertidos a COP con TRM Banco de la República. σ_E = std(log-ret) × √252 en ventana de 252 días."),
            (PURPLE, "③ Solver Merton",     "Sistema no lineal resuelto con scipy.fsolve → V_A (valor de activos) y σ_A (volatilidad de activos). Default Point: DP = PC + 0.5 × PNC."),
            (GREEN,  "④ DD → PD",           "DD = [ln(V_A/DP) + (r − ½σ_A²)T] / (σ_A√T)  →  PD = Φ(−DD)"),
        ]
        for color, title, desc in steps:
            st.markdown(f"""
            <div style="display:flex; gap:16px; align-items:flex-start; margin-bottom:14px; background:{BG2}; border-radius:8px; padding:14px 18px; border-left: 3px solid {color};">
                <div>
                    <div style="font-weight:700; font-size:14px; color:{color}; margin-bottom:4px;">{title}</div>
                    <div style="font-size:13px; color:{MUTED};">{desc}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    with col_param:
        st.markdown(f"""
        <div style="background:{BG2}; border:1px solid {BORDER}; border-radius:8px; padding:20px;">
            <div style="font-size:12px; color:{MUTED}; letter-spacing:1px; text-transform:uppercase; margin-bottom:14px;">Parámetros del Modelo</div>
            <div style="font-size:13px; line-height:2;">
                <span style="color:{MUTED};">Tasa libre de riesgo</span><br>
                <strong style="color:{TEXT};">r = 5.0 %</strong><br><br>
                <span style="color:{MUTED};">Horizonte temporal</span><br>
                <strong style="color:{TEXT};">T = 1 año</strong><br><br>
                <span style="color:{MUTED};">Ventana volatilidad</span><br>
                <strong style="color:{TEXT};">252 días hábiles</strong><br><br>
                <span style="color:{MUTED};">Default Point</span><br>
                <strong style="color:{TEXT};">PC + 0.5 × PNC</strong><br><br>
                <span style="color:{MUTED};">Período de análisis</span><br>
                <strong style="color:{TEXT};">2017 Q1 – 2022 Q1</strong>
            </div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — PUNTO 1: EVOLUCIÓN PD
# ══════════════════════════════════════════════════════════════════════════════
elif "Punto 1" in pagina:

    section_header(
        "Punto 1 — Evolución Histórica de la PD",
        "Probabilidad de incumplimiento trimestral · Modelo Merton–KMV · 5 emisores Nuam Exchange"
    )

    # Controles
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        emisores_sel = st.multiselect(
            "Emisores",
            options=list(NOMBRES.keys()),
            default=list(NOMBRES.keys()),
            format_func=lambda k: NOMBRES[k],
        )
    with col_ctrl2:
        fechas = sorted(kmv["fecha"].unique())
        rango = st.select_slider(
            "Período",
            options=[f.strftime("%Y-%m") for f in pd.to_datetime(fechas)],
            value=(pd.to_datetime(fechas[0]).strftime("%Y-%m"), pd.to_datetime(fechas[-1]).strftime("%Y-%m")),
        )

    # Filtrar
    df_plot = kmv[
        kmv["emisor_key"].isin(emisores_sel) &
        (kmv["fecha"] >= rango[0]) &
        (kmv["fecha"] <= rango[1] + "-31")
    ].copy()

    # ── Figura principal ─────────────────────────────────────────────────────
    fig = go.Figure()

    # Banda COVID
    fig.add_vrect(
        x0="2020-03-01", x1="2020-12-31",
        fillcolor=RED, opacity=0.07,
        line_width=0,
        annotation_text="COVID-19", annotation_position="top left",
        annotation_font=dict(color=RED, size=11),
    )

    for emisor_key in emisores_sel:
        sub = df_plot[df_plot["emisor_key"] == emisor_key].sort_values("fecha")
        if sub.empty:
            continue
        color = COLORES_EMISOR.get(emisor_key, TEXT)
        nombre = NOMBRES.get(emisor_key, emisor_key)
        fig.add_trace(go.Scatter(
            x=sub["fecha"], y=sub["PD_pct"],
            mode="lines+markers",
            name=nombre,
            line=dict(color=color, width=2.2),
            marker=dict(size=6, color=color),
            customdata=sub[["DD", "sigma_A", "V_A"]].values,
            hovertemplate=(
                f"<b>{nombre}</b><br>"
                "Fecha: %{x|%Y-%m}<br>"
                "PD: <b>%{y:.4f}%</b><br>"
                "DD: %{customdata[0]:.2f}σ<br>"
                "σ_A: %{customdata[1]:.1%}<br>"
                "<extra></extra>"
            ),
        ))

    apply_layout(fig,
        title=dict(text="Figura 1 — Probabilidad de Incumplimiento Histórica (5 Emisores)", font=dict(size=15)),
        yaxis=dict(title="PD (%)", tickformat=".2f", ticksuffix="%", range=[0, min(kmv["PD_pct"].max() * 1.15, 15)]),
        xaxis=dict(title="Fecha EEFF"),
        height=460,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabla resumen ────────────────────────────────────────────────────────
    section_header("Resumen por Emisor")
    resumen_rows = []
    for ek in emisores_sel:
        sub = kmv[kmv["emisor_key"] == ek]
        if sub.empty: continue
        idx_max = sub["PD_pct"].idxmax()
        resumen_rows.append({
            "Emisor":         NOMBRES.get(ek, ek),
            "PD Mínima":      f"{sub['PD_pct'].min():.4f}%",
            "PD Máxima":      f"{sub['PD_pct'].max():.4f}%",
            "PD Promedio":    f"{sub['PD_pct'].mean():.4f}%",
            "Fecha Pico":     sub.loc[idx_max, "fecha"].strftime("%Y-%m"),
            "DD en Pico":     f"{sub.loc[idx_max, 'DD']:.2f}σ",
        })
    if resumen_rows:
        df_res = pd.DataFrame(resumen_rows).set_index("Emisor")
        st.dataframe(df_res, use_container_width=True)

    insight("El choque simultáneo de precios del petróleo y la pandemia (Q1–Q2 2020) provocó los picos de PD más altos del período en todos los emisores, siendo Ecopetrol el más afectado por su exposición directa al precio del crudo.")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — LITERAL B: PD vs RATING
# ══════════════════════════════════════════════════════════════════════════════
elif "Literal b" in pagina:

    section_header(
        "Literal b — PD vs Calificación Crediticia · Ecopetrol",
        "¿Anticipa el modelo KMV los cambios de rating de Fitch Ratings Colombia?"
    )

    pd_eco = kmv[kmv["emisor_key"] == "ECOPETROL"].sort_values("fecha").copy()

    # Correlación
    if not rating.empty:
        merged_r = pd.merge_asof(pd_eco.sort_values("fecha"), rating[["fecha","score"]].sort_values("fecha"), on="fecha", direction="backward")
        corr_val = merged_r[["PD_pct","score"]].corr().iloc[0,1]
    else:
        corr_val = np.nan

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi_card("Períodos Ecopetrol", f"{len(pd_eco)}", "Cortes trimestrales"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Cambios de rating disponibles", f"{len(rating)}", "Fitch Ratings Colombia"), unsafe_allow_html=True)
    c3.markdown(kpi_card("Correlación PD ↔ Rating score", f"{corr_val:.2f}" if not np.isnan(corr_val) else "N/D", "Pearson (+ = mayor PD → peor rating)", ORANGE), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Figura dual eje ─────────────────────────────────────────────────────
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    # Banda COVID
    fig2.add_vrect(x0="2020-03-01", x1="2020-12-31",
        fillcolor=RED, opacity=0.07, line_width=0)

    # PD (eje izq)
    fig2.add_trace(go.Scatter(
        x=pd_eco["fecha"], y=pd_eco["PD_pct"],
        name="PD KMV (%)",
        mode="lines+markers",
        line=dict(color=ORANGE, width=2.5),
        marker=dict(size=7, color=ORANGE),
        customdata=pd_eco["DD"].values,
        hovertemplate="<b>PD KMV</b><br>%{x|%Y-%m}: %{y:.4f}%<br>DD: %{customdata:.2f}σ<extra></extra>",
    ), secondary_y=False)

    # Rating (eje der)
    if not rating.empty:
        for _, row in rating.iterrows():
            fig2.add_vline(
                x=row["fecha"].timestamp() * 1000,
                line_dash="dot", line_color=BLUE, line_width=1.2, opacity=0.5,
            )
            fig2.add_annotation(
                x=row["fecha"], y=1.02, yref="paper",
                text=f"<b>{row['rating_label']}</b>",
                showarrow=False, font=dict(size=10, color=BLUE),
                bgcolor=BG2, bordercolor=BLUE, borderwidth=1, borderpad=4,
            )

        fig2.add_trace(go.Scatter(
            x=rating["fecha"], y=rating["score"],
            name="Rating Fitch (ordinal)",
            mode="lines+markers",
            line=dict(color=BLUE, width=2, dash="dash"),
            marker=dict(size=9, color=BLUE, symbol="diamond"),
            text=rating["rating_label"],
            hovertemplate="<b>Rating</b><br>%{x|%Y-%m}: %{text}<extra></extra>",
        ), secondary_y=True)

    apply_layout(fig2,
        title=dict(text="Figura 2 — Ecopetrol: PD KMV vs Calificación Crediticia Fitch Colombia", font=dict(size=15)),
        xaxis=dict(title="Fecha"),
        height=480,
        legend=dict(x=0.01, y=0.99),
    )
    fig2.update_yaxes(title_text="PD (%)", secondary_y=False,
                      tickformat=".3f", ticksuffix="%", gridcolor=BORDER)
    fig2.update_yaxes(title_text="Calificación Fitch (1=AAA, mejor arriba)", secondary_y=True,
                      tickvals=list(RATING_INV.keys()),
                      ticktext=[RATING_INV[k] for k in RATING_INV.keys()],
                      autorange="reversed", gridcolor="rgba(0,0,0,0)")

    st.plotly_chart(fig2, use_container_width=True)

    insight("En 2020, la PD de Ecopetrol alcanzó su máximo histórico coincidiendo con el período de mayor incertidumbre sobre el precio del crudo. El modelo KMV captura en tiempo real la presión financiera que posteriormente se ve reflejada en las revisiones de outlook por parte de las agencias calificadoras.")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — PUNTO 2: EEFF vs PD
# ══════════════════════════════════════════════════════════════════════════════
elif "Punto 2" in pagina:

    section_header(
        "Punto 2 — Análisis Histórico de Métricas EEFF vs PD · Ecopetrol",
        "¿Qué indicadores fundamentales explican mejor la probabilidad de incumplimiento?"
    )

    df_m = metricas.copy()

    # ── Figura 3 — réplica del notebook ──────────────────────────────────────
    section_header("Figura 3 — Ecopetrol: Métricas EEFF vs PD (KMV)",
                   "EBITDA · Deuda Bruta/EBITDA · Probabilidad de incumplimiento")

    fig3_rep = make_subplots(specs=[[{"secondary_y": True}]])

    df3 = df_m[["fecha","ebitda","deuda_ebitda","PD_pct"]].dropna(subset=["ebitda"]).sort_values("fecha")
    ebitda_mm = df3["ebitda"] / 1e12  # miles de millones COP

    # Barras EBITDA
    fig3_rep.add_trace(go.Bar(
        x=df3["fecha"], y=ebitda_mm,
        name="EBITDA",
        marker_color="#4a5568",
        opacity=0.85,
        hovertemplate="%{x|%Y-%m}<br>EBITDA: %{y:.1f} B COP<extra></extra>",
    ), secondary_y=False)

    # Línea Deuda/EBITDA
    fig3_rep.add_trace(go.Scatter(
        x=df3["fecha"], y=df3["deuda_ebitda"],
        name="Deuda Bruta / EBITDA",
        mode="lines+markers",
        line=dict(color=ORANGE, width=2.2),
        marker=dict(size=6),
        hovertemplate="%{x|%Y-%m}<br>Deuda/EBITDA: %{y:.1f}×<extra></extra>",
    ), secondary_y=True)

    # Línea PD
    fig3_rep.add_trace(go.Scatter(
        x=df3["fecha"], y=df3["PD_pct"],
        name="PD KMV (%)",
        mode="lines+markers",
        line=dict(color=RED, width=2, dash="dash"),
        marker=dict(size=6, symbol="triangle-up", color=RED),
        hovertemplate="%{x|%Y-%m}<br>PD: %{y:.3f}%<extra></extra>",
    ), secondary_y=True)

    apply_layout(fig3_rep,
        title=dict(text="Figura 3 — Ecopetrol: Métricas EEFF vs PD (KMV)", font=dict(size=14)),
        xaxis=dict(title="Fecha EEFF"),
        height=420,
        legend=dict(orientation="h", y=1.08, x=0),
        barmode="group",
    )
    fig3_rep.update_yaxes(title_text="EBITDA (billones COP)", secondary_y=False, gridcolor=BORDER)
    fig3_rep.update_yaxes(title_text="Deuda/EBITDA  |  PD (%)", secondary_y=True, gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3_rep, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # KPIs rápidos
    c1, c2, c3, c4 = st.columns(4)
    pd_max_row = df_m.loc[df_m["PD_pct"].idxmax()]
    pd_min_row = df_m.loc[df_m["PD_pct"].idxmin()]
    c1.markdown(kpi_card("Período mayor PD",   pd_max_row["fecha"].strftime("%Y-%m"), f"PD: {pd_max_row['PD_pct']:.3f}%", RED), unsafe_allow_html=True)
    c2.markdown(kpi_card("Cob. intereses (pico PD)", f"{pd_max_row['ebit_intereses']:.1f}×", "EBIT / Costos financieros", RED), unsafe_allow_html=True)
    c3.markdown(kpi_card("Período menor PD",   pd_min_row["fecha"].strftime("%Y-%m"), f"PD: {pd_min_row['PD_pct']:.3f}%", GREEN), unsafe_allow_html=True)
    c4.markdown(kpi_card("Cob. intereses (mín PD)", f"{pd_min_row['ebit_intereses']:.1f}×", "EBIT / Costos financieros", GREEN), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 4 paneles ────────────────────────────────────────────────────────────
    metricas_config = [
        ("deuda_ebitda",      "Deuda Neta / EBITDA",        "×",   RED,    "Apalancamiento — mayor ratio implica mayor riesgo"),
        ("ebit_intereses",    "EBIT / Intereses",           "×",   GREEN,  "Cobertura — menor ratio implica mayor riesgo"),
        ("margen_ebitda_pct", "Margen EBITDA",              "%",   BLUE,   "Rentabilidad operativa"),
        ("razon_corriente",   "Razón Corriente",            "×",   YELLOW, "Liquidez — activo corriente / pasivo corriente"),
    ]

    for i in range(0, 4, 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            campo, titulo, unidad, color, desc = metricas_config[i + j]
            if campo not in df_m.columns:
                col.warning(f"Campo '{campo}' no disponible")
                continue

            sub = df_m[["fecha", campo, "PD_pct"]].dropna(subset=[campo]).sort_values("fecha")

            fig_p = make_subplots(specs=[[{"secondary_y": True}]])
            fig_p.add_trace(go.Bar(
                x=sub["fecha"], y=sub[campo],
                name=titulo,
                marker_color=color,
                opacity=0.75,
                hovertemplate=f"%{{x|%Y-%m}}: %{{y:.2f}}{unidad}<extra></extra>",
            ), secondary_y=False)
            fig_p.add_trace(go.Scatter(
                x=sub["fecha"], y=sub["PD_pct"],
                name="PD KMV",
                mode="lines+markers",
                line=dict(color=ORANGE, width=2),
                marker=dict(size=5),
                hovertemplate="%{x|%Y-%m}: PD %{y:.3f}%<extra></extra>",
            ), secondary_y=True)
            apply_layout(fig_p,
                title=dict(text=titulo, font=dict(size=13)),
                height=280, margin=dict(l=30, r=30, t=40, b=30),
                showlegend=False,
            )
            fig_p.update_yaxes(title_text=unidad, secondary_y=False, gridcolor=BORDER)
            fig_p.update_yaxes(title_text="PD (%)", secondary_y=True, ticksuffix="%", gridcolor="rgba(0,0,0,0)")

            col.plotly_chart(fig_p, use_container_width=True)
            col.markdown(f'<div style="font-size:11px; color:{MUTED}; margin-top:-12px; margin-bottom:8px">{desc}</div>', unsafe_allow_html=True)

    # ── Heatmap de correlaciones ──────────────────────────────────────────────
    section_header("Correlaciones con la PD", "Pearson · métricas EEFF vs probabilidad de incumplimiento")

    corr_cols = ["deuda_ebitda", "ebit_intereses", "margen_ebitda_pct", "margen_neto_pct", "razon_corriente", "caja_activos_pct"]
    corr_cols = [c for c in corr_cols if c in df_m.columns]
    corr_labels = ["Deuda/EBITDA", "EBIT/Intereses", "Mg. EBITDA", "Mg. Neto", "Razón Cte.", "Caja/Activos"][:len(corr_cols)]

    corr_vals = [df_m[["PD_pct", c]].dropna().corr().iloc[0, 1] for c in corr_cols]

    fig_corr = go.Figure(go.Bar(
        x=corr_labels,
        y=corr_vals,
        marker_color=[RED if v > 0 else GREEN for v in corr_vals],
        text=[f"{v:.2f}" for v in corr_vals],
        textposition="outside",
        textfont=dict(color=TEXT),
        hovertemplate="%{x}: r = %{y:.3f}<extra></extra>",
    ))
    apply_layout(fig_corr,
        title=dict(text="Correlación de Pearson con PD (+ = mayor métrica → mayor riesgo)", font=dict(size=13)),
        yaxis=dict(range=[-1.1, 1.1], zeroline=True, zerolinecolor=BORDER, zerolinewidth=1),
        height=320,
        showlegend=False,
    )
    fig_corr.add_hline(y=0, line_color=BORDER)
    st.plotly_chart(fig_corr, use_container_width=True)

    # ── Tabla comparativa ────────────────────────────────────────────────────
    section_header("Comparativo: Mayor PD vs Menor PD")

    col_names = {"deuda_ebitda":"Deuda/EBITDA","ebit_intereses":"EBIT/Intereses",
                 "margen_ebitda_pct":"Mg. EBITDA (%)","margen_neto_pct":"Mg. Neto (%)",
                 "razon_corriente":"Razón Corriente","caja_activos_pct":"Caja/Activos (%)"}

    rows = {"Métrica": [], "Mayor PD": [], "Menor PD": [], "Δ": []}
    for campo, label in col_names.items():
        if campo not in df_m.columns: continue
        v_max = df_m.loc[df_m["PD_pct"].idxmax(), campo]
        v_min = df_m.loc[df_m["PD_pct"].idxmin(), campo]
        rows["Métrica"].append(label)
        rows["Mayor PD"].append(f"{v_max:.2f}")
        rows["Menor PD"].append(f"{v_min:.2f}")
        rows["Δ"].append(f"{v_max - v_min:+.2f}")
    st.dataframe(pd.DataFrame(rows).set_index("Métrica"), use_container_width=True)

    insight("La cobertura de intereses (EBIT/Intereses) y el margen EBITDA son las métricas con mayor correlación negativa con la PD: cuando la rentabilidad operativa cae, el riesgo de crédito estructural sube de forma consistente.")
