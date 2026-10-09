"""
environment.py — Caso studio "ENVIRONMENT FOOTPRINT EVENT" (EF 3.1)
=====================================================================

"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).parent

# ── Mapping ISO → nome paese / ISO3 (per il choropleth) ─────────────────────
ISO_TO_NAME = {
    "AT": "Austria",        "BE": "Belgio",          "BG": "Bulgaria",
    "CY": "Cipro",          "CZ": "Repubblica Ceca", "DE": "Germania",
    "DK": "Danimarca",      "EE": "Estonia",         "ES": "Spagna",
    "FI": "Finlandia",      "FR": "Francia",         "GR": "Grecia",
    "HR": "Croazia",        "HU": "Ungheria",        "IE": "Irlanda",
    "IT": "Italia",         "LT": "Lituania",        "LU": "Lussemburgo",
    "LV": "Lettonia",       "MT": "Malta",           "NL": "Paesi Bassi",
    "PL": "Polonia",        "PT": "Portogallo",      "RO": "Romania",
    "SE": "Svezia",         "SI": "Slovenia",        "SK": "Slovacchia",
    "GB": "Regno Unito",
}
ISO2_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE",
    "DE": "DEU", "DK": "DNK", "EE": "EST", "ES": "ESP", "FI": "FIN",
    "FR": "FRA", "GR": "GRC", "HR": "HRV", "HU": "HUN", "IE": "IRL",
    "IT": "ITA", "LT": "LTU", "LU": "LUX", "LV": "LVA", "MT": "MLT",
    "NL": "NLD", "PL": "POL", "PT": "PRT", "RO": "ROU", "SE": "SWE",
    "SI": "SVN", "SK": "SVK", "GB": "GBR",
}

# ── Le 16 categorie di impatto EF3.1 ─────────────────────────────────────────
IC_COLS = [
    "Ecotoxicity, freshwater impact",
    "Human toxicity, cancer impact",
    "Climate change impact",
    "Human toxicity, non-cancer impact",
    "Resource use, fossils impact",
    "Resource use, minerals and metals impact",
    "Water use impact",
    "Land use impact",
    "Eutrophication, freshwater impact",
    "EF-particulate Matter impact",
    "Photochemical ozone formation - human health impact",
    "Acidification impact",
    "Eutrophication, terrestrial impact",
    "Eutrophication marine impact",
    "Ozone depletion impact",
    "Ionising radiation, human health impact",
]
IC_SHORT = {
    "Ecotoxicity, freshwater impact":                          "Ecotox. acqua dolce",
    "Human toxicity, cancer impact":                           "Tossicità umana (canc.)",
    "Climate change impact":                                   "Cambiamento climatico",
    "Human toxicity, non-cancer impact":                       "Tossicità umana (non c.)",
    "Resource use, fossils impact":                            "Uso risorse fossili",
    "Resource use, minerals and metals impact":                "Uso risorse minerali",
    "Water use impact":                                        "Uso idrico",
    "Land use impact":                                         "Uso del suolo",
    "Eutrophication, freshwater impact":                       "Eutrof. acqua dolce",
    "EF-particulate Matter impact":                            "Particolato (PM)",
    "Photochemical ozone formation - human health impact":     "Ozono troposferico",
    "Acidification impact":                                    "Acidificazione",
    "Eutrophication, terrestrial impact":                      "Eutrof. terrestre",
    "Eutrophication marine impact":                            "Eutrof. marina",
    "Ozone depletion impact":                                  "Deplezione ozono",
    "Ionising radiation, human health impact":                 "Radiazioni ionizzanti",
}
IC_PALETTE = [
    "#2E86AB", "#E85933", "#25465D", "#F4A261", "#2A9D8F",
    "#E9C46A", "#8338EC", "#06D6A0", "#EF476F", "#118AB2",
    "#FFB703", "#780000", "#606C38", "#BC6C25", "#6A4C93", "#546E7A",
]
CATEGORY_PALETTE = {
    "Agricoltura & cereali":        "#FF0000",
    "Zootecnia & prodotti animali": "#FF6B00",
    "Pesca & acquacoltura":         "#FFD700",
    "Trasporti & veicoli":          "#8B008B",
    "Metalli & minerali":           "#00BFFF",
    "Plastica & polimeri":          "#0000FF",
    "Carta, legno & imballaggi":    "#008000",
    "Tessile & fibre":              "#8B4513",
    "Chimica & additivi":           "#FF00FF",
    "Elettronica & componenti":     "#808000",
    "Energia & utilities":          "#808080",
    "Gestione rifiuti & riciclo":   "#FF69B4",
    "Altro":                        "#000000",
}

# ── Tema grafici (coerente con la palette della dashboard ospite) ───────────
CHART_BG    = "#f4faff"
CHART_INNER = "#eaf4fc"
GRID_COLOR  = "#d6eaf6"
AXIS_COLOR  = "#a8cfe0"
TEXT_COLOR  = "#1a3a4f"

PLOTLY_LAYOUT = dict(
    plot_bgcolor  = CHART_INNER,
    paper_bgcolor = CHART_BG,
    font          = dict(color=TEXT_COLOR, size=13),
    xaxis         = dict(
        showgrid=False, zeroline=False, showline=True,
        linecolor=AXIS_COLOR, linewidth=1,
        tickfont=dict(size=12, color=TEXT_COLOR),
        title_font=dict(size=12, color=TEXT_COLOR),
    ),
    yaxis         = dict(
        showgrid=True, gridcolor=GRID_COLOR, gridwidth=1,
        zeroline=False, showline=False,
        tickfont=dict(size=12, color=TEXT_COLOR),
        title_font=dict(size=12, color=TEXT_COLOR),
    ),
    legend        = dict(
        orientation="v", yanchor="top", y=1, xanchor="left", x=1.01,
        font=dict(size=11, color=TEXT_COLOR),
        bgcolor="rgba(244,250,255,0.95)",
        bordercolor=AXIS_COLOR, borderwidth=1,
    ),
    hoverlabel    = dict(bgcolor="#1a3a4f", font_color="white", font_size=12),
    margin        = dict(t=20, b=50, l=65, r=180),
)


# ── Caricamento dati ─────────────────────────────────────────────────────────
def _find_file(*names, subfolders=("dati", "")) -> Path | None:
    for sub in subfolders:
        for name in names:
            p = (BASE_DIR / sub / name) if sub else (BASE_DIR / name)
            if p.is_file():
                return p
    return None


@st.cache_data(show_spinner=False)
def _load_scores():
    path = _find_file("Scores (PaesexAnno).xlsx", "Scores__PaesexAnno_.xlsx", "Scores_PaesexAnno.xlsx")
    if path is None:
        return None
    df = pd.read_excel(path)
    df["iso2"] = df["location"]
    df["location"] = df["iso2"].map(ISO_TO_NAME).fillna(df["iso2"])
    df["iso3"] = df["iso2"].map(ISO2_TO_ISO3)
    df["refYear"] = df["refYear"].astype(int)
    for col in IC_COLS:
        df[col + "_pct"] = df[col] / df["EF3.1"] * 100
    return df


@st.cache_data(show_spinner=False)
def _load_processi():
    path = _find_file("processi_normalizzati.csv")
    if path is None:
        return None
    return pd.read_csv(path)


def _dati_mancanti(nome_file: str):
    st.markdown(f"""
    <div class="insight-box">
        <strong>File dati non trovato:</strong> <code>{nome_file}</code><br>
        Copia il file nella cartella <code>caso_environment/dati/</code>.
    </div>
    """, unsafe_allow_html=True)


@st.cache_data(show_spinner="Carico la mappa…")
def _leggi_html(percorso: str, mtime: float) -> str:
    return Path(percorso).read_text(encoding="utf-8")


def _render_mappa():
    """Mappa Kepler.gl esportata come HTML ("EF3.1 data map.html"), incorporata nella scheda."""
    path = _find_file("EF3.1 data map.html", "EF3.1_data_map.html", subfolders=("", "dati", "mappe"))
    if path is None:
        st.markdown("""
        <div class="insight-box">
            <strong>Mappa non trovata:</strong> <code>EF3.1 data map.html</code><br>
            Copia il file nella cartella <code>caso_environment/</code>.
        </div>
        """, unsafe_allow_html=True)
        return
    components.html(_leggi_html(str(path), path.stat().st_mtime), height=MAPPA_ALTEZZA, scrolling=True)


# ── Entry point chiamato da cases.py ─────────────────────────────────────────
MAPPA_ALTEZZA = 750  # altezza in pixel della mappa Kepler


def render_caso(key_prefix: str):
    df = _load_scores()
    df_proc = _load_processi()

    tab_home, tab_serie, tab_cat, tab_proc, tab_mappa = st.tabs(
        ["Home", "Serie storica", "Categorie di impatto", "Processi produttivi", "Mappa"]
    )

    with tab_home:
        _render_home(df, df_proc)

    with tab_serie:
        if df is None:
            _dati_mancanti("Scores (PaesexAnno).xlsx")
        else:
            _render_serie(df, key_prefix)

    with tab_cat:
        if df is None:
            _dati_mancanti("Scores (PaesexAnno).xlsx")
        else:
            _render_categorie(df, key_prefix)

    with tab_proc:
        if df_proc is None:
            _dati_mancanti("processi_normalizzati.csv")
        else:
            _render_processi(df_proc, key_prefix)

    with tab_mappa:
        _render_mappa()


# ── HOME ──────────────────────────────────────────────────────────────────────
def _render_home(df, df_proc):
    st.markdown("""
    <div class="insight-box">
        <strong>Dataset utilizzati</strong><br><br>
        Per le sezioni <em>Serie storica</em> e <em>Categorie di impatto</em>
        è utilizzato il dataset <strong>Scores (PaesexAnno)</strong>, con l'indice composito
        EF3.1 e le 16 categorie di impatto già normalizzate e pesate secondo i pesi della
        Commissione Europea, per 28 paesi europei nel periodo 2015–2022.<br><br>
        Per la sezione <em>Processi produttivi</em> è utilizzato un dataset di processi con
        valori grezzi delle 16 categorie di impatto, normalizzati sulla media dei
        Normalisation Factors europei 2015–2022 (non disponendo di un anno di riferimento
        per ciascun processo).
    </div>
    """, unsafe_allow_html=True)

    if df is not None:
        n_paesi = df["location"].nunique()
        anni = f'{df["refYear"].min()}–{df["refYear"].max()}'
        media_ef = df["EF3.1"].mean()
        n_processi = df_proc.shape[0] if df_proc is not None else "—"

        c1, c2, c3, c4 = st.columns(4)
        for col, (label, value, color) in zip(
            [c1, c2, c3, c4],
            [
                ("Paesi analizzati", str(n_paesi), "#25465D"),
                ("Periodo", anni, "#2E86AB"),
                ("EF3.1 medio UE", f"{media_ef:.3f}", "#008000"),
                ("Processi mappati", str(n_processi), "#E85933"),
            ],
        ):
            with col:
                st.markdown(f"""
                <div class="kpi-card" style="border-left-color:{color};">
                    <div class="top-bar" style="background:{color};opacity:0.7;"></div>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value" style="color:{color};">{value}</div>
                    <div class="kpi-sub"></div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <p class="section-label">Navigazione</p>
    <p class="section-title">Le quattro sezioni</p>
    <div class="insight-box">
        <strong>Serie storica</strong> — andamento dell'indice EF3.1 nel tempo, con mediana
        europea di riferimento e profilo delle 16 categorie di impatto.<br><br>
        <strong>Categorie di impatto</strong> — composizione percentuale dell'indice per
        paese (barre impilate) e confronto radar tra fino a 5 paesi.<br><br>
        <strong>Processi produttivi</strong> — scatter plot degli impatti per processo
        produttivo, con assi selezionabili tra le 16 categorie e colorazione per categoria
        merceologica.
    </div>
    """, unsafe_allow_html=True)


# ── SERIE STORICA ─────────────────────────────────────────────────────────────
def _render_serie(df, key_prefix):
    st.markdown("""
    <p class="section-label">Sezione 2</p>
    <p class="section-title">Serie storica dell'indice EF3.1</p>
    """, unsafe_allow_html=True)

    all_countries = sorted(df["location"].unique().tolist())
    default_paesi = [p for p in ["Italia", "Germania", "Francia", "Spagna", "Grecia"] if p in all_countries]

    paesi_sel = st.multiselect(
        "Paesi", options=all_countries, default=default_paesi,
        placeholder="Seleziona paesi…", key=f"{key_prefix}_serie_paesi",
    )
    if not paesi_sel:
        st.info("Seleziona almeno un paese.")
        return

    df_sel = df[df["location"].isin(paesi_sel)].copy()
    palette = IC_PALETTE
    country_colors = {c: palette[i % len(palette)] for i, c in enumerate(sorted(paesi_sel))}

    # Grafico A — serie storica EF3.1 + mediana europea
    fig1 = go.Figure()
    for paese in sorted(paesi_sel):
        dfp = df_sel[df_sel["location"] == paese].sort_values("refYear")
        fig1.add_trace(go.Scatter(
            x=dfp["refYear"], y=dfp["EF3.1"], mode="lines+markers", name=paese,
            line=dict(color=country_colors[paese], width=1.8), marker=dict(size=4),
            hovertemplate=f"<b>{paese}</b><br>Anno: %{{x}}<br>EF3.1: %{{y:.4f}}<extra></extra>",
        ))
    df_median = df.groupby("refYear")["EF3.1"].median().reset_index()
    fig1.add_trace(go.Scatter(
        x=df_median["refYear"], y=df_median["EF3.1"], mode="lines", name="mediana UE",
        line=dict(color="#2D6A2D", width=2.5, dash="dash"),
        hovertemplate="<b>Mediana UE</b><br>Anno: %{x}<br>EF3.1: %{y:.4f}<extra></extra>",
    ))
    layout1 = dict(PLOTLY_LAYOUT)
    layout1.update(height=460, hovermode="x unified",
                    yaxis=dict(**PLOTLY_LAYOUT["yaxis"], title="EF3.1 Score", tickformat=".2f"))
    fig1.update_layout(**layout1)
    st.plotly_chart(fig1, use_container_width=True, key=f"{key_prefix}_serie_fig1")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Grafico B — rilevanza percentuale di una categoria di impatto selezionabile
    ic_options = [IC_SHORT[c] for c in IC_COLS]
    ic_reverse = {v: k for k, v in IC_SHORT.items()}
    ic_scelta_short = st.selectbox(
        "Categoria di impatto", options=ic_options,
        index=ic_options.index("Cambiamento climatico"),
        key=f"{key_prefix}_serie_ic",
    )
    ic_scelta = ic_reverse[ic_scelta_short]
    pct_col = ic_scelta + "_pct"

    fig2 = go.Figure()
    for paese in sorted(paesi_sel):
        dfp = df_sel[df_sel["location"] == paese].sort_values("refYear")
        fig2.add_trace(go.Scatter(
            x=dfp["refYear"], y=dfp[pct_col], mode="lines", name=paese,
            line=dict(color=country_colors[paese], width=1.8),
            hovertemplate=f"<b>{paese}</b><br>Anno: %{{x}}<br>{ic_scelta_short}: %{{y:.1f}}%<extra></extra>",
        ))
    layout2 = dict(PLOTLY_LAYOUT)
    layout2.update(height=440, hovermode="x unified",
                    yaxis=dict(**PLOTLY_LAYOUT["yaxis"], title="% su EF3.1", ticksuffix="%"))
    fig2.update_layout(**layout2)
    st.plotly_chart(fig2, use_container_width=True, key=f"{key_prefix}_serie_fig2")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Grafico C — profilo delle 16 categorie per un singolo paese
    paese_singolo = st.selectbox(
        "Profilo paese singolo (tutte le 16 categorie)", options=all_countries,
        index=all_countries.index("Italia") if "Italia" in all_countries else 0,
        key=f"{key_prefix}_serie_paese_singolo",
    )
    df_paese = df[df["location"] == paese_singolo].sort_values("refYear")
    fig3 = go.Figure()
    for i, col in enumerate(IC_COLS):
        fig3.add_trace(go.Scatter(
            x=df_paese["refYear"], y=df_paese[col + "_pct"], mode="lines", name=IC_SHORT[col],
            line=dict(color=IC_PALETTE[i], width=1.6),
            hovertemplate=f"<b>{IC_SHORT[col]}</b><br>Anno: %{{x}}<br>%{{y:.1f}}%<extra></extra>",
        ))
    layout3 = dict(PLOTLY_LAYOUT)
    layout3.update(height=460, hovermode="x unified",
                    legend=dict(**{**PLOTLY_LAYOUT["legend"], "font": dict(size=10, color=TEXT_COLOR)}),
                    yaxis=dict(**PLOTLY_LAYOUT["yaxis"], title="% su EF3.1", ticksuffix="%"))
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True, key=f"{key_prefix}_serie_fig3")


# ── CATEGORIE DI IMPATTO ──────────────────────────────────────────────────────
def _render_categorie(df, key_prefix):
    st.markdown("""
    <p class="section-label">Sezione 3</p>
    <p class="section-title">Categorie di impatto</p>
    """, unsafe_allow_html=True)

    all_countries = sorted(df["location"].unique().tolist())
    anni_disponibili = sorted(df["refYear"].unique().tolist())

    c_anno, c_paesi = st.columns([1, 3])
    with c_anno:
        anno_sel = st.selectbox(
            "Anno", options=anni_disponibili, index=len(anni_disponibili) - 1,
            key=f"{key_prefix}_cat_anno",
        )
    with c_paesi:
        paesi_bar = st.multiselect(
            "Paesi (barre impilate)", options=all_countries, default=all_countries[:10],
            placeholder="Seleziona paesi…", key=f"{key_prefix}_cat_paesi_bar",
        )

    df_anno = df[df["refYear"] == anno_sel].copy()

    if not paesi_bar:
        st.info("Seleziona almeno un paese per le barre impilate.")
    else:
        df_bar = df_anno[df_anno["location"].isin(paesi_bar)].set_index("location")
        fig_bar = go.Figure()
        for i, col in enumerate(IC_COLS):
            fig_bar.add_trace(go.Bar(
                name=IC_SHORT[col], x=df_bar.index.tolist(), y=df_bar[col + "_pct"].tolist(),
                marker_color=IC_PALETTE[i],
                hovertemplate=f"<b>{IC_SHORT[col]}</b><br>Paese: %{{x}}<br>Rilevanza: %{{y:.1f}}%<extra></extra>",
            ))
        layout_bar = dict(PLOTLY_LAYOUT)
        layout_bar.update(
            barmode="stack", height=460,
            xaxis=dict(**PLOTLY_LAYOUT["xaxis"], title=None, tickangle=-30),
            yaxis=dict(**PLOTLY_LAYOUT["yaxis"], title="Rilevanza % sul totale EF3.1", range=[0, 100], ticksuffix="%"),
            legend=dict(**{**PLOTLY_LAYOUT["legend"], "font": dict(size=10, color=TEXT_COLOR)}),
            margin=dict(t=20, b=80, l=65, r=200),
        )
        fig_bar.update_layout(**layout_bar)
        st.plotly_chart(fig_bar, use_container_width=True, key=f"{key_prefix}_cat_fig_bar")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    paesi_radar = st.multiselect(
        "Paesi (radar, max 5)", options=all_countries,
        default=[p for p in ["Italia", "Germania", "Francia", "Spagna", "Grecia"] if p in all_countries],
        max_selections=5, placeholder="Seleziona fino a 5 paesi…", key=f"{key_prefix}_cat_paesi_radar",
    )

    if not paesi_radar:
        st.info("Seleziona almeno un paese per il radar.")
        return

    def _hex_to_rgba(hex_color, alpha=0.12):
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    radar_colors = ["#2E86AB", "#FF0000", "#008000", "#FFB703", "#8338EC"]
    fig_radar = go.Figure()
    for i, paese in enumerate(paesi_radar):
        row = df_anno[df_anno["location"] == paese]
        if row.empty:
            continue
        vals = [float(row[c + "_pct"].iloc[0]) for c in IC_COLS]
        labels = [IC_SHORT[c] for c in IC_COLS]
        vals_closed, labels_closed = vals + [vals[0]], labels + [labels[0]]
        color = radar_colors[i % len(radar_colors)]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals_closed, theta=labels_closed, fill="toself",
            fillcolor=_hex_to_rgba(color), line=dict(color=color, width=2), name=paese,
            hovertemplate="<b>%{theta}</b><br>%{r:.1f}%<extra></extra>",
        ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor=CHART_INNER,
            radialaxis=dict(visible=True, ticksuffix="%", tickfont=dict(size=9, color=TEXT_COLOR),
                             gridcolor=AXIS_COLOR, linecolor=AXIS_COLOR),
            angularaxis=dict(tickfont=dict(size=9, color=TEXT_COLOR), linecolor=AXIS_COLOR, gridcolor=AXIS_COLOR),
        ),
        paper_bgcolor=CHART_BG,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5,
                    font=dict(size=11, color=TEXT_COLOR)),
        margin=dict(t=40, b=80, l=80, r=80), height=520,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key=f"{key_prefix}_cat_fig_radar")


# ── PROCESSI PRODUTTIVI ───────────────────────────────────────────────────────
def _render_processi(df_proc, key_prefix):
    st.markdown("""
    <p class="section-label">Sezione 4</p>
    <p class="section-title">Processi produttivi</p>
    """, unsafe_allow_html=True)

    all_categories = sorted(df_proc["categoria"].dropna().unique().tolist())
    ic_options = [IC_SHORT[c] for c in IC_COLS]
    ic_reverse = {v: k for k, v in IC_SHORT.items()}

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        asse_x_short = st.selectbox("Asse X", options=ic_options,
                                     index=ic_options.index("Cambiamento climatico"),
                                     key=f"{key_prefix}_proc_x")
    with c2:
        asse_y_short = st.selectbox("Asse Y", options=ic_options,
                                     index=ic_options.index("Uso risorse fossili"),
                                     key=f"{key_prefix}_proc_y")
    with c3:
        cat_sel = st.multiselect("Categorie merceologiche", options=all_categories,
                                  default=all_categories, placeholder="Seleziona categorie…",
                                  key=f"{key_prefix}_proc_cat")

    if not cat_sel:
        st.info("Seleziona almeno una categoria merceologica.")
        return

    asse_x, asse_y = ic_reverse[asse_x_short], ic_reverse[asse_y_short]
    df_sel = df_proc[df_proc["categoria"].isin(cat_sel)].copy()

    fig = go.Figure()
    for cat in sorted(cat_sel):
        df_cat = df_sel[df_sel["categoria"] == cat]
        color = CATEGORY_PALETTE.get(cat, "#aaaaaa")
        fig.add_trace(go.Scatter(
            x=df_cat[asse_x], y=df_cat[asse_y], mode="markers", name=cat,
            marker=dict(color=color, size=7, opacity=0.75, line=dict(width=0.5, color="white")),
            text=df_cat["nome_processo"],
            hovertemplate=f"<b>%{{text}}</b><br>{asse_x_short}: %{{x:.4f}}<br>{asse_y_short}: %{{y:.4f}}<extra></extra>",
        ))
    layout = dict(PLOTLY_LAYOUT)
    layout.update(
        height=580,
        xaxis=dict(**{**PLOTLY_LAYOUT["xaxis"], "title": asse_x_short, "zeroline": True, "zerolinecolor": AXIS_COLOR}),
        yaxis=dict(**{**PLOTLY_LAYOUT["yaxis"], "title": asse_y_short, "zeroline": True, "zerolinecolor": AXIS_COLOR}),
        margin=dict(t=20, b=60, l=70, r=200),
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_proc_fig")

    st.markdown("""
    <div class="insight-box">
        <strong>Lettura del grafico</strong><br>
        Ogni punto rappresenta un processo produttivo. Gli assi sono selezionabili tra le 16
        categorie di impatto normalizzate secondo i Normalisation Factors europei (EF 3.1).
        Il colore identifica la categoria merceologica del processo.
    </div>
    """, unsafe_allow_html=True)