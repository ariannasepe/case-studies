"""
Caso studio: Monitoraggio ambientale.

"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ── Mappe ────────────────────────────────────────────────────────────────────
MAPPE = {
    "Dashboard monitoraggio ambientale": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/montoraggio-ambientale/dashboard_v2%20(1).html", 
}
MAPPA_ALTEZZA = 750  # altezza in pixel


@st.cache_data(show_spinner="Carico la mappa…")
def _leggi_html(percorso: str, mtime: float) -> str:
    return Path(percorso).read_text(encoding="utf-8")


def _mostra_mappa(sorgente: str, nome: str):
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
        Indica il file (in <code>caso_/mappe/</code>) o il link in <code>MAPPE</code>, in cima a <code>smonitoraggio.py</code>.
    </div>
    """, unsafe_allow_html=True)


def render_caso(key: str = "monitoraggio"):
    """Punto d'ingresso: le due mappe, una sotto l'altra."""
    for nome, sorgente in MAPPE.items():
        st.markdown(f'<div class="section-label">{nome.upper()}</div>', unsafe_allow_html=True)
        _mostra_mappa(sorgente, nome)