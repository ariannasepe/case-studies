from pathlib import Path

import streamlit as st

# ── Immagini ─────────────────────────────────────────────────────────────────
# Link https://... oppure nome file in caso_rappresentazioni/immagini/
IMMAGINI = {
    "City - Bari": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Bari.png",
    "City - Bologna": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Bologna.png",
    "City - Cagliari": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Cagliari.png",
    "City - Catania": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Catania.png",
    "City - Firenze": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Firenze.png",
    "City - Genova": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Genova.png",
    "City - Messina": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Messina.png",
    "City - Milano": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Milano.png",
    "City - Napoli": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Napoli.png",
    "City - Palermo": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Palermo.png",
    "City - Reggio Calabria": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Reggio_Calabria.png",
    "City - Roma": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Roma.png",
    "City - Torino": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Torino.png",
    "City - Venezia": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/city/Venezia.png",

    "Street - Bari": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Bari_street.png",
    "Street - Bologna": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Bologna_street.png",
    "Street - Cagliari": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Cagliari_street.png",
    "Street - Catania": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Catania_street.png",
    "Street - Firenze": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Firenze_street.png",
    "Street - Genova": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Genova_street.png",
    "Street - Messina": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Messina_street.png",
    "Street - Milano": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Milano_street.png",
    "Street - Napoli": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Napoli_street.png",
    "Street - Palermo": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Palermo_street.png",
    "Street - Reggio Calabria": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Reggio_Calabria_street.png",
    "Street - Roma": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Roma_street.png",
    "Street - Torino": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Torino_street.png",
    "Street - Venezia": "https://pub-b89a9f244d3b4a3d9a1385478a18203c.r2.dev/rappresentazioni-grafiche-delle-citta-italiane/street/Venezia_street.png",
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
        Indica il file (in <code>immagini/</code>) o il link in <code>IMMAGINI</code>, in cima a <code>rappresentazioni.py</code>.
    </div>
    """, unsafe_allow_html=True)


def render_caso(key: str = "rappresentazioni"):
    """Punto d'ingresso: per ogni città, City e Street affiancate."""
    citta = [k.split(" - ", 1)[1] for k in IMMAGINI if k.startswith("City - ")]

    for c in citta:
        st.markdown(f'<div class="section-label">{c.upper()}</div>', unsafe_allow_html=True)
        col_city, col_street = st.columns(2)

        with col_city:
            st.caption("City")
            _mostra_immagine(IMMAGINI.get(f"City - {c}", ""), f"City - {c}")

        with col_street:
            st.caption("Street")
            _mostra_immagine(IMMAGINI.get(f"Street - {c}", ""), f"Street - {c}")