from pathlib import Path

import streamlit as st

# ── Immagini ─────────────────────────────────────────────────────────────────
# Link https://... oppure nome file in caso_analisi_energetica/immagini/
IMMAGINI = {
    "Mappa - Rapporto tra produzione FER comunale e consumi elettrici comunali (2015)": "immagini/",
    "Mappa - Produzione elettrica di biomasse totali regionali (2023)": "immagini/",
}


def _mostra_immagine(sorgente: str, nome: str):
    sorgente = (sorgente or "").strip()
    if sorgente.startswith(("http://", "https://")):
        st.image(sorgente, use_container_width=True)
        return
    for base in (Path(__file__).parent / "immagini", Path(__file__).parent):
        p = base / sorgente
        if sorgente and p.is_file():
            st.image(str(p), use_container_width=True)
            return
    st.markdown(f"""
    <div class="insight-box">
        <strong>Immagine non trovata:</strong> {nome}<br>
        Indica il file (in <code>immagini/</code>) o il link in <code>IMMAGINI</code>, in cima a <code>analisi_energetica.py</code>.
    </div>
    """, unsafe_allow_html=True)


def render_caso(key: str = "analisi_energetica"):
    """Punto d'ingresso: le due immagini, una sotto l'altra."""
    for nome, sorgente in IMMAGINI.items():
        st.markdown(f'<div class="section-label">{nome.upper()}</div>', unsafe_allow_html=True)
        _mostra_immagine(sorgente, nome)
