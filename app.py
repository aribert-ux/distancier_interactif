import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="Distancier", layout="wide", page_icon="🗺️")

st.title("🗺️ Distancier — Visualisation des distances")

# ─────────────────────────────────────────────
# CHARGEMENT DES DONNÉES
# ─────────────────────────────────────────────
@st.cache_data
def charger_distancier():
    df = pd.read_csv("data/distancier.csv", sep=";")
    df.columns = df.columns.str.strip()
    df["De"]   = df["De"].str.strip()
    df["Vers"] = df["Vers"].str.strip()
    return df

@st.cache_data
def charger_coordonnees():
    df = pd.read_csv("data/coordonnees.csv", sep=";")
    df.columns = df.columns.str.strip()
    df["tag"]  = df["tag"].str.strip()
    return df

df_dist  = charger_distancier()
df_coords = charger_coordonnees()

# Dictionnaire tag → (lat, lon)
coords_dict = {
    row["tag"]: (row["latitude"], row["longitude"])
    for _, row in df_coords.iterrows()
}

# Liste de tous les lieux disponibles
tous_lieux = sorted(coords_dict.keys())

# ─────────────────────────────────────────────
# ÉTAT DE SESSION
# ─────────────────────────────────────────────
if "point_a" not in st.session_state:
    st.session_state.point_a = None
if "point_b" not in st.session_state:
    st.session_state.point_b = None
if "mode_clic" not in st.session_state:
    st.session_state.mode_clic = "A"  # prochain clic pose A ou B

# ─────────────────────────────────────────────
# SIDEBAR — SÉLECTION PAR LISTE
# ─────────────────────────────────────────────
st.sidebar.header("🔍 Sélection par liste")

st.sidebar.markdown("**Point A**")
choix_a = st.sidebar.selectbox(
    "Rechercher le point A",
    options=["— Choisir —"] + tous_lieux,
    key="select_a"
)

st.sidebar.markdown("**Point B**")
choix_b = st.sidebar.selectbox(
    "Rechercher le point B",
    options=["— Choisir —"] + tous_lieux,
    key="select_b"
)

if st.sidebar.button("✅ Valider la sélection par liste"):
    if choix_a != "— Choisir —":
        st.session_state.point_a = choix_a
    if choix_b != "— Choisir —":
        st.session_state.point_b = choix_b

st.sidebar.divider()

# ─────────────────────────────────────────────
# SIDEBAR — MODE CLIC CARTE
# ─────────────────────────────────────────────
st.sidebar.header("📍 Sélection par clic sur la carte")
st.sidebar.markdown(
    "Cliquez sur un lieu sur la carte pour le sélectionner comme **Point A** puis **Point B**."
)

mode = st.sidebar.radio(
    "Prochain clic sur la carte =",
    options=["Point A", "Point B"],
    index=0 if st.session_state.mode_clic == "A" else 1,
    key="radio_mode"
)
st.session_state.mode_clic = "A" if mode == "Point A" else "B"

st.sidebar.divider()

# Affichage des points sélectionnés
st.sidebar.subheader("📌 Points sélectionnés")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.markdown(f"**A :** {st.session_state.point_a or '—'}")
with col2:
    st.markdown(f"**B :** {st.session_state.point_b or '—'}")

if st.sidebar.button("🔄 Réinitialiser"):
    st.session_state.point_a = None
    st.session_state.point_b = None
    st.rerun()

# ─────────────────────────────────────────────
# CARTE FOLIUM
# ─────────────────────────────────────────────
centre_lat = 50.2
centre_lon = 2.8
zoom_depart = 8

m = folium.Map(location=[centre_lat, centre_lon], zoom_start=zoom_depart, tiles="OpenStreetMap")

# Ajouter tous les lieux comme marqueurs cliquables (petits cercles)
for tag, (lat, lon) in coords_dict.items():
    # Couleur selon sélection
    if tag == st.session_state.point_a and tag == st.session_state.point_b:
        color = "purple"
        radius = 8
    elif tag == st.session_state.point_a:
        color = "blue"
        radius = 8
    elif tag == st.session_state.point_b:
        color = "red"
        radius = 8
    else:
        color = "gray"
        radius = 5

    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        tooltip=tag,
        popup=folium.Popup(f"<b>{tag}</b>", max_width=200),
    ).add_to(m)

# Ligne entre A et B si les deux sont sélectionnés
if st.session_state.point_a and st.session_state.point_b:
    coord_a = coords_dict.get(st.session_state.point_a)
    coord_b = coords_dict.get(st.session_state.point_b)
    if coord_a and coord_b:
        folium.PolyLine(
            locations=[coord_a, coord_b],
            color="orange",
            weight=3,
            opacity=0.8,
            tooltip="Trajet A → B"
        ).add_to(m)

# ─────────────────────────────────────────────
# AFFICHAGE CARTE + GESTION DU CLIC
# ─────────────────────────────────────────────
st.subheader("🗺️ Carte interactive")
st.caption(
    "💡 Cliquez sur un point de la carte pour le sélectionner. "
    "Choisissez d'abord si le clic pose le **Point A** ou le **Point B** dans le menu à gauche."
)

carte_data = st_folium(m, width="100%", height=550, returned_objects=["last_object_clicked_tooltip"])

# Traitement du clic sur la carte
if carte_data and carte_data.get("last_object_clicked_tooltip"):
    lieu_clique = carte_data["last_object_clicked_tooltip"]
    if lieu_clique in coords_dict:
        if st.session_state.mode_clic == "A":
            if st.session_state.point_a != lieu_clique:
                st.session_state.point_a = lieu_clique
                st.rerun()
        else:
            if st.session_state.point_b != lieu_clique:
                st.session_state.point_b = lieu_clique
                st.rerun()

# ─────────────────────────────────────────────
# RÉSULTAT — DISTANCE ET TEMPS
# ─────────────────────────────────────────────
st.divider()
st.subheader("📊 Résultat")

point_a = st.session_state.point_a
point_b = st.session_state.point_b

if point_a and point_b:
    if point_a == point_b:
        st.info("ℹ️ Les deux points sont identiques. Distance = 0 km, Temps = 0 min.")
    else:
        # Chercher dans le distancier (A → B ou B → A)
        ligne = df_dist[
            ((df_dist["De"] == point_a) & (df_dist["Vers"] == point_b)) |
            ((df_dist["De"] == point_b) & (df_dist["Vers"] == point_a))
        ]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🔵 Point A", point_a)
        with col2:
            st.metric("🔴 Point B", point_b)
        with col3:
            if not ligne.empty:
                km      = ligne.iloc[0]["Km"]
                minutes = ligne.iloc[0]["Minutes"]
                heures  = minutes // 60
                mins    = minutes % 60
                duree_str = f"{heures}h{mins:02d}" if heures > 0 else f"{mins} min"
                st.metric("📏 Distance", f"{km} km")
                st.metric("⏱️ Durée estimée", duree_str)
            else:
                st.warning("⚠️ Aucune donnée disponible pour ce trajet dans le distancier.")

        # Tableau détaillé si plusieurs lignes (doublons A→B et B→A)
        if not ligne.empty and len(ligne) > 1:
            with st.expander("📋 Voir toutes les lignes correspondantes"):
                st.dataframe(ligne, use_container_width=True)

else:
    st.info("👆 Sélectionnez un **Point A** et un **Point B** pour afficher la distance.")

# ─────────────────────────────────────────────
# TABLEAU DE TOUTES LES DISTANCES DEPUIS A
# ─────────────────────────────────────────────
if point_a:
    st.divider()
    with st.expander(f"📋 Toutes les distances depuis **{point_a}**"):
        df_depuis_a = df_dist[df_dist["De"] == point_a].sort_values("Km")
        st.dataframe(df_depuis_a, use_container_width=True, height=300)
