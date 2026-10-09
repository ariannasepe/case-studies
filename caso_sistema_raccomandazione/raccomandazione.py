"""
Caso studio: Sistema di raccomandazione personalizzata dei luoghi culturali
in Italia — portato da app_raccomandazione.py.

"""

import html
import re
import sys
import textwrap
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# user_profile.py e recommender.py stanno in questa cartella e si importano
# tra loro con import assoluti: la cartella deve essere nel path.
_QUI = Path(__file__).parent
if str(_QUI) not in sys.path:
    sys.path.insert(0, str(_QUI))

from user_profile import (  # noqa: E402
    UserProfile, get_area_centroid,
    TEMI, TIPOLOGIE, REGIONI, PROFILI_PREDEFINITI,
)
from recommender import raccomanda, spiega_raccomandazione  # noqa: E402

# ── Configurazione ───────────────────────────────────────────────────────────
NOME_FILE_DATI = "dataset_sistema.csv"
ALTEZZA_MAPPA = 520

# Chiave OpenCage (geocodifica dell'indirizzo): se in .streamlit/secrets.toml
# esiste OPENCAGE_KEY viene usata quella, altrimenti questa.
OPENCAGE_KEY = "646511d641a34b2a8bb2fe5cebb1f32d"

LIKERT_SCALE = {
    "Per nulla": 0.0,
    "Poco": 0.25,
    "Abbastanza": 0.5,
    "Molto": 0.75,
    "Moltissimo": 1.0,
}
LIKERT_LABELS = list(LIKERT_SCALE.keys())

COLORI_FOLIUM = {
    "Museo":             "blue",
    "Galleria":          "purple",
    "Biblioteca":        "green",
    "Teatro":            "orange",
    "Monumento":         "gray",
    "Sito archeologico": "red",
}

# Nel dataset alcune regioni hanno un nome diverso da quello di REGIONI
# (nomi bilingue, o in inglese/francese): uniformati al caricamento.
REGIONI_DATASET = {
    "Trentino-Alto Adige/Südtirol": "Trentino-Alto Adige",
    "Valle d'Aosta/Vallée d'Aoste": "Valle d'Aosta",
    "The Marches": "Marche",
    "Basilicate": "Basilicata",
}

CSS = """
<style>
.scheda {
    background: #f4faff; border-radius: 14px; padding: 1.2rem 1.4rem;
    border-left: 4px solid #25465D; box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    margin-bottom: 0.8rem;
}
.scheda-top {
    display: flex; align-items: flex-start; justify-content: space-between;
    gap: 8px; margin-bottom: 0.3rem;
}
.scheda-title { font-size: 1rem; font-weight: 700; color: #25465D; }
.scheda-meta  { font-size: 0.78rem; color: #34465A; margin-bottom: 0.5rem; }
.scheda .insight-box { margin: 0.6rem 0 0 0; }
.score-badge {
    display: inline-block; background: #25465D; color: #ffffff;
    border-radius: 20px; padding: 2px 12px; font-size: 0.75rem;
    font-weight: 700; letter-spacing: 0.5px; white-space: nowrap; flex-shrink: 0;
}
.tipologia-tag {
    display: inline-block; background: #dbeafe; color: #1a6a9a;
    border-radius: 4px; padding: 1px 8px; font-size: 0.75rem;
    font-weight: 600; margin-right: 4px;
}
.tema-tag {
    display: inline-block; background: #e2f0fb; color: #25465D;
    border-radius: 4px; padding: 1px 8px; font-size: 0.75rem; font-weight: 600;
}
</style>
"""


# ── Helper ───────────────────────────────────────────────────────────────────
def _largo(funzione, *args, **kwargs):
    """Widget a tutta larghezza: il parametro cambia a seconda della versione
    di Streamlit, quindi si prova in ordine dal più recente al più vecchio."""
    for extra in ({"width": "stretch"}, {"use_container_width": True}, {}):
        try:
            return funzione(*args, **kwargs, **extra)
        except TypeError:
            continue


def _label(testo: str):
    st.markdown(f'<div class="section-label">{testo}</div>', unsafe_allow_html=True)


def _titolo(testo: str):
    st.markdown(f'<div class="section-title" style="font-size:1.1rem;">{testo}</div>',
                unsafe_allow_html=True)


def _divider():
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


def _percorso_dati() -> Path | None:
    for base in (_QUI / "dati", _QUI):
        p = base / NOME_FILE_DATI
        if p.is_file():
            return p
    return None


@st.cache_data(show_spinner="Carico il dataset dei luoghi culturali…")
def carica_dati(percorso: str, mtime: float):
    """Restituisce (dataset, elenco dei comuni). `mtime` serve solo a
    invalidare la cache quando il file cambia."""
    df = pd.read_csv(percorso)
    df["regione"] = df["regione"].replace(REGIONI_DATASET)
    comuni = sorted(df["comune"].dropna().str.title().unique().tolist())
    return df, comuni


def _chiave_opencage() -> str:
    try:
        return st.secrets.get("OPENCAGE_KEY", OPENCAGE_KEY)
    except Exception:
        return OPENCAGE_KEY


@st.cache_data(show_spinner=False)
def _geocodifica(indirizzo: str, comune: str):
    """(lat, lon, indirizzo formattato) oppure None se non trovato."""
    from opencage.geocoder import OpenCageGeocode
    risultati = OpenCageGeocode(_chiave_opencage()).geocode(
        f"{indirizzo}, {comune}, Italia", language="it", countrycode="it")
    if not risultati:
        return None
    r = risultati[0]
    return r["geometry"]["lat"], r["geometry"]["lng"], r["formatted"]


def _nome_area(area: dict) -> str:
    """Nome da mostrare: le regioni restano come sono ("Valle d'Aosta"),
    i comuni (salvati in minuscolo) tornano con l'iniziale maiuscola."""
    valore = str(area["valore"])
    return valore if valore in REGIONI else valore.title()


def _scheda_html(rank: int, row: pd.Series, profilo: UserProfile) -> str:
    esc = html.escape
    # spiega_raccomandazione() restituisce Markdown (**grassetto**): dentro un
    # blocco HTML non verrebbe interpretato, quindi lo si converte in <b>.
    spiegazione = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>",
                         esc(spiega_raccomandazione(row, profilo)))
    meta = (f"{esc(row['comune'].title())}, {esc(row['regione'])}"
            f" &nbsp;·&nbsp; {row['distanza_km']:.1f} km")
    if int(row["accessibile_disabili"]) == 1:
        meta += " &nbsp;·&nbsp; Accessibile"
    return "".join([
        '<div class="scheda">',
        '<div class="scheda-top">',
        f'<div class="scheda-title">#{rank} {esc(row["nome"])}</div>',
        f'<span class="score-badge">Score {row["score"]:.3f}</span>',
        '</div>',
        f'<div class="scheda-meta">{meta}</div>',
        f'<span class="tipologia-tag">{esc(row["tipologia"])}</span>',
        f'<span class="tema-tag">{esc(row["tema_principale"])}</span>',
        f'<div class="insight-box">{spiegazione}</div>',
        '</div>',
    ])


NOTA_METODOLOGICA = """
**Obiettivo della dashboard**

La dashboard supporta la raccomandazione personalizzata di luoghi culturali italiani (musei, gallerie, biblioteche, teatri, monumenti e siti archeologici) sulla base delle preferenze espresse dall'utente, della localizzazione geografica e delle caratteristiche dell'offerta culturale disponibile. Il sistema genera una graduatoria dei luoghi più pertinenti e ne visualizza la distribuzione territoriale tramite mappa interattiva.

**Costruzione del profilo utente**

L'utente definisce il proprio profilo attraverso: selezione di un profilo culturale predefinito; attribuzione di pesi ai temi di interesse mediante scala Likert a cinque livelli; selezione delle tipologie di luoghi culturali preferite; definizione dell'area geografica di ricerca (regione o comune); impostazione del raggio di ricerca espresso in chilometri; eventuale filtro per l'accessibilità ai disabili. Le risposte vengono trasformate in pesi numerici compresi tra 0 e 1.

**Processo di raccomandazione**

Il sistema adotta un approccio di raccomandazione basato sul contenuto (content-based recommendation), attribuendo a ciascun luogo culturale uno score di rilevanza basato sulla corrispondenza con le preferenze dell'utente, sulla tipologia del luogo e sulla prossimità geografica. I risultati vengono successivamente ordinati e presentati come raccomandazioni personalizzate.

**Visualizzazione dei risultati**

I risultati vengono presentati attraverso una mappa interattiva e attraverso schede descrittive che riportano posizione in classifica, punteggio ottenuto, distanza dal centro di ricerca, tipologia e tema principale, spiegazione testuale della raccomandazione e indicazione dell'accessibilità quando disponibile.

**Interpretazione dello score**

Lo score rappresenta un indice sintetico di compatibilità tra il profilo utente e il luogo culturale analizzato. Valori più elevati indicano una maggiore aderenza alle preferenze espresse e ai criteri territoriali impostati. Lo score è utilizzato esclusivamente per il ranking relativo dei risultati e non costituisce una misura assoluta della qualità del luogo culturale.

**Limiti dell'analisi**

I risultati dipendono dalla completezza e dall'aggiornamento del dataset utilizzato. Le raccomandazioni riflettono le preferenze dichiarate dall'utente e le informazioni disponibili nel sistema e non tengono conto di fattori esterni quali recensioni recenti, eventi temporanei, disponibilità di accesso o variazioni dell'offerta culturale successive all'aggiornamento del database.

---
*Fonte dati: OpenStreetMap via Overpass API, ISTAT. Elaborazione: Python (Pandas, Numpy, Folium, OpenCage, Streamlit).*
"""


# ── Form del profilo ─────────────────────────────────────────────────────────
def _form(df: pd.DataFrame, comuni: list, key: str):
    """Disegna i controlli e restituisce (profilo, top_n, cerca)."""
    k = lambda nome: f"{key}_{nome}"

    c1, c2 = st.columns([1, 2], gap="medium")
    with c1:
        nome = st.text_input("Il tuo nome (opzionale)", placeholder="Es. Mario", key=k("nome"))
    with c2:
        profilo_scelto = st.selectbox("Chi sei?", list(PROFILI_PREDEFINITI), key=k("profilo"))
    dati_profilo = PROFILI_PREDEFINITI[profilo_scelto]
    st.caption(dati_profilo["descrizione"])

    with st.expander("Personalizza i pesi (opzionale)"):
        st.caption("Quanto ti interessano i seguenti aspetti?")
        st.markdown("**Temi**")
        temi_pesi = {}
        colonne = st.columns(3, gap="medium")
        for i, tema in enumerate(TEMI):
            default_value = dati_profilo["temi_pesi"].get(tema, 0.5)
            default_label = next(
                (lab for lab, val in LIKERT_SCALE.items() if abs(val - default_value) < 0.01),
                "Abbastanza")
            with colonne[i % 3]:
                scelta = st.select_slider(tema, options=LIKERT_LABELS, value=default_label,
                                          key=k(f"tema_{tema}_{profilo_scelto}"))
            temi_pesi[tema] = LIKERT_SCALE[scelta]

        st.markdown("**Tipologie**")
        tipologie_pesi = {}
        colonne = st.columns(3, gap="medium")
        for i, tipologia in enumerate(TIPOLOGIE):
            peso = dati_profilo["tipologie_pesi"].get(tipologia, 0.0)
            with colonne[i % 3]:
                scelta = st.checkbox(tipologia, value=peso > 0,
                                     key=k(f"tipo_{tipologia}_{profilo_scelto}"))
            tipologie_pesi[tipologia] = peso if scelta else 0.0

    a1, a2, a3 = st.columns([1, 1.3, 1.7], gap="medium")
    coordinate = None
    with a1:
        area_tipo = st.radio("Cerca per", ["Regione", "Comune"], horizontal=True, key=k("area_tipo"))
    with a2:
        if area_tipo == "Regione":
            area_valore = st.selectbox("Regione", REGIONI, key=k("regione"))
        else:
            area_valore = st.selectbox("Comune", comuni, key=k("comune"))
    with a3:
        if area_tipo == "Comune":
            indirizzo = st.text_input("Indirizzo specifico (opzionale)",
                                      placeholder="Es. Via Roma 1", key=k("indirizzo"))
            if indirizzo.strip():
                try:
                    trovato = _geocodifica(indirizzo.strip(), area_valore)
                    if trovato:
                        coordinate = trovato[:2]
                        st.success(trovato[2])
                    else:
                        st.warning("Indirizzo non trovato nel comune selezionato. "
                                   "La ricerca partirà dal centro del comune.")
                except Exception:
                    st.warning("Servizio di geolocalizzazione non disponibile. "
                               "La ricerca partirà dal centro del comune.")

    b1, b2, b3 = st.columns([1.3, 1.3, 1], gap="medium")
    with b1:
        raggio_km = st.slider("Raggio di ricerca (km)", 10, 300, 50, 10, key=k("raggio"))
    with b2:
        top_n = st.slider("Numero di risultati", 5, 30, 10, 5, key=k("top_n"))
    with b3:
        st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        solo_accessibile = st.checkbox("Solo luoghi accessibili ai disabili", key=k("accessibile"))

    cerca = _largo(st.button, "Cerca luoghi", type="primary", key=k("cerca"))

    area = {"tipo": area_tipo.lower(),
            "valore": area_valore if area_tipo == "Regione" else area_valore.lower()}
    if coordinate:
        area["tipo"] = "indirizzo"
        area["centroid"] = coordinate

    profilo = UserProfile(nome=nome, temi_pesi=temi_pesi, tipologie_pesi=tipologie_pesi,
                          area=area, raggio_km=raggio_km, solo_accessibile=solo_accessibile)
    return profilo, top_n, cerca


# ── Risultati ────────────────────────────────────────────────────────────────
def _risultati(df: pd.DataFrame, profilo: UserProfile, top_n: int, key: str):
    valido, messaggio = profilo.is_valid()
    if not valido:
        st.warning(messaggio)
        return

    with st.spinner("Calcolo raccomandazioni in corso..."):
        risultati = raccomanda(profilo, df, top_n=top_n)

    if risultati.empty:
        st.error("Nessun luogo trovato con i criteri selezionati. "
                 "Prova ad aumentare il raggio o a selezionare più tipologie.")
        return

    area = profilo.area
    if area.get("tipo") == "indirizzo":
        centroid = area["centroid"]
    else:
        centroid = get_area_centroid(profilo, df)

    nome_display = f"**{profilo.nome}**" if profilo.nome else "te"
    st.success(f"Trovati **{len(risultati)}** luoghi per {nome_display} "
               f"in **{_nome_area(area)}** entro **{profilo.raggio_km:.0f} km**.")
    _divider()

    col_mappa, col_schede = st.columns([1.2, 1], gap="medium")

    with col_mappa:
        _label("Distribuzione geografica")
        _titolo("Mappa dei luoghi consigliati")
        mappa = folium.Map(location=list(centroid), zoom_start=9, tiles="OpenStreetMap")
        folium.Marker(
            location=list(centroid),
            tooltip=f"Centro ricerca: {_nome_area(area)}",
            icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
        ).add_to(mappa)
        folium.Circle(
            location=list(centroid), radius=profilo.raggio_km * 1000,
            color="#25465D", fill=True, fill_opacity=0.05, weight=1.5,
        ).add_to(mappa)
        for rank, (_, row) in enumerate(risultati.iterrows(), start=1):
            popup_html = (
                "<div style='min-width:180px;font-family:sans-serif;'>"
                f"<b style='color:#25465D'>#{rank} {html.escape(row['nome'])}</b><br>"
                f"<span style='color:#555'>{html.escape(row['tipologia'])} · "
                f"{html.escape(row['comune'].title())}</span><br>"
                f"<span style='color:#888'>{html.escape(row['tema_principale'])}</span><br>"
                f"<b>Score: {row['score']:.3f}</b> · {row['distanza_km']:.1f} km</div>"
            )
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"#{rank} {row['nome']}",
                icon=folium.Icon(color=COLORI_FOLIUM.get(row["tipologia"], "blue"),
                                 icon="info-sign"),
            ).add_to(mappa)
        st_folium(mappa, width="100%", height=ALTEZZA_MAPPA, returned_objects=[],
                  key=f"{key}_mappa")

    with col_schede:
        _label("Raccomandazioni personalizzate")
        _titolo("Luoghi consigliati")
        for rank, (_, row) in enumerate(risultati.iterrows(), start=1):
            st.markdown(_scheda_html(rank, row, profilo), unsafe_allow_html=True)

    with st.expander("Dati completi risultati"):
        _largo(st.dataframe, risultati.drop(columns=["lat", "lon"], errors="ignore"),
               hide_index=True)


# ── Punto d'ingresso ─────────────────────────────────────────────────────────
def render_caso(key: str = "raccomandazione"):
    """Punto d'ingresso: form del profilo, mappa e schede dei luoghi consigliati."""
    st.markdown(CSS, unsafe_allow_html=True)

    percorso = _percorso_dati()
    if percorso is None:
        st.error(f"File dati non trovato: `{NOME_FILE_DATI}` deve stare nella cartella "
                 f"`dati/` (o accanto a questo file).")
        return
    df, comuni = carica_dati(str(percorso), percorso.stat().st_mtime)

    profilo, top_n, cerca = _form(df, comuni, key)

    if not cerca:
        st.markdown("""
        <div class="insight-box" style="text-align:center;padding:1.6rem 1.2rem;">
            <strong>Configura il tuo profilo e avvia la ricerca</strong><br>
            Scegli il tuo profilo culturale, l'area geografica di interesse e il raggio di
            esplorazione: il sistema calcolerà i luoghi più pertinenti in base alle tue preferenze.
        </div>
        """, unsafe_allow_html=True)
    else:
        _risultati(df, profilo, top_n, key)

    with st.expander("Nota metodologica"):
        st.markdown(textwrap.dedent(NOTA_METODOLOGICA))