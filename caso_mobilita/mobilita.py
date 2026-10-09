"""
Caso studio: Analisi dei flussi di mobilità territoriale e attrattività
culturale in Italia.

"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Percorso dati ────────────────────────────────────────────────────────────
FILE_DATI = Path(__file__).parent / "dati" / "comuni_kpi_finale_reti.csv"

# ── Da shared.py: regioni, ripartizioni, colori, tema grafici ───────────────
REGIONI = {
    1: "Piemonte", 2: "Valle d'Aosta", 3: "Lombardia",
    4: "Trentino-Alto Adige", 5: "Veneto", 6: "Friuli-Venezia Giulia",
    7: "Liguria", 8: "Emilia-Romagna", 9: "Toscana", 10: "Umbria",
    11: "Marche", 12: "Lazio", 13: "Abruzzo", 14: "Molise",
    15: "Campania", 16: "Puglia", 17: "Basilicata", 18: "Calabria",
    19: "Sicilia", 20: "Sardegna",
}
RIPARTIZIONI = {
    1: "Nord-Ovest", 2: "Nord-Ovest", 3: "Nord-Ovest", 7: "Nord-Ovest",
    4: "Nord-Est", 5: "Nord-Est", 6: "Nord-Est", 8: "Nord-Est",
    9: "Centro", 10: "Centro", 11: "Centro", 12: "Centro",
    13: "Sud", 14: "Sud", 15: "Sud", 16: "Sud", 17: "Sud", 18: "Sud",
    19: "Isole", 20: "Isole",
}
COLORI = {"attrattore": "#051186", "emettitore": "#00880D", "equilibrato": "#C1C1C1"}

CHART_BG    = "#f4faff"
CHART_INNER = "#eaf4fc"
GRID_COLOR  = "#d6eaf6"
AXIS_COLOR  = "#a8cfe0"
TEXT_COLOR  = "#1a3a4f"
CHART_FONT  = "Plus Jakarta Sans"

PLOTLY_LAYOUT = dict(
    plot_bgcolor=CHART_INNER, paper_bgcolor=CHART_BG,
    font=dict(family=CHART_FONT, color=TEXT_COLOR, size=13),
    xaxis=dict(showgrid=False, zeroline=False, showline=True, linecolor=AXIS_COLOR, linewidth=1,
               tickfont=dict(size=12, color=TEXT_COLOR), title_font=dict(size=12, color=TEXT_COLOR)),
    yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, gridwidth=1, zeroline=False, showline=False,
               tickfont=dict(size=12, color=TEXT_COLOR), title_font=dict(size=12, color=TEXT_COLOR)),
    legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="left", x=0,
                font=dict(size=12, color=TEXT_COLOR), bgcolor="rgba(244,250,255,0.9)",
                bordercolor=AXIS_COLOR, borderwidth=1),
    hoverlabel=dict(bgcolor=TEXT_COLOR, font_color="white", font_family=CHART_FONT, font_size=12,
                     bordercolor=TEXT_COLOR),
    margin=dict(t=30, b=40, l=55, r=20),
)


@st.cache_data(show_spinner="Carico i dati dei comuni…")
def carica_dati() -> pd.DataFrame | None:
    if not FILE_DATI.is_file():
        return None
    df = pd.read_csv(FILE_DATI, encoding="utf-8-sig", dtype={"Procom": str})
    df["nome_regione"] = df["COD_REG"].map(REGIONI)
    df["ripartizione"] = df["COD_REG"].map(RIPARTIZIONI)
    df["COMUNE"] = df["COMUNE"].fillna("N/D")
    return df


def _layout(**override) -> dict:
    """Copia di PLOTLY_LAYOUT (da shared.py); **override la personalizza senza toccare l'originale."""
    import copy
    base = copy.deepcopy(PLOTLY_LAYOUT)
    base.update(override)
    return base


def _kpi_row(voci):
    """voci: lista di (colore, etichetta, valore, sottotitolo)."""
    colonne = st.columns(len(voci))
    for col, (colore, label, val, sub) in zip(colonne, voci):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color:{colore}; min-height:130px; height:130px;">
                <div class="top-bar" style="background:{colore};"></div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="color:{colore}; font-size:1.5rem;">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)


def _divider():
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


def _label(testo: str):
    st.markdown(f'<div class="section-label">{testo}</div>', unsafe_allow_html=True)


def _titolo(testo: str):
    st.markdown(f'<div class="section-title" style="font-size:1.1rem;">{testo}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — PANORAMICA NAZIONALE  (da 1_panoramica.py)
# ══════════════════════════════════════════════════════════════════════════
def _tab_panoramica(df: pd.DataFrame, key: str):
    classificazione_sel = st.multiselect("Classificazione",
        ["attrattore", "emettitore", "equilibrato"],
        default=["attrattore", "emettitore", "equilibrato"], key=f"{key}_pan_cls")
    c1, c2 = st.columns(2)
    with c1:
        ripartizione_sel = st.selectbox("Ripartizione geografica",
            ["Tutta Italia", "Nord-Ovest", "Nord-Est", "Centro", "Sud", "Isole"],
            key=f"{key}_pan_rip")
    with c2:
        min_pop = st.slider("Popolazione minima", 0, 100_000, 0, step=1000,
                             format="%d ab.", key=f"{key}_pan_pop")

    dff = df.copy()
    if ripartizione_sel != "Tutta Italia":
        dff = dff[dff["ripartizione"] == ripartizione_sel]
    if classificazione_sel:
        dff = dff[dff["classificazione"].isin(classificazione_sel)]
    dff = dff[dff["POP21"] >= min_pop]

    if dff.empty:
        st.warning("Nessun comune corrisponde ai filtri selezionati.")
        return

    n_attr, n_emit, n_equi = ((dff["classificazione"] == c).sum() for c in ("attrattore", "emettitore", "equilibrato"))
    n_tot = max(len(dff), 1)

    _kpi_row([
        ("#051186", "Comuni attrattori",  f"{n_attr:,}", f"{n_attr/n_tot*100:.1f}% del totale"),
        ("#00880D", "Comuni emettitori",  f"{n_emit:,}", f"{n_emit/n_tot*100:.1f}% del totale"),
        ("#C1C1C1", "Comuni equilibrati", f"{n_equi:,}", f"{n_equi/n_tot*100:.1f}% del totale"),
        ("#00649C", "Pendolari totali",   f"{dff['entrate'].sum()/1e6:.1f}M", "flussi in entrata aggregati"),
        ("#4FC3F7", "Ind. attrattività",  f"{dff['indice_attrattivita'].mean():.3f}", f"max {dff['indice_attrattivita'].max():.2f}"),
        ("#10a870", "Poli culturali",     f"{dff['n_poli_totali'].sum():,}", f"in {(dff['n_poli_totali']>0).sum():,} comuni"),
    ])
    _divider()

    c1, c2, c3 = st.columns([1.2, 1.5, 2])
    with c1:
        _label("COMPOSIZIONE")
        counts = dff["classificazione"].value_counts()
        fig = go.Figure(go.Pie(
            labels=counts.index.tolist(), values=counts.values.tolist(), hole=0.6,
            marker=dict(colors=[COLORI.get(l, "#888") for l in counts.index], line=dict(color=CHART_BG, width=2)),
            textinfo="none", hovertemplate="<b>%{label}</b><br>%{value:,} comuni (%{percent})<extra></extra>",
        ))
        fig.update_layout(**_layout(
            showlegend=True, legend=dict(orientation="h", x=0, y=-0.15, font=dict(size=10, color=TEXT_COLOR)),
            height=260, margin=dict(t=20, b=50, l=10, r=10),
            annotations=[dict(text=f"<b>{n_tot:,}</b><br><span style='font-size:10px'>comuni</span>",
                               x=0.5, y=0.5, font=dict(size=12, color=TEXT_COLOR), showarrow=False)],
        ))
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_pan_donut")

    with c2:
        _label("DISTRIBUZIONE SALDO NETTO")
        dh = dff.copy()
        dh["saldo_log"] = np.sign(dh["saldo_netto"]) * np.log10(np.abs(dh["saldo_netto"]) + 1)
        fig = px.histogram(dh, x="saldo_log", color="classificazione", color_discrete_map=COLORI,
                            nbins=80, labels={"saldo_log": "Saldo netto (log simmetrico)"}, height=260)
        fig.update_layout(**_layout(showlegend=False, bargap=0.05, margin=dict(t=10, b=40, l=40, r=20)))
        fig.add_vline(x=0, line_dash="dash", line_color="#051186", line_width=1.5)
        tv = [-100000, -10000, -1000, -100, 0, 100, 1000, 10000, 100000]
        fig.update_xaxes(tickvals=[np.sign(v) * np.log10(abs(v) + 1) for v in tv],
                          ticktext=["-100k", "-10k", "-1k", "-100", "0", "100", "1k", "10k", "100k"],
                          title_text="Saldo netto")
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_pan_hist")

    with c3:
        _label("ATTRATTIVITÀ VS POPOLAZIONE")
        ds = dff[dff["POP21"] > 500].copy()
        ds["_size"] = ds["n_poli_totali"].clip(lower=1)
        fig = px.scatter(ds, x="POP21", y="indice_attrattivita", color="classificazione",
                          color_discrete_map=COLORI, size="_size", size_max=25, hover_name="COMUNE",
                          log_x=True, labels={"POP21": "Popolazione (scala log)", "indice_attrattivita": "Indice attrattività"},
                          height=260)
        fig.update_layout(**_layout(showlegend=False, margin=dict(t=10, b=40, l=50, r=20)))
        fig.add_hline(y=1, line_dash="dash", line_color="#C1C1C1", line_width=1)
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_pan_scatter")

    _divider()
    _label("ANALISI PER REGIONE")
    _titolo("Struttura territoriale delle regioni italiane")

    reg = dff.groupby("nome_regione").agg(
        attrattori=("classificazione", lambda x: (x == "attrattore").sum()),
        emettitori=("classificazione", lambda x: (x == "emettitore").sum()),
        equilibrati=("classificazione", lambda x: (x == "equilibrato").sum()),
        tot_comuni=("Procom", "count"), poli=("n_poli_totali", "sum"),
        ind_attr=("indice_attrattivita", "mean"),
    ).reset_index()
    reg["pct_attrattori"] = (reg["attrattori"] / reg["tot_comuni"] * 100).round(1)

    cr1, cr2 = st.columns(2)
    with cr1:
        rs = reg.sort_values("tot_comuni")
        fig = go.Figure()
        for campo, nome, colore in [("attrattori", "Attrattori", "#051186"),
                                     ("emettitori", "Emettitori", "#00880D"),
                                     ("equilibrati", "Equilibrati", "#C1C1C1")]:
            fig.add_trace(go.Bar(y=rs["nome_regione"], x=rs[campo], name=nome, orientation="h", marker_color=colore))
        fig.update_layout(**_layout(barmode="group", height=560, bargap=0.15, bargroupgap=0.05,
                                     margin=dict(t=50, b=30, l=150, r=20),
                                     legend=dict(orientation="h", y=1.04, x=0, font=dict(size=12, color=TEXT_COLOR)),
                                     xaxis=dict(title="N. comuni", gridcolor=GRID_COLOR, tickfont=dict(color=TEXT_COLOR))))
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_pan_regbar")

    with cr2:
        fig = px.scatter(reg, x="pct_attrattori", y="poli", size="tot_comuni", color="ind_attr",
                          hover_name="nome_regione", color_continuous_scale=["#b3dff5", "#051186"], size_max=40,
                          labels={"pct_attrattori": "% Comuni attrattori", "poli": "N. Poli culturali", "ind_attr": "Ind. attr. medio"},
                          height=560)
        fig.update_layout(**_layout(margin=dict(t=10, b=40, l=50, r=10)))
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_pan_bubble")

    _divider()
    _label("CLASSIFICHE")
    _titolo("Top comuni per indicatore")
    indicatore = st.radio("Ordina per", ["Saldo netto assoluto", "Indice attrattività", "Poli culturali", "Intensità culturale"],
                           key=f"{key}_pan_top", horizontal=True)
    if indicatore == "Saldo netto assoluto":
        top = dff[dff["classificazione"] == "attrattore"].sort_values("saldo_netto", ascending=False).head(20)
        cols, nomi = ["COMUNE", "nome_regione", "POP21", "saldo_netto", "entrate", "uscite", "n_poli_totali"], \
                     ["Comune", "Regione", "Popolazione", "Saldo netto", "Entrate", "Uscite", "Poli culturali"]
    elif indicatore == "Indice attrattività":
        top = dff[dff["classificazione"] == "attrattore"].sort_values("indice_attrattivita", ascending=False).head(20)
        cols, nomi = ["COMUNE", "nome_regione", "indice_attrattivita", "entrate", "POP21", "n_poli_totali"], \
                     ["Comune", "Regione", "Ind. attrattività", "Entrate", "Popolazione", "Poli culturali"]
    elif indicatore == "Poli culturali":
        top = dff[dff["n_poli_totali"] > 0].sort_values("n_poli_totali", ascending=False).head(20)
        cols, nomi = ["COMUNE", "nome_regione", "n_poli_totali", "POP21", "saldo_netto", "classificazione"], \
                     ["Comune", "Regione", "Poli culturali", "Popolazione", "Saldo netto", "Classificazione"]
    else:
        top = dff[dff["uscite"] >= 200].sort_values("intensita_culturale", ascending=False).head(20)
        cols, nomi = ["COMUNE", "nome_regione", "intensita_culturale", "flussi_verso_cultura", "n_destinazioni_culturali", "classificazione"], \
                     ["Comune", "Regione", "Intensità culturale", "Flussi verso cultura", "Destinazioni culturali", "Classificazione"]
    t = top[cols].reset_index(drop=True); t.index += 1; t.columns = nomi
    st.dataframe(t, use_container_width=True, height=420)


# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — ANALISI TERRITORIALE  (da 2_territoriale.py)
# ══════════════════════════════════════════════════════════════════════════
CITTA_METRO = {"015": "Milano", "058": "Roma", "063": "Napoli", "001": "Torino",
               "007": "Genova", "037": "Bologna", "048": "Firenze", "072": "Bari",
               "087": "Catania", "082": "Palermo", "027": "Venezia", "023": "Verona"}
CAPOLUOGHI = {"015146": "Milano", "058091": "Roma", "063049": "Napoli", "001272": "Torino",
              "007024": "Genova", "037006": "Bologna", "048017": "Firenze", "072006": "Bari",
              "087015": "Catania", "082053": "Palermo", "027042": "Venezia", "023036": "Verona"}
PALETTE_METRO = ["#051186", "#4FC3F7", "#00649C", "#10a870", "#00880D",
                 "#7B5EA7", "#F2A65A", "#3AAFA9", "#D62828", "#F7B731", "#2E86AB", "#A23B72"]


def _tab_territoriale(df: pd.DataFrame, key: str):
    df = df.copy()
    df["cod_prov"] = df["Procom"].str[:3]
    df["citta_metro"] = df["cod_prov"].map(CITTA_METRO)
    df["e_capoluogo"] = df["Procom"].isin(CAPOLUOGHI.keys())

    scala = st.radio("Scala di analisi", ["Regionale", "Città metropolitane", "Confronto ripartizioni"],
                      key=f"{key}_terr_scala", horizontal=True)

    # ── Regionale ─────────────────────────────────────────────────────────
    if scala == "Regionale":
        regione_sel = st.selectbox("Seleziona regione", sorted(df["nome_regione"].dropna().unique()),
                                    key=f"{key}_terr_reg")
        dff = df[df["nome_regione"] == regione_sel].copy()
        n_attr, n_emit, n_equi = ((dff["classificazione"] == c).sum() for c in ("attrattore", "emettitore", "equilibrato"))
        n_tot = max(len(dff), 1)
        _kpi_row([
            ("#051186", "Attrattori",  f"{n_attr}", f"{n_attr/n_tot*100:.0f}% dei comuni"),
            ("#00880D", "Emettitori",  f"{n_emit}", f"{n_emit/n_tot*100:.0f}% dei comuni"),
            ("#C1C1C1", "Equilibrati", f"{n_equi}", f"{n_equi/n_tot*100:.0f}% dei comuni"),
            ("#00649C", "Poli culturali", f"{dff['n_poli_totali'].sum():,}", f"in {(dff['n_poli_totali']>0).sum()} comuni"),
            ("#4FC3F7", "Ind. attr. medio", f"{dff['indice_attrattivita'].mean():.3f}", f"max {dff['indice_attrattivita'].max():.3f}"),
        ])
        _divider()
        c1, c2 = st.columns([3, 2])
        with c1:
            combinato = pd.concat([dff.nlargest(15, "saldo_netto"), dff.nsmallest(15, "saldo_netto")]).sort_values("saldo_netto")
            fig = px.bar(combinato, x="saldo_netto", y="COMUNE", color="classificazione", color_discrete_map=COLORI,
                         orientation="h", height=500, labels={"saldo_netto": "Saldo netto", "COMUNE": ""})
            fig.update_layout(**_layout(showlegend=False, margin=dict(t=10, b=30, l=10, r=20)))
            fig.add_vline(x=0, line_color="#051186", line_width=1)
            st.plotly_chart(fig, use_container_width=True, key=f"{key}_terr_bar")
        with c2:
            fig = px.scatter(dff[dff["POP21"] > 200], x="POP21", y="saldo_netto", color="classificazione",
                              color_discrete_map=COLORI, size="n_poli_totali", size_max=30, hover_name="COMUNE",
                              labels={"POP21": "Popolazione", "saldo_netto": "Saldo netto"}, height=240)
            fig.update_layout(**_layout(showlegend=False, margin=dict(t=10, b=40, l=50, r=10)))
            fig.add_hline(y=0, line_dash="dash", line_color="#051186", line_width=1)
            st.plotly_chart(fig, use_container_width=True, key=f"{key}_terr_scatter")

            tip = pd.DataFrame({
                "Tipologia": ["Musei", "Teatri", "Biblioteche", "Siti arch.", "Monumenti", "Gallerie"],
                "N.": [dff["n_musei"].sum(), dff["n_teatri"].sum(), dff["n_biblioteche"].sum(),
                       dff["n_siti_arch"].sum(), dff["n_monumenti"].sum(), dff["n_gallerie"].sum()],
            }).sort_values("N.")
            fig = px.bar(tip, x="N.", y="Tipologia", orientation="h", color="N.",
                         color_continuous_scale=["#b3dff5", "#051186"], height=240)
            fig.update_layout(**_layout(showlegend=False, coloraxis_showscale=False, margin=dict(t=5, b=30, l=10, r=10)))
            st.plotly_chart(fig, use_container_width=True, key=f"{key}_terr_tip")

    # ── Città metropolitane ──────────────────────────────────────────────
    elif scala == "Città metropolitane":
        metro_sel = st.multiselect("Città metropolitane", list(CITTA_METRO.values()),
                                    default=["Milano", "Roma", "Napoli", "Torino", "Firenze"], key=f"{key}_terr_metro")
        if not metro_sel:
            st.info("Seleziona almeno una città metropolitana.")
            return
        dff = df[df["citta_metro"].isin(metro_sel)].copy()
        metro = dff.groupby("citta_metro").agg(
            n_comuni=("Procom", "count"),
            attrattori=("classificazione", lambda x: (x == "attrattore").sum()),
            emettitori=("classificazione", lambda x: (x == "emettitore").sum()),
            saldo_totale=("saldo_netto", "sum"), ind_attr_medio=("indice_attrattivita", "mean"),
            poli_totali=("n_poli_totali", "sum"), int_cult_media=("intensita_culturale", "mean"),
            pop_totale=("POP21", "sum"),
        ).reset_index()
        metro["pct_attrattori"] = (metro["attrattori"] / metro["n_comuni"] * 100).round(1)

        try:
            from sklearn.preprocessing import MinMaxScaler
            dims = ["attrattori", "poli_totali", "ind_attr_medio", "int_cult_media", "saldo_totale"]
            labels_radar = ["Attrattori", "Poli culturali", "Ind. attrattività", "Intensità culturale", "Saldo netto"]
            norm = metro.copy()
            norm[dims] = MinMaxScaler().fit_transform(metro[dims])
            fig = go.Figure()
            for i, row in norm.iterrows():
                vals = [row[d] for d in dims] + [row[dims[0]]]
                fig.add_trace(go.Scatterpolar(r=vals, theta=labels_radar + [labels_radar[0]], fill="toself",
                                               name=row["citta_metro"], line_color=PALETTE_METRO[i % len(PALETTE_METRO)], opacity=0.8))
            fig.update_layout(
                polar=dict(bgcolor="#eaf4fc", radialaxis=dict(visible=True, range=[0, 1], gridcolor=AXIS_COLOR,
                                                                tickfont=dict(color=TEXT_COLOR, size=11)),
                           angularaxis=dict(gridcolor=AXIS_COLOR, tickfont=dict(color=TEXT_COLOR, size=12))),
                paper_bgcolor=CHART_BG, font=dict(family=CHART_FONT, color=TEXT_COLOR),
                showlegend=True, height=430, margin=dict(t=30, b=30, l=60, r=60),
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{key}_terr_radar")
        except ImportError:
            st.info("Installa scikit-learn per il radar chart: pip install scikit-learn")

        _divider()
        c1, c2 = st.columns(2)
        with c1:
            ruolo = dff.copy()
            ruolo["ruolo"] = ruolo.apply(lambda r: "Capoluogo" if r["e_capoluogo"] else r["classificazione"].capitalize(), axis=1)
            mr = ruolo.groupby(["citta_metro", "ruolo"]).size().reset_index(name="n_comuni")
            ordine = metro.sort_values("saldo_totale", ascending=False)["citta_metro"].tolist()
            mr["citta_metro"] = pd.Categorical(mr["citta_metro"], categories=ordine, ordered=True)
            mr = mr.sort_values("citta_metro")
            fig = px.bar(mr, x="citta_metro", y="n_comuni", color="ruolo", barmode="stack",
                         color_discrete_map={"Capoluogo": "#c9a84c", "Attrattore": "#051186",
                                              "Emettitore": "#00880D", "Equilibrato": "#4FC3F7"},
                         labels={"citta_metro": "", "n_comuni": "N. comuni", "ruolo": ""}, height=320)
            fig.update_layout(**_layout(margin=dict(t=10, b=60, l=40, r=10)))
            st.plotly_chart(fig, use_container_width=True, key=f"{key}_terr_ruolo")
        with c2:
            fig = px.scatter(metro, x="saldo_totale", y="poli_totali", text="citta_metro", size="pop_totale",
                              size_max=40, color="ind_attr_medio", color_continuous_scale=["#b3dff5", "#051186"],
                              labels={"saldo_totale": "Saldo netto totale", "poli_totali": "N. poli culturali"}, height=300)
            fig.update_layout(**_layout(margin=dict(t=10, b=40, l=50, r=10)))
            fig.update_traces(textposition="top center", textfont=dict(size=10, color=TEXT_COLOR))
            st.plotly_chart(fig, use_container_width=True, key=f"{key}_terr_metroscatter")

        disp = metro[["citta_metro", "n_comuni", "attrattori", "emettitori", "pct_attrattori",
                       "poli_totali", "ind_attr_medio", "int_cult_media", "saldo_totale"]].copy()
        disp.columns = ["Città", "N. comuni", "Attrattori", "Emettitori", "% attrattori",
                         "Poli culturali", "Ind. attr. medio", "Int. culturale media", "Saldo netto totale"]
        disp["Ind. attr. medio"] = disp["Ind. attr. medio"].round(3)
        disp["Int. culturale media"] = disp["Int. culturale media"].round(3)
        disp["% attrattori"] = disp["% attrattori"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(disp.set_index("Città"), use_container_width=True)

    # ── Confronto ripartizioni ───────────────────────────────────────────
    else:
        rip = df.groupby("ripartizione").agg(
            n_comuni=("Procom", "count"),
            attrattori=("classificazione", lambda x: (x == "attrattore").sum()),
            emettitori=("classificazione", lambda x: (x == "emettitore").sum()),
            poli_totali=("n_poli_totali", "sum"), ind_attr_medio=("indice_attrattivita", "mean"),
            int_cult_media=("intensita_culturale", "mean"), saldo_medio=("saldo_netto", "mean"),
            pop_totale=("POP21", "sum"),
        ).reset_index()
        rip["pct_attrattori"] = (rip["attrattori"] / rip["n_comuni"] * 100).round(1)

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            for cls, colore in COLORI.items():
                vals = rip.apply(lambda r: df[(df["ripartizione"] == r["ripartizione"]) & (df["classificazione"] == cls)].shape[0], axis=1)
                fig.add_trace(go.Bar(x=rip["ripartizione"], y=vals, name=cls.capitalize(), marker_color=colore))
            fig.update_layout(**_layout(barmode="stack", height=360, margin=dict(t=10, b=60, l=40, r=10)))
            st.plotly_chart(fig, use_container_width=True, key=f"{key}_terr_ripbar")
        with c2:
            fig = px.bar(rip, x="ripartizione", y=["ind_attr_medio", "int_cult_media"], barmode="group", height=360,
                         color_discrete_map={"ind_attr_medio": "#051186", "int_cult_media": "#4FC3F7"},
                         labels={"ripartizione": "", "value": "Valore medio", "variable": "Indicatore"})
            fig.update_layout(**_layout(margin=dict(t=10, b=60, l=40, r=10)))
            nomi = {"ind_attr_medio": "Ind. attrattività", "int_cult_media": "Int. culturale"}
            fig.for_each_trace(lambda t: t.update(name=nomi.get(t.name, t.name)))
            st.plotly_chart(fig, use_container_width=True, key=f"{key}_terr_ripgroup")

        disp = rip.copy()
        disp["ind_attr_medio"] = disp["ind_attr_medio"].round(3)
        disp["int_cult_media"] = disp["int_cult_media"].round(3)
        disp["saldo_medio"] = disp["saldo_medio"].round(0).astype(int)
        disp["pct_attrattori"] = disp["pct_attrattori"].apply(lambda x: f"{x:.1f}%")
        disp.columns = ["Ripartizione", "N. comuni", "Attrattori", "Emettitori", "Poli culturali",
                         "Ind. attr. medio", "Int. cult. media", "Saldo medio", "Popolazione", "% attrattori"]
        st.dataframe(disp.set_index("Ripartizione"), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — CULTURA & MOBILITÀ  (da 3_cultura_mobilita.py)
# ══════════════════════════════════════════════════════════════════════════
def _tab_cultura(df: pd.DataFrame, key: str):
    c1, c2, c3 = st.columns(3)
    with c1:
        soglia_poli = st.select_slider("Soglia 'territorio culturale'", options=[1, 2, 5, 10, 20, 50], value=5,
                                        key=f"{key}_cult_soglia",
                                        help="Numero minimo di poli per definire un territorio culturale")
    with c2:
        regione_filtro = st.selectbox("Regione (opzionale)", ["Tutte"] + sorted(df["nome_regione"].dropna().unique()),
                                       key=f"{key}_cult_reg")
    with c3:
        min_uscite = st.slider("Uscite minime (pendolari)", 0, 5000, 100, step=100, key=f"{key}_cult_usc")

    dff = df.copy()
    if regione_filtro != "Tutte":
        dff = dff[dff["nome_regione"] == regione_filtro]
    dff = dff[dff["uscite"] >= min_uscite]

    n_culturali = (dff["n_poli_totali"] >= soglia_poli).sum()
    flussi_verso = dff["flussi_verso_cultura"].sum()
    pct_flussi = flussi_verso / dff["uscite"].sum() * 100 if dff["uscite"].sum() > 0 else 0

    _kpi_row([
        ("#25465D", "Territori culturali",  f"{n_culturali:,}", f"comuni con ≥{soglia_poli} poli"),
        ("#4FC3F7", "Flussi verso cultura", f"{flussi_verso/1e6:.2f}M", f"{pct_flussi:.1f}% del totale"),
        ("#10a870", "Int. culturale media", f"{dff['intensita_culturale'].mean():.3f}", "quota flussi verso cultura"),
        ("#7B5EA7", "Dest. culturali medie", f"{dff['n_destinazioni_culturali'].mean():.1f}", "comuni cult. distinti raggiunti"),
    ])
    _divider()

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.scatter(dff, x="intensita_culturale", y="saldo_netto", color="classificazione",
                          color_discrete_map=COLORI, size="n_poli_totali", size_max=35, hover_name="COMUNE",
                          labels={"intensita_culturale": "Intensità culturale (quota flussi → cultura)",
                                  "saldo_netto": "Saldo netto mobilità"}, height=400)
        fig.update_layout(**_layout(margin=dict(t=10, b=40, l=50, r=20)))
        fig.add_hline(y=0, line_dash="dash", line_color="#25465D", line_width=1, opacity=0.5)
        fig.add_vline(x=dff["intensita_culturale"].median(), line_dash="dot", line_color="#4FC3F7", line_width=1, opacity=0.5)
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_cult_scatter1")
    with c2:
        fig = go.Figure()
        for cls in ["emettitore", "attrattore", "equilibrato"]:
            vals = dff[dff["classificazione"] == cls]["intensita_culturale"].dropna()
            fig.add_trace(go.Box(y=vals, name=cls, marker_color=COLORI.get(cls, "#888"), boxpoints=False, hoverinfo="none"))
        fig.update_layout(**_layout(showlegend=False, height=190, margin=dict(t=40, b=30, l=40, r=40)))
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_cult_box")

        d2 = dff[dff["n_poli_totali"] > 0]
        fig = px.scatter(d2, x="indice_attrattivita", y="n_poli_totali", color="classificazione",
                          color_discrete_map=COLORI, hover_name="COMUNE", log_y=True,
                          labels={"indice_attrattivita": "Indice attrattività", "n_poli_totali": "N. poli (log)"}, height=190)
        fig.update_layout(**_layout(showlegend=False, margin=dict(t=5, b=40, l=50, r=10)))
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_cult_scatter2")

    _divider()
    _label("SENSIBILITÀ ALLA SOGLIA CULTURALE")
    _titolo("Come cambia la quota di flussi verso cultura al variare della soglia")

    righe = []
    for s in [1, 2, 5, 10, 20, 50, 100]:
        n_c = (df["n_poli_totali"] >= s).sum()
        fl_ratio = n_c / max((df["n_poli_totali"] >= 1).sum(), 1) if s != 1 else 1
        fl, tot = dff["flussi_verso_cultura"].sum() * fl_ratio, dff["uscite"].sum()
        righe.append({"Soglia": f"≥{s}", "N. comuni culturali": n_c,
                       "% flussi verso cultura": round(fl / tot * 100, 1) if tot > 0 else 0})
    ds = pd.DataFrame(righe)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(ds, x="Soglia", y="N. comuni culturali", color="N. comuni culturali",
                     color_continuous_scale=["#b3dff5", "#25465D"], height=270)
        fig.update_layout(**_layout(coloraxis_showscale=False, margin=dict(t=10, b=40, l=50, r=10)))
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_cult_sens1")
    with c2:
        fig = px.line(ds, x="Soglia", y="% flussi verso cultura", markers=True, height=270)
        fig.update_layout(**_layout(margin=dict(t=10, b=40, l=50, r=10)))
        fig.update_traces(line_color="#25465D", marker_color="#4FC3F7")
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_cult_sens2")

    _divider()
    _label("PROFILI TERRITORIO")
    _titolo("Quattro quadranti della relazione cultura-mobilità")

    med_int, med_attr = dff["intensita_culturale"].median(), dff["indice_attrattivita"].median()

    def _quadrante(r):
        alta_i, alta_a = r["intensita_culturale"] >= med_int, r["indice_attrattivita"] >= med_attr
        if alta_i and alta_a: return "Alta attrattività + Alta int. culturale"
        if alta_a: return "Alta attrattività + Bassa int. culturale"
        if alta_i: return "Bassa attrattività + Alta int. culturale"
        return "Bassa attrattività + Bassa int. culturale"

    dff = dff.copy()
    dff["quadrante"] = dff.apply(_quadrante, axis=1)
    colori_q = {"Alta attrattività + Alta int. culturale": "#10a870", "Alta attrattività + Bassa int. culturale": "#25465D",
                "Bassa attrattività + Alta int. culturale": "#4FC3F7", "Bassa attrattività + Bassa int. culturale": "#b3dff5"}

    fig = px.scatter(dff[dff["uscite"] >= 200], x="intensita_culturale", y="indice_attrattivita", color="quadrante",
                      color_discrete_map=colori_q, size="n_poli_totali", size_max=30, hover_name="COMUNE",
                      labels={"intensita_culturale": "Intensità culturale", "indice_attrattivita": "Indice attrattività"}, height=430)
    fig.update_layout(**_layout(margin=dict(t=10, b=80, l=50, r=20),
                                 legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=10, color=TEXT_COLOR))))
    fig.add_hline(y=med_attr, line_dash="dot", line_color="#b3dff5", line_width=1)
    fig.add_vline(x=med_int, line_dash="dot", line_color="#b3dff5", line_width=1)
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_cult_quad")

    cq = dff.groupby("quadrante").agg(n_comuni=("Procom", "count"), poli_medi=("n_poli_totali", "mean"),
                                       ind_attr_medio=("indice_attrattivita", "mean")).reset_index()
    cq["poli_medi"] = cq["poli_medi"].round(1)
    cq["ind_attr_medio"] = cq["ind_attr_medio"].round(3)
    cq.columns = ["Quadrante", "N. comuni", "Poli medi", "Ind. attr. medio"]
    st.dataframe(cq.set_index("Quadrante"), use_container_width=True)



# ══════════════════════════════════════════════════════════════════════════
# MAPPE INTERATTIVE (Kepler.gl)
# ══════════════════════════════════════════════════════════════════════════
# Per ciascuna mappa indica UNA delle due cose:
#   - un file HTML esportato da Kepler.gl, nella cartella caso_mobilita/mappe/  (es. "classificazione_comuni.html")
#   - un link https://... alla mappa già pubblicata online
# Lasciando "" la mappa mostra un riquadro "non trovata".
MAPPE = {
    "Classificazione comuni": "https://timely-melba-1159fe.netlify.app/mappa.gl.html",   # ← file o link: comuni per classificazione + rete infrastrutturale
    "Saldo netto": "https://incandescent-pony-29622c.netlify.app/mappa_saldo.gl.html",              # ← file o link: intensità del saldo netto + rete infrastrutturale
}
MAPPA_ALTEZZA = 750  # altezza in pixel


@st.cache_data(show_spinner="Carico la mappa…")
def _leggi_html(percorso: str, mtime: float) -> str:
    return Path(percorso).read_text(encoding="utf-8")


def _mostra_mappa(sorgente: str, nome: str):
    import streamlit.components.v1 as components
    sorgente = (sorgente or "").strip()
    if sorgente.startswith(("http://", "https://")):
        components.iframe(sorgente, height=MAPPA_ALTEZZA, scrolling=True)
        return
    for base in (Path(__file__).parent / "mappe", Path(__file__).parent):
        p = base / sorgente
        if sorgente and p.is_file():
            components.html(_leggi_html(str(p), p.stat().st_mtime), height=MAPPA_ALTEZZA, scrolling=True)
            return
    st.markdown(f"""
    <div class="insight-box">
        <strong>Mappa non trovata:</strong> {nome}<br>
        Indica il file (in <code>caso_mobilita/mappe/</code>) o il link in <code>MAPPE</code>, in cima a questa sezione di <code>mobilita.py</code>.
    </div>
    """, unsafe_allow_html=True)


def _tab_mappe(key: str):
    scelta = st.radio("Mappa", list(MAPPE), key=f"{key}_mappe_sel", horizontal=True)
    _mostra_mappa(MAPPE[scelta], scelta)


def render_caso(key: str = "mobilita"):
    """Punto d'ingresso: 4 schede (Panoramica, Analisi territoriale, Cultura & Mobilità, Mappe)."""
    df = carica_dati()
    if df is None:
        st.error(f"File dati non trovato: `{FILE_DATI.name}` deve stare nella cartella `dati/` accanto a questo file.")
        return
    t1, t2, t3, t4 = st.tabs(["Panoramica nazionale", "Analisi territoriale", "Cultura & Mobilità", "Mappe interattive"])
    with t1:
        _tab_panoramica(df, key)
    with t2:
        _tab_territoriale(df, key)
    with t3:
        _tab_cultura(df, key)
    with t4:
        _tab_mappe(key)