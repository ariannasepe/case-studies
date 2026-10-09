"""
digital_twin.py — Caso studio "DIGITAL TWIN" (Rimini)
=====================================================
"""
import json
import math
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# ── TEMA CROMATICO (identico alla base grafica di riferimento) ───────────────
CHART_BG    = "#f4faff"
CHART_INNER = "#eaf4fc"
GRID_COLOR  = "#d6eaf6"
AXIS_COLOR  = "#a8cfe0"
TEXT_COLOR  = "#1a3a4f"
CHART_FONT  = "Manrope"

# Palette dedicata alle aree tematiche del Digital Twin
AREA_COLORS = {
    "Popolazione": "#25465D",
    "Economia":    "#F4A261",
    "Territorio":  "#00A878",
    "Servizi":     "#E85933",
}

PLOTLY_LAYOUT = dict(
    plot_bgcolor  = CHART_INNER,
    paper_bgcolor = CHART_BG,
    font          = dict(family=CHART_FONT, color=TEXT_COLOR, size=13),
    title         = dict(
        font=dict(size=15, color=TEXT_COLOR, family=CHART_FONT),
        x=0.01, xanchor="left", y=0.97, yanchor="top",
    ),
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
        orientation="h", yanchor="top", y=-0.32,
        xanchor="center", x=0.5,
        font=dict(size=12, color=TEXT_COLOR),
        bgcolor="rgba(244,250,255,0.9)",
        bordercolor=AXIS_COLOR, borderwidth=1,
        title_text="",
    ),
    hoverlabel    = dict(
        bgcolor="#1a3a4f", font_color="white",
        font_family=CHART_FONT, font_size=12, bordercolor="#1a3a4f"
    ),
    margin        = dict(t=48, b=110, l=55, r=20),
)


def applica_layout(fig, height=None, xaxis_title=None, yaxis_title=None, **extra):
    """Applica PLOTLY_LAYOUT e, se richiesto, imposta i titoli degli assi
    SENZA perdere font/colore già definiti in PLOTLY_LAYOUT. Per i grafici
    cartesiani (bar, line, scatter...)."""
    fig.update_layout(**PLOTLY_LAYOUT)
    if height is not None:
        fig.update_layout(height=height)
    if xaxis_title is not None:
        fig.update_xaxes(title=dict(text=xaxis_title, font=dict(size=12, color=TEXT_COLOR)))
    if yaxis_title is not None:
        fig.update_yaxes(title=dict(text=yaxis_title, font=dict(size=12, color=TEXT_COLOR)))
    if extra:
        fig.update_layout(**extra)
    return fig


_MAPPE_NUOVE = hasattr(px, "scatter_map")


def scatter_mappa(*args, **kwargs):
    return px.scatter_map(*args, **kwargs) if _MAPPE_NUOVE else px.scatter_mapbox(*args, **kwargs)


def choropleth_mappa(*args, **kwargs):
    return px.choropleth_map(*args, **kwargs) if _MAPPE_NUOVE else px.choropleth_mapbox(*args, **kwargs)


def linea_mappa(*args, **kwargs):
    return px.line_map(*args, **kwargs) if _MAPPE_NUOVE else px.line_mapbox(*args, **kwargs)


def imposta_stile_mappa(fig, stile="open-street-map"):
    if _MAPPE_NUOVE:
        fig.update_layout(map_style=stile)
    else:
        fig.update_layout(mapbox_style=stile)
    return fig


def applica_layout_mappa(fig, height=460, titolo=None):
    """Layout dedicato alle mappe (scatter_mapbox / choropleth_mapbox), che
    non hanno assi cartesiani: applica solo font, sfondo, margini e titolo."""
    fig.update_layout(
        paper_bgcolor=CHART_BG,
        font=dict(family=CHART_FONT, color=TEXT_COLOR, size=13),
        margin=dict(t=48 if titolo else 10, b=10, l=10, r=10),
        height=height,
        legend=dict(
            orientation="h", yanchor="top", y=-0.04, xanchor="center", x=0.5,
            font=dict(size=11, color=TEXT_COLOR),
            bgcolor="rgba(244,250,255,0.9)", bordercolor=AXIS_COLOR, borderwidth=1,
            title_text="",
        ),
     
        coloraxis_colorbar=dict(
            tickfont=dict(color=TEXT_COLOR, size=12, family=CHART_FONT),
            title=dict(font=dict(color=TEXT_COLOR, size=12, family=CHART_FONT)),
            bgcolor="rgba(244,250,255,0.9)",
            bordercolor=AXIS_COLOR, borderwidth=1, outlinewidth=0,
        ),
        hoverlabel=dict(bgcolor="#1a3a4f", font_color="white", font_family=CHART_FONT, font_size=12),
    )
    if titolo:
        fig.update_layout(title=dict(
            text=titolo, font=dict(size=15, color=TEXT_COLOR, family=CHART_FONT),
            x=0.01, xanchor="left", y=0.97, yanchor="top",
        ))
    return fig


def kpi(col, label, value, sub, color):
    # font-size calibrato sulla lunghezza effettiva del valore
    n = len(str(value))
    if n <= 4:
        font_size = "2.3rem"
    elif n <= 6:
        font_size = "2rem"
    elif n <= 8:
        font_size = "1.7rem"
    elif n <= 10:
        font_size = "1.4rem"
    else:
        font_size = "1.2rem"

    with col:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:{color};">
            <div class="top-bar" style="background:{color};opacity:0.7;"></div>
            <div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="color:{color};font-size:{font_size};">{value}</div>
            </div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)


def fmt(v, decimali=0):
    if isinstance(v, (int, float, np.integer, np.floating)):
        return f"{v:,.{decimali}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return v


# ══════════════════════════════════════════════════════════════════════════
# DATI — SEZIONE AMBIENTE (Home): caricati dai geojson reali del Digital Twin
# ══════════════════════════════════════════════════════════════════════════
AMBIENTE_FILES = {
    "aria":      DATA_DIR / "ambiente/aria_rimini.geojson",
    "energia":   DATA_DIR / "ambiente/energia_rimini.geojson",
    "meteo":     DATA_DIR / "ambiente/meteo_rimini.geojson",
    "uso_suolo": DATA_DIR / "ambiente/uso_suolo_rimini.geojson",
}

LANDUSE_VERDE = {
    "grass", "forest", "meadow", "farmland", "orchard", "allotments",
    "recreation_ground", "flowerbed", "plant_nursery",
    "greenhouse_horticulture", "greenfield",
}

TIPO_ENERGIA_LABEL = {
    "pannello_solare":    "Pannelli solari",
    "colonnina_ricarica": "Colonnine di ricarica",
    "centrale_elettrica": "Centrali elettriche",
    "cabina_elettrica":   "Cabine elettriche",
}
TIPO_ENERGIA_COLOR = {
    "Pannelli solari":       "#F4A261",
    "Colonnine di ricarica": "#4FC3F7",
    "Centrali elettriche":   "#E85933",
    "Cabine elettriche":     "#25465D",
}


def _geojson_punti_to_df(geojson: dict) -> pd.DataFrame:
    righe = []
    for feat in geojson.get("features", []):
        geom = feat.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        lon, lat = geom["coordinates"][:2]
        props = feat.get("properties", {})
        righe.append({
            "id": props.get("id"), "tipo": props.get("tipo"),
            "name": props.get("name"), "lat": lat, "lon": lon,
        })
    return pd.DataFrame(righe)


def _geojson_poligoni_to_df(geojson: dict) -> pd.DataFrame:
    righe = []
    for feat in geojson.get("features", []):
        geom = feat.get("geometry") or {}
        props = feat.get("properties", {})
        lat_c = lon_c = None
        if geom.get("type") == "Polygon" and geom.get("coordinates"):
            anello = geom["coordinates"][0]
            lon_c = sum(p[0] for p in anello) / len(anello)
            lat_c = sum(p[1] for p in anello) / len(anello)
        righe.append({
            "id": props.get("id"), "landuse": props.get("landuse"),
            "name": props.get("name"), "color": props.get("color"),
            "description": props.get("description"), "lat": lat_c, "lon": lon_c,
        })
    return pd.DataFrame(righe)


@st.cache_data
def carica_dati_ambiente():
    """Carica i 4 layer geojson del Digital Twin (aria, energia, meteo,
    uso del suolo) dalla cartella data/ accanto allo script.
    """
    risultato = {}
    mancanti = []
    for chiave, path in AMBIENTE_FILES.items():
        if not path.exists():
            risultato[chiave] = None
            mancanti.append(path.name)
            continue
        with open(path, encoding="utf-8") as f:
            gj = json.load(f)
        if chiave == "uso_suolo":
            risultato[chiave] = {"geojson": gj, "df": _geojson_poligoni_to_df(gj)}
        else:
            risultato[chiave] = {"geojson": gj, "df": _geojson_punti_to_df(gj)}
    return risultato, mancanti


@st.cache_data(ttl=600)
def meteo_live(lat: float, lon: float):
    """Meteo in tempo reale via Open-Meteo (API gratuita, senza chiave).

    Funzione opzionale "a valore aggiunto": se non c'è connessione o il
    servizio non risponde, ritorna None e la dashboard mostra un valore di
    fallback senza generare errori.
    """
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current_weather=true"
        )
        with urllib.request.urlopen(url, timeout=5) as resp:
            payload = json.loads(resp.read().decode())
        return payload.get("current_weather")
    except Exception:
        return None


@st.cache_data(ttl=86400)
def meteo_storico(lat: float, lon: float) -> pd.DataFrame:
    """Serie storica di temperatura e precipitazioni per la stazione meteo
    di Rimini, via la Historical Weather API di Open-Meteo 
    https://open-meteo.com/en/docs/historical-weather-api

    Copre gli ultimi 12 mesi circa, con 7 giorni di margine rispetto a
    oggi per il ritardo di pubblicazione tipico dei dati di rianalisi.

    Funzione opzionale "a valore aggiunto": se non c'è connessione o il
    servizio non risponde, ritorna un DataFrame vuoto e la dashboard mostra
    un avviso senza generare errori.
    """
    fine = date.today() - timedelta(days=7)
    inizio = fine - timedelta(days=365)
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat}&longitude={lon}"
        f"&start_date={inizio.isoformat()}&end_date={fine.isoformat()}"
        "&hourly=temperature_2m,precipitation&timezone=Europe%2FRome"
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            payload = json.loads(resp.read().decode())
        orario = payload.get("hourly", {})
        df = pd.DataFrame({
            "data_ora": pd.to_datetime(orario.get("time", [])),
            "temperatura": orario.get("temperature_2m", []),
            "precipitazioni": orario.get("precipitation", []),
        })
        if df.empty:
            return pd.DataFrame()
        df["data"] = df["data_ora"].dt.date
        giornaliero = df.groupby("data", as_index=False).agg(
            temperatura_media=("temperatura", "mean"),
            temperatura_max=("temperatura", "max"),
            temperatura_min=("temperatura", "min"),
            precipitazioni_mm=("precipitazioni", "sum"),
        )
        giornaliero["data"] = pd.to_datetime(giornaliero["data"])
        return giornaliero
    except Exception:
        return pd.DataFrame()


WMO_METEO = {
    0: "Sereno", 1: "Prevalentemente sereno", 2: "Parzialmente nuvoloso",
    3: "Coperto", 45: "Nebbia", 48: "Nebbia con brina",
    51: "Pioviggine debole", 61: "Pioggia debole", 63: "Pioggia moderata",
    65: "Pioggia forte", 71: "Neve debole", 80: "Rovesci",
    95: "Temporale",
}


# ══════════════════════════════════════════════════════════════════════════
# DATI — SEZIONE POPOLAZIONE: caricati dai geojson reali del Digital Twin
# ══════════════════════════════════════════════════════════════════════════
POPOLAZIONE_FILES = {
    "comune":     DATA_DIR / "popolazione/popolazione_rimini.geojson",
    "quartieri":  DATA_DIR / "popolazione/quartieri_rimini.geojson",
    "sezioni":    DATA_DIR / "popolazione/sezioni_censimento_rimini.geojson",
}

NOME_TOTALE_COMUNE = "Comune di Rimini - TOTALE"


def _geojson_quartieri_to_df(geojson: dict) -> pd.DataFrame:
    """Converte quartieri_rimini.geojson (poligoni) in un DataFrame con una
    riga per quartiere: popolazione, struttura per età, famiglie, densità e
    colore ufficiale, più il centroide per eventuali marker puntuali."""
    righe = []
    for feat in geojson.get("features", []):
        p = feat.get("properties", {})
        righe.append({
            "quartiere": p.get("nome"),
            "popolazione": p.get("popolazione"),
            "eta_0_14": p.get("eta_0_14"),
            "eta_15_64": p.get("eta_15_64"),
            "eta_65_plus": p.get("eta_65_plus"),
            "famiglie": p.get("famiglie"),
            "eta_media": p.get("eta_media"),
            "densita_ab_kmq": p.get("densita_ab_kmq"),
            "color": p.get("color"),
            "centroid_lat": p.get("centroid_lat"),
            "centroid_lon": p.get("centroid_lon"),
        })
    return pd.DataFrame(righe)


def _geojson_sezioni_to_df(geojson: dict) -> pd.DataFrame:
    """Converte sezioni_censimento_rimini.geojson (punti) in un DataFrame,
    per le analisi a grana fine (73 sezioni di censimento ISTAT)."""
    righe = []
    for feat in geojson.get("features", []):
        p = feat.get("properties", {})
        geom = feat.get("geometry") or {}
        lon, lat = (geom.get("coordinates") or [None, None])[:2]
        righe.append({
            "sezione_id": p.get("sezione_id"),
            "quartiere": p.get("quartiere"),
            "pop_tot": p.get("pop_tot"),
            "pop_0_14": p.get("pop_0_14"),
            "pop_15_64": p.get("pop_15_64"),
            "pop_65p": p.get("pop_65p"),
            "densita_ab_kmq": p.get("densita_ab_kmq"),
            "lat": lat, "lon": lon,
        })
    return pd.DataFrame(righe)


def _dati_comune_da_geojson(geojson: dict) -> dict | None:
    """Estrae i totali comunali (riga 'Comune di Rimini - TOTALE') da
    popolazione_rimini.geojson."""
    for feat in geojson.get("features", []):
        p = feat.get("properties", {})
        if p.get("nome") == NOME_TOTALE_COMUNE:
            return p
    return None


@st.cache_data
def carica_dati_popolazione():
    risultato = {"comune": None, "quartieri": None, "sezioni": None,
                 "geojson_quartieri": None}
    mancanti = []
    for chiave, path in POPOLAZIONE_FILES.items():
        if not path.exists():
            mancanti.append(path.name)
            continue
        with open(path, encoding="utf-8") as f:
            gj = json.load(f)
        if chiave == "comune":
            risultato["comune"] = _dati_comune_da_geojson(gj)
        elif chiave == "quartieri":
            risultato["geojson_quartieri"] = gj
            risultato["quartieri"] = _geojson_quartieri_to_df(gj)
        elif chiave == "sezioni":
            risultato["sezioni"] = _geojson_sezioni_to_df(gj)
    return risultato, mancanti


# ══════════════════════════════════════════════════════════════════════════
# DATI — SEZIONE ECONOMIA: caricati dai geojson reali (OSM) del Digital Twin
# ══════════════════════════════════════════════════════════════════════════
ECONOMIA_FILES = {
    "commercio": DATA_DIR / "economia" / "commercio_rimini.geojson",
    "imprese":   DATA_DIR / "economia" / "imprese_rimini.geojson",
}

_PREFISSI_CATEGORIA = {
    "negozio": "Negozi", "ufficio": "Uffici", "artigianato": "Artigianato",
}

MACRO_CATEGORIA_COLORS = {
    "Negozi": "#2E86AB", "Uffici": "#C1666B",
    "Artigianato": "#F4A261", "Grande distribuzione": "#00A878",
}

_ETICHETTE_SOTTOCATEGORIA = {
    "clothes": "Abbigliamento", "hairdresser": "Parrucchiere/Barbiere",
    "supermarket": "Supermercato", "tobacco": "Tabaccheria",
    "convenience": "Alimentari", "vacant": "Locale sfitto",
    "optician": "Ottica", "car_repair": "Officina auto", "laundry": "Lavanderia",
    "bakery": "Panetteria", "car": "Concessionaria auto", "bicycle": "Ciclofficina",
    "newsagent": "Edicola", "estate_agent": "Agenzia immobiliare",
    "yes": "Non specificato", "shoes": "Calzature", "government": "Ufficio pubblico",
    "greengrocer": "Fruttivendolo", "books": "Libreria", "pastry": "Pasticceria",
    "deli": "Gastronomia", "gift": "Articoli da regalo", "jewelry": "Gioielleria",
    "kiosk": "Chiosco", "company": "Azienda", "chemist": "Parafarmacia",
    "beauty": "Centro estetico", "travel_agency": "Agenzia viaggi",
    "lawyer": "Studio legale", "hardware": "Ferramenta", "butcher": "Macelleria",
    "motorcycle": "Moto", "furniture": "Mobili", "insurance": "Assicurazioni",
    "electronics": "Elettronica", "florist": "Fioraio", "pet": "Articoli per animali",
    "tattoo": "Tatuaggi", "wine": "Enoteca", "cosmetics": "Cosmesi",
    "sports": "Articoli sportivi", "it": "Informatica",
    "supermercato": "Supermercato", "mercato": "Mercato",
    "centro_commerciale": "Centro commerciale", "grande_magazzino": "Grande magazzino",
}


def _etichetta_sottocategoria(suffisso: str) -> str:
    if suffisso in _ETICHETTE_SOTTOCATEGORIA:
        return _ETICHETTE_SOTTOCATEGORIA[suffisso]
    return suffisso.replace("_", " ").capitalize()


def _punto_rappresentativo(geometry: dict):
    """Ritorna (lon, lat) di un punto rappresentativo della geometria: le
    coordinate dirette per i Point, il centroide approssimato (media dei
    vertici) per i Polygon — alcuni esercizi in questi dataset OSM sono
    mappati come sagoma dell'edificio anziché come singolo nodo."""
    t = geometry.get("type")
    if t == "Point":
        lon, lat = geometry["coordinates"][:2]
        return lon, lat
    if t == "Polygon" and geometry.get("coordinates"):
        anello = geometry["coordinates"][0]
        if anello:
            return (sum(c[0] for c in anello) / len(anello),
                    sum(c[1] for c in anello) / len(anello))
    return None, None


def _punto_in_anello(x, y, anello) -> bool:
    """Ray casting: test punto-in-poligono su un singolo anello di coordinate."""
    dentro = False
    n = len(anello)
    j = n - 1
    for i in range(n):
        xi, yi = anello[i]
        xj, yj = anello[j]
        if (yi > y) != (yj > y):
            x_int = (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi
            if x < x_int:
                dentro = not dentro
        j = i
    return dentro


def _punto_in_poligono(lon, lat, geometry) -> bool:
    t = geometry.get("type")
    if t == "Polygon":
        poligoni = [geometry["coordinates"]]
    elif t == "MultiPolygon":
        poligoni = geometry.get("coordinates", [])
    else:
        return False
    for poligono in poligoni:
        if poligono and _punto_in_anello(lon, lat, poligono[0]) and not any(
            _punto_in_anello(lon, lat, buco) for buco in poligono[1:]
        ):
            return True
    return False


def _prepara_indice_quartieri(geojson_quartieri: dict | None):
    indice = []
    if not geojson_quartieri:
        return indice
    for feat in geojson_quartieri.get("features", []):
        geom = feat.get("geometry") or {}
        anelli = []
        if geom.get("type") == "Polygon":
            anelli = geom.get("coordinates", [])
        elif geom.get("type") == "MultiPolygon":
            for poligono in geom.get("coordinates", []):
                anelli.extend(poligono)
        punti = [c for anello in anelli for c in anello]
        if not punti:
            continue
        lons = [c[0] for c in punti]
        lats = [c[1] for c in punti]
        indice.append({
            "nome": feat.get("properties", {}).get("nome"),
            "geometry": geom,
            "bbox": (min(lons), min(lats), max(lons), max(lats)),
        })
    return indice


def _assegna_quartiere(lon, lat, indice_quartieri):
    if not indice_quartieri or lon is None:
        return None
    for q in indice_quartieri:
        minlon, minlat, maxlon, maxlat = q["bbox"]
        if lon < minlon or lon > maxlon or lat < minlat or lat > maxlat:
            continue
        if _punto_in_poligono(lon, lat, q["geometry"]):
            return q["nome"]
    return None


def _geojson_esercizi_to_df(geojson: dict, geojson_quartieri, macro_fissa=None) -> pd.DataFrame:
    righe = []
    for feat in geojson.get("features", []):
        p = feat.get("properties", {})
        lon, lat = _punto_rappresentativo(feat.get("geometry", {}))
        tipo = p.get("tipo", "")
        if macro_fissa:
            macro, sotto = macro_fissa, tipo
        elif "_" in tipo:
            prefisso, sotto = tipo.split("_", 1)
            macro = _PREFISSI_CATEGORIA.get(prefisso, prefisso.capitalize())
        else:
            macro, sotto = "Altro", tipo
        righe.append({
            "id": p.get("id"), "nome": p.get("name") or "—",
            "macro_categoria": macro,
            "sotto_categoria": _etichetta_sottocategoria(sotto),
            "quartiere": _assegna_quartiere(lon, lat, geojson_quartieri),
            "lat": lat, "lon": lon,
        })
    return pd.DataFrame(righe)


@st.cache_data
def carica_dati_economia(_geojson_quartieri):
    mancanti = []
    frame = []
    _geojson_quartieri = _prepara_indice_quartieri(_geojson_quartieri)
    for chiave, path in ECONOMIA_FILES.items():
        if not path.exists():
            mancanti.append(path.name)
            continue
        with open(path, encoding="utf-8") as f:
            gj = json.load(f)
        macro_fissa = "Grande distribuzione" if chiave == "commercio" else None
        frame.append(_geojson_esercizi_to_df(gj, _geojson_quartieri, macro_fissa=macro_fissa))
    esercizi = pd.concat(frame, ignore_index=True) if frame else pd.DataFrame()
    return esercizi, mancanti


# ══════════════════════════════════════════════════════════════════════════
# DATI — SEZIONE SERVIZI: caricati dai geojson reali (OSM) del Digital Twin
# ══════════════════════════════════════════════════════════════════════════
SERVIZI_FILES = {
    "sanita":     DATA_DIR / "servizi" / "ospedali_rimini.geojson",
    "istruzione": DATA_DIR / "servizi" / "scuole_rimini.geojson",
    "trasporto":  DATA_DIR / "servizi" / "trasporto_pubblico_rimini.geojson",
    "eventi":     DATA_DIR / "servizi" / "eventi_rimini.geojson",
    "parcheggi":  DATA_DIR / "servizi" / "parcheggi_rimini.geojson",
    "ciclabili":  DATA_DIR / "servizi" / "ciclabili_rimini.geojson",
}

# Colori per dominio di servizio, usati nella mappa e nei grafici.
SERVIZIO_DOMINIO_COLORS = {
    "Sanità": "#E85933", "Istruzione": "#2E86AB",
    "Trasporto pubblico": "#8E7CC3", "Eventi e cultura": "#00A878",
    "Parcheggi": "#5E5E5E",
}

# Etichette leggibili per il tag OSM "parking" (dataset parcheggi, che non
# ha un campo "tipo" come gli altri layer Servizi).
_ETICHETTE_PARCHEGGIO = {
    "surface": "Parcheggio a raso", "street_side": "Parcheggio su strada",
    "underground": "Parcheggio sotterraneo", "multi-storey": "Parcheggio multipiano",
    "lane": "Corsia di sosta", "": "Non specificato",
}

# Etichette leggibili per il tag OSM "highway" del layer ciclabili.
_ETICHETTE_CICLABILE = {
    "cycleway": "Pista ciclabile", "path": "Sentiero/pista promiscua",
    "footway": "Marciapiede/percorso pedonale", "pedestrian": "Area pedonale",
    "construction": "In costruzione", "steps": "Scalinata",
    "tertiary": "Strada condivisa", "service": "Strada di servizio",
    "residential": "Strada residenziale",
}

# Colori per tutte le tipologie di rete ciclabile (tonalità volutamente
CICLABILI_TIPO_COLORS = {
    "Pista ciclabile": "#00A878", "Sentiero/pista promiscua": "#2E86AB",
    "Marciapiede/percorso pedonale": "#8E7CC3", "Area pedonale": "#F4A261",
    "In costruzione": "#E85933", "Scalinata": "#D4A574",
    "Strada condivisa": "#C1666B", "Strada di servizio": "#5E5E5E",
    "Strada residenziale": "#25465D",
}


def _geojson_servizio_to_df(geojson: dict, dominio: str, geojson_quartieri, campo_nome="name") -> pd.DataFrame:
    """Converte un geojson di punti-servizio (sanità, istruzione, trasporto
    pubblico, eventi) in un DataFrame con dominio fisso, tipo leggibile,
    coordinate e quartiere di appartenenza. Riusa le stesse funzioni di
    geometria/point-in-polygon già definite per la sezione Economia."""
    righe = []
    for feat in geojson.get("features", []):
        p = feat.get("properties", {})
        lon, lat = _punto_rappresentativo(feat.get("geometry", {}))
        tipo = p.get("tipo", "") or ""
        righe.append({
            "id": p.get("id"), "nome": p.get(campo_nome) or "—",
            "dominio": dominio,
            "tipo": _etichetta_sottocategoria(tipo) if tipo else dominio,
            "quartiere": _assegna_quartiere(lon, lat, geojson_quartieri),
            "lat": lat, "lon": lon,
        })
    return pd.DataFrame(righe)


def _geojson_parcheggi_to_df(geojson: dict, geojson_quartieri) -> pd.DataFrame:
    """Converte parcheggi_rimini.geojson: usa il tag OSM 'parking' come
    tipo (non ha un campo 'tipo' come gli altri layer Servizi) e la
    capacità dichiarata, quando presente."""
    righe = []
    for feat in geojson.get("features", []):
        p = feat.get("properties", {})
        lon, lat = _punto_rappresentativo(feat.get("geometry", {}))
        parking = p.get("parking", "") or ""
        capacita = p.get("capacity")
        try:
            capacita = int(capacita) if capacita not in (None, "") else None
        except ValueError:
            capacita = None
        righe.append({
            "id": p.get("id"), "nome": p.get("name") or "—",
            "dominio": "Parcheggi",
            "tipo": _ETICHETTE_PARCHEGGIO.get(parking, parking.replace("_", " ").capitalize() or "Non specificato"),
            "capacita": capacita,
            "quartiere": _assegna_quartiere(lon, lat, geojson_quartieri),
            "lat": lat, "lon": lon,
        })
    return pd.DataFrame(righe)


def _haversine_km(lon1, lat1, lon2, lat2) -> float:
    """Distanza approssimata in km tra due punti (lon, lat), formula
    dell'emisenoverso — sufficiente per sommare le lunghezze dei tratti di
    pista ciclabile, senza dipendenze geografiche aggiuntive."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _geojson_ciclabili_to_df(geojson: dict, geojson_quartieri):
    """Converte ciclabili_rimini.geojson (LineString) in due strutture:
    - un DataFrame riassuntivo (una riga per tratto: lunghezza, tipo, quartiere)
    - un DataFrame "lungo" (un vertice per riga) pronto per essere disegnato
      su mappa con `linea_mappa` (line_group per tratto).
    Il quartiere di un tratto è assegnato in base al suo punto medio."""
    righe_tratti, righe_vertici = [], []
    for i, feat in enumerate(geojson.get("features", [])):
        p = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates") or []
        if len(coords) < 2:
            continue
        lunghezza = sum(
            _haversine_km(coords[j][0], coords[j][1], coords[j + 1][0], coords[j + 1][1])
            for j in range(len(coords) - 1)
        )
        lon_medio, lat_medio = coords[len(coords) // 2]
        highway = p.get("highway", "") or ""
        tipo = _ETICHETTE_CICLABILE.get(highway, highway.replace("_", " ").capitalize() or "Non specificato")
        quartiere = _assegna_quartiere(lon_medio, lat_medio, geojson_quartieri)
        righe_tratti.append({
            "id": p.get("id") or i, "nome": p.get("name") or "—",
            "tipo": tipo, "lunghezza_km": lunghezza, "quartiere": quartiere,
        })
        for lon, lat in coords:
            righe_vertici.append({"tratto_id": p.get("id") or i, "tipo": tipo, "lat": lat, "lon": lon})
    return pd.DataFrame(righe_tratti), pd.DataFrame(righe_vertici)


@st.cache_data
def carica_dati_servizi(_geojson_quartieri):
    """Carica i 6 layer geojson reali (OSM + Comune di Rimini) della
    sezione Servizi: sanità, istruzione, trasporto pubblico, eventi e
    cultura, parcheggi (tutti punti) e rete ciclabile (linee, gestita a
    parte per via della geometria diversa).

    TODO: DATO REALE — l'indice di accessibilità sintetico e i dati sulla
    frequenza del trasporto pubblico non sono coperti da questi layer OSM;
    andrebbero integrati con fonti comunali/regionali se necessario.
    """
    mancanti = []
    frame_punti = []
    _geojson_quartieri = _prepara_indice_quartieri(_geojson_quartieri)

    def _leggi(chiave):
        path = SERVIZI_FILES[chiave]
        if not path.exists():
            mancanti.append(path.name)
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    gj = _leggi("sanita")
    if gj is not None:
        frame_punti.append(_geojson_servizio_to_df(gj, "Sanità", _geojson_quartieri))
    gj = _leggi("istruzione")
    if gj is not None:
        frame_punti.append(_geojson_servizio_to_df(gj, "Istruzione", _geojson_quartieri))
    gj = _leggi("trasporto")
    if gj is not None:
        frame_punti.append(_geojson_servizio_to_df(gj, "Trasporto pubblico", _geojson_quartieri))
    gj = _leggi("eventi")
    if gj is not None:
        frame_punti.append(_geojson_servizio_to_df(gj, "Eventi e cultura", _geojson_quartieri, campo_nome="nome"))
    gj = _leggi("parcheggi")
    parcheggi = _geojson_parcheggi_to_df(gj, _geojson_quartieri) if gj is not None else pd.DataFrame()
    if gj is not None:
        frame_punti.append(parcheggi.drop(columns=["capacita"]))

    gj = _leggi("ciclabili")
    ciclabili_tratti, ciclabili_vertici = (
        _geojson_ciclabili_to_df(gj, _geojson_quartieri) if gj is not None else (pd.DataFrame(), pd.DataFrame())
    )

    punti = pd.concat(frame_punti, ignore_index=True) if frame_punti else pd.DataFrame()
    return {
        "punti": punti, "parcheggi": parcheggi,
        "ciclabili_tratti": ciclabili_tratti, "ciclabili_vertici": ciclabili_vertici,
    }, mancanti


# ══════════════════════════════════════════════════════════════════════════
# DATI — SEZIONE TERRITORIO (placeholder, solo parte "Analisi per quartiere")
# ══════════════════════════════════════════════════════════════════════════
# Quartieri/frazioni di Rimini monitorati dal Digital Twin.
# DATO REALE — elenco ufficiale delle 12 zone censuarie/circoscrizioni usate
# dai layer cartografici del Digital Twin (quartieri_rimini.geojson), con i
# colori associati a ciascuna zona già presenti nel dataset.
QUARTIERI = [
    "Zona Nord - mare", "Zona Nord - monte", "Centro storico",
    "San Giuliano Celle", "Borgo Mazzini", "Colonnella",
    "Borgo S.Giovanni - Lagomaggio", "Marina centro", "Zona Sud - Mare",
    "Ghetto Turco", "Marecchiese", "Zona Sud - monte",
]

ANNI = list(range(2015, 2025))

QUARTIERE_COLORS = dict(zip(
    QUARTIERI,
    ["#25465D", "#2E86AB", "#4FC3F7", "#00A878", "#F4A261", "#E85933",
     "#8E7CC3", "#5E5E5E", "#45B7D1", "#C1666B", "#7A9E7E", "#D4A574"],
))


def _genera_dati_placeholder():
    rng = np.random.default_rng(42)

    righe = []
    for q in QUARTIERI:
        superficie = round(rng.uniform(1.2, 9.5), 2)
        righe.append({
            "quartiere": q, "superficie_kmq": superficie,
            "aree_verdi_pct": round(rng.uniform(8, 45), 1),
            "suolo_impermeabilizzato_pct": round(rng.uniform(25, 78), 1),
            "edifici_totali": int(rng.integers(400, 6000)),
        })
    territorio = pd.DataFrame(righe)

    righe = []
    consumo_base = rng.uniform(0.5, 2.5)
    for anno in ANNI:
        righe.append({"anno": anno, "consumo_suolo_ha": round(consumo_base + rng.normal(0, 0.15), 2)})
    consumo_suolo = pd.DataFrame(righe)

    return {
        "territorio": territorio,
        "consumo_suolo": consumo_suolo,
    }


@st.cache_data
def carica_dati():
    try:
        return _genera_dati_placeholder()
    except Exception as e:
        st.error(f"Errore nel caricamento dati: {e}")
        return None




def render_caso(key_prefix: str):
    """Entry point chiamato da cases.py."""
    dati = carica_dati()
    dati_ambiente, file_ambiente_mancanti = carica_dati_ambiente()
    dati_popolazione, file_popolazione_mancanti = carica_dati_popolazione()
    dati_economia, file_economia_mancanti = carica_dati_economia(
        (dati_popolazione or {}).get("geojson_quartieri")
    )
    dati_servizi, file_servizi_mancanti = carica_dati_servizi(
        (dati_popolazione or {}).get("geojson_quartieri")
    )

    # ── NAVIGAZIONE + FILTRI (nella dashboard originale erano in sidebar) ────
    SEZIONI = ["Popolazione", "Economia", "Territorio", "Servizi"]
    SOTTOTITOLO_SEZIONE = {
        "Popolazione": "Demografia e struttura per quartiere",
        "Economia": "Esercizi commerciali, negozi e uffici sul territorio",
        "Territorio": "Ambiente, uso del suolo e consumo di suolo",
        "Servizi": "Sanità, istruzione, mobilità e cultura sul territorio",
    }

    col_nav, col_filtro = st.columns([3, 2], gap="large")
    with col_nav:
        st.markdown('<p class="section-label">Sezioni</p>', unsafe_allow_html=True)
        sezione = st.radio(
            "Sezioni", options=SEZIONI, horizontal=True,
            label_visibility="collapsed", key=f"{key_prefix}_dt_sezione",
        )
    with col_filtro:
        st.markdown('<p class="section-label">Quartiere / frazione</p>', unsafe_allow_html=True)
        quartiere_sel = st.multiselect(
            "Quartiere", options=QUARTIERI, placeholder="Tutti i quartieri",
            label_visibility="collapsed", key=f"{key_prefix}_dt_quartiere",
        )
    st.markdown(
        f'<p style="font-size:0.82rem;color:#34465A;margin:0.2rem 0 0.6rem 0;">'
        f'{sezione} · {SOTTOTITOLO_SEZIONE[sezione]}</p>',
        unsafe_allow_html=True,
    )

    # ── FILTRAGGIO DATI SOCIO-ECONOMICI ──────────────────────────────────────────
    if dati is not None:
        quartieri_attivi = quartiere_sel if quartiere_sel else QUARTIERI

        territorio_f = dati["territorio"][dati["territorio"]["quartiere"].isin(quartieri_attivi)]
        consumo_suolo_f = dati["consumo_suolo"]
    else:
        quartieri_attivi = quartiere_sel if quartiere_sel else QUARTIERI
        territorio_f = consumo_suolo_f = None

    if dati_popolazione is not None and dati_popolazione.get("quartieri") is not None:
        popolazione_f = dati_popolazione["quartieri"][
            dati_popolazione["quartieri"]["quartiere"].isin(quartieri_attivi)
        ]
        sezioni_f = (
            dati_popolazione["sezioni"][dati_popolazione["sezioni"]["quartiere"].isin(quartieri_attivi)]
            if dati_popolazione.get("sezioni") is not None else None
        )
    else:
        popolazione_f = None
        sezioni_f = None

    if dati_economia is not None and len(dati_economia) > 0:
        economia_f = dati_economia[
            dati_economia["quartiere"].isin(quartieri_attivi) | dati_economia["quartiere"].isna()
        ]
    else:
        economia_f = None

    if dati_servizi is not None and dati_servizi.get("punti") is not None and len(dati_servizi["punti"]) > 0:
        servizi_f = dati_servizi["punti"][
            dati_servizi["punti"]["quartiere"].isin(quartieri_attivi) | dati_servizi["punti"]["quartiere"].isna()
        ]
    else:
        servizi_f = None

    if dati_servizi is not None and dati_servizi.get("parcheggi") is not None and len(dati_servizi["parcheggi"]) > 0:
        parcheggi_f = dati_servizi["parcheggi"][
            dati_servizi["parcheggi"]["quartiere"].isin(quartieri_attivi) | dati_servizi["parcheggi"]["quartiere"].isna()
        ]
    else:
        parcheggi_f = None

    if dati_servizi is not None and dati_servizi.get("ciclabili_tratti") is not None and len(dati_servizi["ciclabili_tratti"]) > 0:
        ciclabili_tratti_f = dati_servizi["ciclabili_tratti"][
            dati_servizi["ciclabili_tratti"]["quartiere"].isin(quartieri_attivi)
            | dati_servizi["ciclabili_tratti"]["quartiere"].isna()
        ]
        ciclabili_vertici_f = dati_servizi["ciclabili_vertici"][
            dati_servizi["ciclabili_vertici"]["tratto_id"].isin(ciclabili_tratti_f["id"])
        ]
    else:
        ciclabili_tratti_f = None
        ciclabili_vertici_f = None



    # ══════════════════════════════════════════════════════════════════════════
    # HOME — AMBIENTE (dati reali: aria, energia, meteo, uso del suolo)
    # ══════════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════════
    # POPOLAZIONE
    # ══════════════════════════════════════════════════════════════════════════
    if sezione == "Popolazione":
        st.markdown("""
    <p class="section-label">Area tematica</p>
    <p class="section-title">Popolazione: demografia e struttura per quartiere</p>
    """, unsafe_allow_html=True)

        comune = (dati_popolazione or {}).get("comune")
        anno_dato = comune.get("anno") if comune else "2023"
        st.markdown(f"""
        <div class="insight-box">
            <b>Popolazione residente</b>, <b>densità abitativa</b> e <b>struttura
            per età</b> nei 12 quartieri di Rimini, con dettaglio fino alle
            singole sezioni di censimento ISTAT.
            <br><br>
            <b>Dataset collegati:</b>
            <ul style="margin:0.4rem 0 0 0; padding-left:1.2rem;">
                <li>popolazione_rimini.geojson — totali comunali {anno_dato}</li>
                <li>quartieri_rimini.geojson — popolazione e struttura per età per quartiere (poligoni)</li>
                <li>sezioni_censimento_rimini.geojson — 73 sezioni di censimento ISTAT</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        file_pop_mancanti = [f for f in file_popolazione_mancanti] if dati_popolazione else list(POPOLAZIONE_FILES.values())
        if file_pop_mancanti:
            st.warning(
                "File dati non trovati nella cartella `data/`: "
                + ", ".join(file_pop_mancanti)
                + ". Alcuni elementi della sezione potrebbero non essere visibili."
            )

        if popolazione_f is not None and len(popolazione_f) > 0:
            col1, col2, col3, col4 = st.columns(4)
            kpi(col1, "Popolazione (quartieri sel.)", fmt(popolazione_f["popolazione"].sum()), "somma quartieri selezionati", AREA_COLORS["Popolazione"])
            kpi(col2, "Densità media", f"{fmt(popolazione_f['densita_ab_kmq'].mean(), 0)} ab/km²", "quartieri selezionati", "#2E86AB")
            kpi(col3, "Età media", fmt(popolazione_f["eta_media"].mean(), 1), "quartieri selezionati", "#4FC3F7")
            kpi(col4, "Famiglie", fmt(popolazione_f["famiglie"].sum()), "quartieri selezionati", "#F4A261")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                geojson_quartieri = dati_popolazione.get("geojson_quartieri")
                if geojson_quartieri is not None:
                    with st.spinner("Rendering della mappa dei quartieri…"):
                        figm = choropleth_mappa(
                            popolazione_f, geojson=geojson_quartieri, locations="quartiere",
                            featureidkey="properties.nome", color="popolazione",
                            color_continuous_scale=["#eaf4fc", "#25465D"],
                            hover_data={"densita_ab_kmq": True, "eta_media": True},
                            center={"lat": 44.05, "lon": 12.55}, zoom=10.5, opacity=0.8,
                        )
                    imposta_stile_mappa(figm)
                    applica_layout_mappa(figm, height=420, titolo="Popolazione residente per quartiere")
                    st.plotly_chart(figm, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Layer geografico dei quartieri non disponibile.")

            with c2:
                ordinato = popolazione_f.sort_values("popolazione", ascending=True)
                fig2 = px.bar(
                    ordinato, x="popolazione", y="quartiere", orientation="h",
                    color="quartiere", color_discrete_map=QUARTIERE_COLORS,
                    title="Popolazione residente per quartiere",
                )
                applica_layout(fig2, height=420, xaxis_title="Residenti", showlegend=False)
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            c3, c4 = st.columns(2)
            with c3:
                eta_long = popolazione_f.melt(
                    id_vars="quartiere",
                    value_vars=["eta_0_14", "eta_15_64", "eta_65_plus"],
                    var_name="fascia_eta", value_name="residenti",
                )
                eta_long["fascia_eta"] = eta_long["fascia_eta"].map({
                    "eta_0_14": "0-14 anni", "eta_15_64": "15-64 anni", "eta_65_plus": "65+ anni",
                })
                fig3 = px.bar(
                    eta_long, x="quartiere", y="residenti", color="fascia_eta",
                    barmode="stack",
                    color_discrete_map={"0-14 anni": "#4FC3F7", "15-64 anni": "#2E86AB", "65+ anni": "#25465D"},
                    title="Struttura per età per quartiere",
                )
                applica_layout(
                    fig3, height=460, yaxis_title="Residenti",
                    margin=dict(t=48, b=150, l=55, r=20),
                    legend=dict(y=-0.45),
                )
                # Titolo asse x rimosso: è ridondante con le etichette dei
                # quartieri (già ruotate) e altrimenti si sovrappone alla legenda.
                fig3.update_xaxes(tickangle=-30, title_text="")
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

            with c4:
                ultimo = popolazione_f.sort_values("densita_ab_kmq", ascending=True)
                fig4 = px.bar(
                    ultimo, x="densita_ab_kmq", y="quartiere", orientation="h",
                    color="quartiere", color_discrete_map=QUARTIERE_COLORS,
                    title="Densità abitativa per quartiere",
                )
                applica_layout(fig4, height=420, xaxis_title="Abitanti / km²", showlegend=False)
                st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            c5, c6 = st.columns(2)
            with c5:
                fig5 = px.scatter(
                    popolazione_f, x="famiglie", y="popolazione", size="densita_ab_kmq",
                    color="quartiere", color_discrete_map=QUARTIERE_COLORS,
                    title="Popolazione vs. nuclei familiari per quartiere",
                )
                applica_layout(fig5, height=400, xaxis_title="Nuclei familiari", yaxis_title="Residenti")
                st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

            with c6:
                if sezioni_f is not None and len(sezioni_f) > 0:
                    fig6 = scatter_mappa(
                        sezioni_f, lat="lat", lon="lon", color="quartiere",
                        size="pop_tot", hover_name="sezione_id",
                        hover_data={"densita_ab_kmq": True, "pop_tot": True},
                        color_discrete_map=QUARTIERE_COLORS, zoom=10.5,
                        center={"lat": 44.05, "lon": 12.55},
                    )
                    imposta_stile_mappa(fig6)
                    applica_layout_mappa(fig6, height=400, titolo="Sezioni di censimento ISTAT (dettaglio)")
                    st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Dato sezioni di censimento non disponibile.")
        else:
            st.info("Nessun dato disponibile per i filtri selezionati.")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════════════
    # ECONOMIA
    # ══════════════════════════════════════════════════════════════════════════
    elif sezione == "Economia":
        st.markdown("""
    <p class="section-label">Area tematica</p>
    <p class="section-title">Economia: tessuto commerciale sul territorio</p>
    """, unsafe_allow_html=True)

        st.markdown("""
    <div class="insight-box">
        Censimento degli <b>esercizi commerciali</b>, <b>uffici</b> e
        <b>botteghe artigiane</b> del territorio riminese, con il dettaglio
        della <b>grande distribuzione</b> (supermercati, centri commerciali,
        mercati) e la distribuzione per quartiere.
        <br><br>
        <b>Dataset collegati:</b>
        <ul style="margin:0.4rem 0 0 0; padding-left:1.2rem;">
            <li>commercio_rimini.geojson — grande distribuzione (supermercati, centri commerciali, mercati, grandi magazzini)</li>
            <li>imprese_rimini.geojson — negozi, uffici e attività artigiane di dettaglio (dati OpenStreetMap)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

        if file_economia_mancanti:
            st.warning(
                "File dati non trovati nella cartella `data/economia/`: "
                + ", ".join(file_economia_mancanti)
                + ". Alcuni elementi della sezione potrebbero non essere visibili."
            )

        if economia_f is not None and len(economia_f) > 0:
            n_grande_distrib = int((economia_f["macro_categoria"] == "Grande distribuzione").sum())
            macro_top = economia_f["macro_categoria"].value_counts().idxmax()
            macro_top_n = int(economia_f["macro_categoria"].value_counts().max())
            conteggio_quartieri = economia_f.dropna(subset=["quartiere"])["quartiere"].value_counts()

            col1, col2, col3, col4 = st.columns(4)
            kpi(col1, "Esercizi censiti", fmt(len(economia_f)), "negozi, uffici, artigianato e GDO", AREA_COLORS["Economia"])
            kpi(col2, "Grande distribuzione", fmt(n_grande_distrib), "supermercati, centri comm., mercati", "#25465D")
            kpi(col3, "Categoria più diffusa", macro_top, f"{fmt(macro_top_n)} esercizi", "#2E86AB")
            if len(conteggio_quartieri) > 0:
                kpi(col4, "Quartiere più commerciale", conteggio_quartieri.index[0], f"{fmt(int(conteggio_quartieri.iloc[0]))} esercizi", "#F4A261")
            else:
                kpi(col4, "Quartiere più commerciale", "—", "nessun dato di quartiere", "#F4A261")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                mappa_pts = economia_f.dropna(subset=["lat", "lon"])
                fig1 = scatter_mappa(
                    mappa_pts, lat="lat", lon="lon", color="macro_categoria",
                    hover_name="nome", hover_data={"sotto_categoria": True, "quartiere": True},
                    color_discrete_map=MACRO_CATEGORIA_COLORS, zoom=10.5,
                    center={"lat": 44.05, "lon": 12.55}, opacity=0.75,
                )
                imposta_stile_mappa(fig1)
                applica_layout_mappa(fig1, height=440, titolo="Esercizi commerciali sul territorio")
                st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

            with c2:
                per_macro = economia_f["macro_categoria"].value_counts().reset_index()
                per_macro.columns = ["macro_categoria", "esercizi"]
                fig2 = px.bar(
                    per_macro.sort_values("esercizi"), x="esercizi", y="macro_categoria", orientation="h",
                    color="macro_categoria", color_discrete_map=MACRO_CATEGORIA_COLORS,
                    title="Esercizi per macro-categoria",
                )
                applica_layout(fig2, height=440, xaxis_title="N. esercizi", showlegend=False)
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            c3, c4 = st.columns(2)
            with c3:
                top_sotto = economia_f["sotto_categoria"].value_counts().head(15).reset_index()
                top_sotto.columns = ["sotto_categoria", "esercizi"]
                fig3 = px.bar(
                    top_sotto.sort_values("esercizi"), x="esercizi", y="sotto_categoria", orientation="h",
                    color_discrete_sequence=["#2E86AB"],
                    title="Le 15 tipologie di esercizio più diffuse",
                )
                applica_layout(fig3, height=460, xaxis_title="N. esercizi")
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

            with c4:
                if len(conteggio_quartieri) > 0:
                    per_quartiere = conteggio_quartieri.reset_index()
                    per_quartiere.columns = ["quartiere", "esercizi"]
                    fig4 = px.bar(
                        per_quartiere.sort_values("esercizi", ascending=True), x="esercizi", y="quartiere", orientation="h",
                        color="quartiere", color_discrete_map=QUARTIERE_COLORS,
                        title="Esercizi commerciali per quartiere",
                    )
                    applica_layout(fig4, height=460, xaxis_title="N. esercizi", showlegend=False)
                    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Nessun esercizio associato a un quartiere per i filtri selezionati.")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            con_quartiere = economia_f.dropna(subset=["quartiere"])
            if len(con_quartiere) > 0:
                composizione = con_quartiere.groupby(["quartiere", "macro_categoria"], as_index=False).size()
                fig5 = px.bar(
                    composizione, x="quartiere", y="size", color="macro_categoria",
                    barmode="stack", color_discrete_map=MACRO_CATEGORIA_COLORS,
                    title="Composizione del tessuto commerciale per quartiere",
                )
                applica_layout(
                    fig5, height=460, yaxis_title="N. esercizi",
                    margin=dict(t=48, b=150, l=55, r=20), legend=dict(y=-0.45),
                )
                fig5.update_xaxes(tickangle=-30, title_text="")
                st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Nessun dato disponibile per i filtri selezionati.")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════════════
    # TERRITORIO
    # ══════════════════════════════════════════════════════════════════════════
    elif sezione == "Territorio":
        st.markdown("""
    <p class="section-label">Area tematica</p>
    <p class="section-title">Territorio: ambiente e uso del suolo</p>
    """, unsafe_allow_html=True)

        st.markdown("""
    <div class="insight-box">
        Panoramica ambientale del territorio di Rimini — <b>fonti di
        emissione</b> e <b>stazioni di monitoraggio dell'aria</b>,
        infrastrutture per l'<b>energia</b> (pannelli solari, colonnine di
        ricarica, centrali e cabine elettriche), <b>stazione meteo</b> di
        riferimento e composizione dell'<b>uso del suolo</b> — seguita
        dall'analisi per quartiere di <b>superficie</b>, <b>aree verdi</b> e
        <b>suolo impermeabilizzato</b>, con l'andamento storico del
        <b>consumo di suolo</b> a scala comunale.
        <br><br>
        <b>Dataset utilizzati (reali):</b>
        <ul style="margin:0.4rem 0 0 0; padding-left:1.2rem;">
            <li>aria_rimini.geojson — fonti di emissione e stazioni di monitoraggio</li>
            <li>energia_rimini.geojson — impianti e infrastrutture energetiche</li>
            <li>meteo_rimini.geojson — stazioni meteo</li>
            <li>uso_suolo_rimini.geojson — poligoni di uso del suolo</li>
        </ul>
    """, unsafe_allow_html=True)

        st.markdown("#### Ambiente: aria, energia, meteo e uso del suolo")

        if file_ambiente_mancanti:
            st.warning(
                "File mancanti nella cartella `data/ambiente/` accanto allo script: "
                + ", ".join(file_ambiente_mancanti)
                + ". Copia lì i 4 geojson per popolare questa parte della sezione."
            )

        df_aria    = dati_ambiente["aria"]["df"] if dati_ambiente.get("aria") else pd.DataFrame()
        df_energia = dati_ambiente["energia"]["df"] if dati_ambiente.get("energia") else pd.DataFrame()
        df_meteo   = dati_ambiente["meteo"]["df"] if dati_ambiente.get("meteo") else pd.DataFrame()
        df_suolo   = dati_ambiente["uso_suolo"]["df"] if dati_ambiente.get("uso_suolo") else pd.DataFrame()
        suolo_geojson = dati_ambiente["uso_suolo"]["geojson"] if dati_ambiente.get("uso_suolo") else None

        # ── KPI ambiente ─────────────────────────────────────────────────────
        n_fonti_emissione = int((df_aria["tipo"] == "fonte_emissione").sum()) if not df_aria.empty else "—"
        n_staz_aria = int((df_aria["tipo"] == "stazione_monitoraggio").sum()) if not df_aria.empty else "—"
        n_impianti_energia = int(len(df_energia)) if not df_energia.empty else "—"
        n_pannelli_solari = int((df_energia["tipo"] == "pannello_solare").sum()) if not df_energia.empty else "—"
        verde_pct = round(df_suolo["landuse"].isin(LANDUSE_VERDE).mean() * 100, 1) if not df_suolo.empty else "—"

        meteo_val = "—"
        meteo_sub = "nessuna stazione disponibile"
        if not df_meteo.empty:
            staz = df_meteo.iloc[0]
            meteo_sub = f"stazione: {staz['name']}"
            live = meteo_live(staz["lat"], staz["lon"])
            if live and live.get("temperature") is not None:
                meteo_val = f"{live['temperature']:.0f}°C"
                desc = WMO_METEO.get(int(live.get("weathercode", -1)), "")
                if desc:
                    meteo_sub = f"{staz['name']} · {desc}"
            else:
                meteo_val = "n.d."
                meteo_sub = f"{staz['name']} · dato live non disponibile"

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        kpi(col1, "Fonti di emissione", fmt(n_fonti_emissione), "monitorate sul territorio", AREA_COLORS["Territorio"])
        kpi(col2, "Stazioni qualità aria", fmt(n_staz_aria), "rete di monitoraggio", "#2E86AB")
        kpi(col3, "Impianti energetici", fmt(n_impianti_energia), "solare, ricarica, cabine, centrali", AREA_COLORS["Economia"])
        kpi(col4, "Pannelli solari", fmt(n_pannelli_solari), "censiti nel layer energia", "#F4A261")
        kpi(col5, "Superficie a verde", f"{fmt(verde_pct, 1)}%" if verde_pct != "—" else "—", "stima su n. poligoni uso suolo", "#00A878")
        kpi(col6, "Meteo in tempo reale", meteo_val, meteo_sub, "#4FC3F7")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # ── Storico meteo (ultimi 12 mesi, Open-Meteo Historical Weather API) ──
        if not df_meteo.empty:
            staz = df_meteo.iloc[0]
            storico = meteo_storico(staz["lat"], staz["lon"])
            if not storico.empty:
                st.markdown(f"""
                <div class="insight-box">
                    Andamento di <b>temperatura</b> e <b>precipitazioni</b>
                    nell'ultimo anno sulla stazione meteo "{staz['name']}",
                    da dati storici di rianalisi (Open-Meteo Historical
                    Weather API).
                </div>
                """, unsafe_allow_html=True)

                cm1, cm2 = st.columns(2)
                with cm1:
                    fig_t = px.line(
                        storico, x="data", y="temperatura_media", markers=False,
                        color_discrete_sequence=["#E85933"],
                        title="Temperatura media giornaliera — ultimi 12 mesi",
                    )
                    applica_layout(fig_t, height=380, xaxis_title="Data", yaxis_title="°C")
                    st.plotly_chart(fig_t, use_container_width=True, config={"displayModeBar": False})

                with cm2:
                    storico_mensile = storico.copy()
                    storico_mensile["mese"] = storico_mensile["data"].dt.to_period("M").dt.to_timestamp()
                    precip_mensile = storico_mensile.groupby("mese", as_index=False)["precipitazioni_mm"].sum()
                    fig_p = px.bar(
                        precip_mensile, x="mese", y="precipitazioni_mm",
                        color_discrete_sequence=["#2E86AB"],
                        title="Precipitazioni mensili — ultimi 12 mesi",
                    )
                    applica_layout(fig_p, height=380, xaxis_title="Mese", yaxis_title="mm")
                    st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})

                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            else:
                st.info("Serie storica meteo non disponibile al momento (servizio Open-Meteo non raggiungibile).")
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if not df_energia.empty:
                conteggio = df_energia["tipo"].map(TIPO_ENERGIA_LABEL).value_counts().reset_index()
                conteggio.columns = ["tipo", "numero"]
                fig = px.bar(
                    conteggio.sort_values("numero"), x="numero", y="tipo", orientation="h",
                    color="tipo", color_discrete_map=TIPO_ENERGIA_COLOR,
                    title="Infrastrutture energetiche per tipologia",
                )
                applica_layout(fig, height=380, xaxis_title="Numero di impianti", showlegend=False)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Dato energia non disponibile.")

        with c2:
            if not df_suolo.empty:
                top_landuse = df_suolo["landuse"].value_counts().head(10).reset_index()
                top_landuse.columns = ["landuse", "numero"]
                colore_landuse = df_suolo.drop_duplicates("landuse").set_index("landuse")["color"].to_dict()
                fig2 = px.bar(
                    top_landuse.sort_values("numero"), x="numero", y="landuse", orientation="h",
                    color="landuse", color_discrete_map=colore_landuse,
                    title="Uso del suolo — categorie principali (n. poligoni)",
                )
                applica_layout(fig2, height=380, xaxis_title="Numero di poligoni", showlegend=False)
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Dato uso del suolo non disponibile.")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        with c3:
            punti = []
            if not df_aria.empty:
                tmp = df_aria.copy()
                tmp["categoria"] = tmp["tipo"].map({
                    "fonte_emissione": "Fonte di emissione",
                    "stazione_monitoraggio": "Stazione qualità aria",
                }).fillna(tmp["tipo"])
                punti.append(tmp[["lat", "lon", "name", "categoria"]])
            if not df_energia.empty:
                tmp = df_energia.copy()
                tmp["categoria"] = tmp["tipo"].map(TIPO_ENERGIA_LABEL).fillna(tmp["tipo"])
                punti.append(tmp[["lat", "lon", "name", "categoria"]])
            if not df_meteo.empty:
                tmp = df_meteo.copy()
                tmp["categoria"] = "Stazione meteo"
                punti.append(tmp[["lat", "lon", "name", "categoria"]])

            if punti:
                df_mappa = pd.concat(punti, ignore_index=True)
                colori_punti = {**TIPO_ENERGIA_COLOR,
                                 "Fonte di emissione": "#E85933",
                                 "Stazione qualità aria": "#2E86AB",
                                 "Stazione meteo": "#00A878"}
                fig3 = scatter_mappa(
                    df_mappa, lat="lat", lon="lon", color="categoria", hover_name="name",
                    color_discrete_map=colori_punti, zoom=10.5,
                    center={"lat": 44.05, "lon": 12.55},
                )
                fig3.update_traces(marker=dict(size=9))
                imposta_stile_mappa(fig3)
                applica_layout_mappa(fig3, height=460, titolo="Aria, energia e meteo sul territorio")
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Nessun punto geografico disponibile.")

        with c4:
            if suolo_geojson is not None and not df_suolo.empty:
                colore_landuse = df_suolo.drop_duplicates("landuse").set_index("landuse")["color"].to_dict()
                with st.spinner("Rendering dei poligoni di uso del suolo…"):
                    fig4 = choropleth_mappa(
                        df_suolo, geojson=suolo_geojson, locations="id",
                        featureidkey="properties.id", color="landuse",
                        color_discrete_map=colore_landuse,
                        center={"lat": 44.05, "lon": 12.55}, zoom=10.5, opacity=0.75,
                    )
                imposta_stile_mappa(fig4)
                fig4.update_layout(showlegend=False)
                applica_layout_mappa(fig4, height=460, titolo="Mappa dell'uso del suolo")
                st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Dato uso del suolo non disponibile.")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════════════
    # SERVIZI
    # ══════════════════════════════════════════════════════════════════════════
    elif sezione == "Servizi":
        st.markdown("""
    <p class="section-label">Area tematica</p>
    <p class="section-title">Servizi: sanità, istruzione, mobilità e cultura</p>
    """, unsafe_allow_html=True)

        st.markdown("""
    <div class="insight-box">
        Censimento dei <b>servizi pubblici e di prossimità</b> sul territorio
        riminese: <b>sanità</b> (farmacie, cliniche, ospedali), <b>istruzione</b>
        (asili, scuole, università), <b>trasporto pubblico</b> (fermate,
        stazioni), <b>parcheggi</b>, <b>rete ciclabile</b> e <b>luoghi di
        cultura e sport</b> (teatri, cinema, stadi, palazzetti).
        <br><br>
        <b>Dataset collegati:</b>
        <ul style="margin:0.4rem 0 0 0; padding-left:1.2rem;">
            <li>ospedali_rimini.geojson — farmacie, cliniche, medici, ospedali</li>
            <li>scuole_rimini.geojson — asili, scuole, università</li>
            <li>trasporto_pubblico_rimini.geojson — fermate bus, stazioni, terminal traghetti</li>
            <li>parcheggi_rimini.geojson — parcheggi, con capacità dove nota</li>
            <li>eventi_rimini.geojson — teatri, cinema, stadi, palazzetti, centri congressi</li>
            <li>ciclabili_rimini.geojson — rete ciclabile e percorsi promiscui (linee)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

        if file_servizi_mancanti:
            st.warning(
                "File dati non trovati nella cartella `data/servizi/`: "
                + ", ".join(file_servizi_mancanti)
                + ". Alcuni elementi della sezione potrebbero non essere visibili."
            )

        if servizi_f is not None and len(servizi_f) > 0:
            n_sanita = int((servizi_f["dominio"] == "Sanità").sum())
            n_istruzione = int((servizi_f["dominio"] == "Istruzione").sum())
            n_trasporto = int((servizi_f["dominio"] == "Trasporto pubblico").sum())
            n_parcheggi = int((servizi_f["dominio"] == "Parcheggi").sum())
            n_eventi = int((servizi_f["dominio"] == "Eventi e cultura").sum())
            cap_totale = int(parcheggi_f["capacita"].dropna().sum()) if parcheggi_f is not None and not parcheggi_f.empty else 0
            km_totali = float(ciclabili_tratti_f["lunghezza_km"].sum()) if ciclabili_tratti_f is not None and not ciclabili_tratti_f.empty else 0.0

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            kpi(col1, "Sanità", fmt(n_sanita), "farmacie, cliniche, ospedali", AREA_COLORS["Servizi"])
            kpi(col2, "Istruzione", fmt(n_istruzione), "asili, scuole, università", "#2E86AB")
            kpi(col3, "Trasporto pubblico", fmt(n_trasporto), "fermate, stazioni, terminal", "#8E7CC3")
            kpi(col4, "Parcheggi", fmt(n_parcheggi), f"{fmt(cap_totale)} posti auto noti", "#5E5E5E")
            kpi(col5, "Rete ciclabile", f"{fmt(km_totali, 1)} km", "piste e percorsi mappati", "#00A878")
            kpi(col6, "Cultura e sport", fmt(n_eventi), "teatri, cinema, stadi, palazzetti", "#F4A261")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                mappa_pts = servizi_f.dropna(subset=["lat", "lon"])
                fig1 = scatter_mappa(
                    mappa_pts, lat="lat", lon="lon", color="dominio",
                    hover_name="nome", hover_data={"tipo": True, "quartiere": True},
                    color_discrete_map=SERVIZIO_DOMINIO_COLORS, zoom=10.5,
                    center={"lat": 44.05, "lon": 12.55}, opacity=0.75,
                )
                imposta_stile_mappa(fig1)
                applica_layout_mappa(fig1, height=440, titolo="Servizi sul territorio")
                st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

            with c2:
                per_dominio = servizi_f["dominio"].value_counts().reset_index()
                per_dominio.columns = ["dominio", "numero"]
                fig2 = px.bar(
                    per_dominio.sort_values("numero"), x="numero", y="dominio", orientation="h",
                    color="dominio", color_discrete_map=SERVIZIO_DOMINIO_COLORS,
                    title="Servizi per dominio",
                )
                applica_layout(fig2, height=440, xaxis_title="N. servizi", showlegend=False)
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            c3, c4 = st.columns(2)
            with c3:
                top_tipi = servizi_f["tipo"].value_counts().head(15).reset_index()
                top_tipi.columns = ["tipo", "numero"]
                fig3 = px.bar(
                    top_tipi.sort_values("numero"), x="numero", y="tipo", orientation="h",
                    color_discrete_sequence=["#2E86AB"],
                    title="Le 15 tipologie di servizio più diffuse",
                )
                applica_layout(fig3, height=460, xaxis_title="N. servizi")
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

            with c4:
                con_quartiere = servizi_f.dropna(subset=["quartiere"])
                if len(con_quartiere) > 0:
                    composizione = con_quartiere.groupby(["quartiere", "dominio"], as_index=False).size()
                    fig4 = px.bar(
                        composizione, x="quartiere", y="size", color="dominio",
                        barmode="stack", color_discrete_map=SERVIZIO_DOMINIO_COLORS,
                        title="Composizione dei servizi per quartiere",
                    )
                    applica_layout(
                        fig4, height=460, yaxis_title="N. servizi",
                        margin=dict(t=48, b=150, l=55, r=20), legend=dict(y=-0.45),
                    )
                    fig4.update_xaxes(tickangle=-30, title_text="")
                    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Nessun servizio associato a un quartiere per i filtri selezionati.")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            c5, c6 = st.columns(2)
            with c5:
                if ciclabili_vertici_f is not None and len(ciclabili_vertici_f) > 0:
                    fig5 = linea_mappa(
                        ciclabili_vertici_f, lat="lat", lon="lon", color="tipo",
                        line_group="tratto_id", color_discrete_map=CICLABILI_TIPO_COLORS,
                        zoom=10.5, center={"lat": 44.05, "lon": 12.55},
                    )
                    imposta_stile_mappa(fig5)
                    applica_layout_mappa(fig5, height=440, titolo="Rete ciclabile")
                    st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Dato rete ciclabile non disponibile per i filtri selezionati.")

            with c6:
                if ciclabili_tratti_f is not None and len(ciclabili_tratti_f) > 0:
                    km_per_tipo = ciclabili_tratti_f.groupby("tipo", as_index=False)["lunghezza_km"].sum()
                    fig6 = px.bar(
                        km_per_tipo.sort_values("lunghezza_km"), x="lunghezza_km", y="tipo", orientation="h",
                        color_discrete_sequence=["#00A878"],
                        title="Km di rete per tipologia",
                    )
                    applica_layout(fig6, height=440, xaxis_title="Km")
                    st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Dato rete ciclabile non disponibile per i filtri selezionati.")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            if popolazione_f is not None and len(popolazione_f) > 0 and len(con_quartiere) > 0:
                conteggio_quartiere = con_quartiere.groupby("quartiere", as_index=False).size()
                conteggio_quartiere.columns = ["quartiere", "n_servizi"]
                merge_pop = conteggio_quartiere.merge(
                    popolazione_f[["quartiere", "popolazione"]], on="quartiere", how="inner"
                )
                merge_pop["servizi_per_1000_ab"] = merge_pop["n_servizi"] / merge_pop["popolazione"] * 1000
                fig7 = px.bar(
                    merge_pop.sort_values("servizi_per_1000_ab", ascending=True),
                    x="servizi_per_1000_ab", y="quartiere", orientation="h",
                    color="quartiere", color_discrete_map=QUARTIERE_COLORS,
                    title="Servizi mappati ogni 1.000 abitanti, per quartiere",
                )
                applica_layout(fig7, height=440, xaxis_title="Servizi ogni 1.000 abitanti", showlegend=False)
                st.plotly_chart(fig7, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Dato insufficiente (servizi o popolazione) per calcolare l'indicatore per quartiere.")
        else:
            st.info("Nessun dato disponibile per i filtri selezionati.")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════════════
    # NOTA METODOLOGICA
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("Nota metodologica"):
        st.markdown("""
**Navigazione:** le sezioni sono selezionabili dal menu a sinistra, che organizza gli
indicatori del territorio in una barra laterale di sezioni tematiche
navigabili. L'app si apre di default sulla sezione **Popolazione**.

**Popolazione — dati reali:** questa sezione legge direttamente tre dataset
geojson (`data/popolazione/popolazione_rimini.geojson`,
`data/popolazione/quartieri_rimini.geojson`,
`data/popolazione/sezioni_censimento_rimini.geojson`). Il filtro
quartiere è attivo.

**Economia:** questa sezione legge 2 dataset geojson
(`data/economia/commercio_rimini.geojson` per la grande distribuzione,
`data/economia/imprese_rimini.geojson` per negozi/uffici/artigianato di
dettaglio). Anche qui il filtro quartiere è attivo.

**Territorio :** la prima parte della sezione legge direttamente 4
dataset geojson  (`data/ambiente/aria_rimini.geojson`,
`data/ambiente/energia_rimini.geojson`, `data/ambiente/meteo_rimini.geojson`,
`data/ambiente/uso_suolo_rimini.geojson`).  Il meteo in tempo reale usa l'API gratuita
**Open-Meteo**;
se il servizio non risponde (es. assenza di connessione), la dashboard
mostra "n.d." senza generare errori. Qui non è attivo il filtro quartiere.

**Servizi:** questa sezione legge 6 dataset geojson
(`data/servizi/ospedali_rimini.geojson`,
`scuole_rimini.geojson`, `trasporto_pubblico_rimini.geojson`,
`parcheggi_rimini.geojson`, `eventi_rimini.geojson`,
`ciclabili_rimini.geojson`). Anche qui il filtro quartiere è attivo.
""")