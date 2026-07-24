import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ─────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Distancier Auchan",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Distancier Auchan — Carte interactive")
st.markdown(
    "Sélectionnez deux points et visualisez le trajet sur la carte. "
    "**Point A** et **Point B** peuvent être un entrepôt ou un magasin."
)

# ─────────────────────────────────────────────
# CHARGEMENT DES DONNÉES
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data/distancier.csv", sep=";")
    df.columns = df.columns.str.strip()
    df["De"]      = df["De"].str.strip()
    df["Vers"]    = df["Vers"].str.strip()
    df["Km"]      = pd.to_numeric(df["Km"],      errors="coerce")
    df["Minutes"] = pd.to_numeric(df["Minutes"], errors="coerce")
    return df

@st.cache_data
def load_coordinates():
    coords_df = pd.read_csv("data/coordonnees.csv", sep=";")
    coords_df.columns = coords_df.columns.str.strip()
    coords_df["tag"]       = coords_df["tag"].str.strip()
    coords_df["latitude"]  = pd.to_numeric(coords_df["latitude"],  errors="coerce")
    coords_df["longitude"] = pd.to_numeric(coords_df["longitude"], errors="coerce")
    coords = dict(zip(coords_df["tag"], zip(coords_df["latitude"], coords_df["longitude"])))
    return coords

df     = load_data()
coords = load_coordinates()

# ─────────────────────────────────────────────
# LISTES DE LIEUX
# ─────────────────────────────────────────────
tous_lieux   = sorted(set(df["De"].unique()) | set(df["Vers"].unique()))
entrepots    = sorted([l for l in tous_lieux if l.startswith("ENT")])
magasins     = sorted([l for l in tous_lieux if not l.startswith("ENT")])

entrepots_ok = [e for e in entrepots if e in coords]
magasins_ok  = [m for m in magasins  if m in coords]
tous_ok      = sorted([l for l in tous_lieux if l in coords])

# ─────────────────────────────────────────────
# SESSION STATE — initialisation
# ─────────────────────────────────────────────
if "point_a" not in st.session_state:
    st.session_state.point_a = entrepots_ok[0] if entrepots_ok else tous_ok[0]
if "point_b" not in st.session_state:
    st.session_state.point_b = magasins_ok[0] if magasins_ok else tous_ok[0]
if "mode_carte" not in st.session_state:
    st.session_state.mode_carte = None
if "type_a" not in st.session_state:
    st.session_state.type_a = "🏭 Entrepôt (ENT)"
if "type_b" not in st.session_state:
    st.session_state.type_b = "🏪 Magasin / Drive"
# Clé pour forcer le reset des selectbox sans conflit
if "last_clicked" not in st.session_state:
    st.session_state.last_clicked = None

# ─────────────────────────────────────────────
# SIDEBAR — POINT A
# ─────────────────────────────────────────────
st.sidebar.header("📍 Sélection des points")
st.sidebar.markdown("### Point A")

type_a_new = st.sidebar.radio(
    "Type Point A",
    options=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"],
    index=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"].index(
        st.session_state.type_a
    ),
    key="radio_type_a"
)
if type_a_new != st.session_state.type_a:
    st.session_state.type_a = type_a_new
    if st.session_state.mode_carte == "A":
        st.session_state.mode_carte = None

# Liste filtrée pour A
if st.session_state.type_a == "🏭 Entrepôt (ENT)":
    liste_a = entrepots_ok
elif st.session_state.type_a == "🏪 Magasin / Drive":
    liste_a = magasins_ok
else:
    liste_a = tous_ok

# Sécurité : point_a doit être dans liste_a
if st.session_state.point_a not in liste_a:
    st.session_state.point_a = liste_a[0] if liste_a else tous_ok[0]

# ── Selectbox A : on lit la valeur SANS la stocker via key= ──
idx_a = liste_a.index(st.session_state.point_a) if st.session_state.point_a in liste_a else 0
point_a_select = st.sidebar.selectbox(
    "📍 Point A — liste",
    options=liste_a,
    index=idx_a,
    key="select_a"
)

# Mise à jour depuis selectbox uniquement si pas en mode carte A
if st.session_state.mode_carte != "A":
    st.session_state.point_a = point_a_select

# ── Boutons mode carte A ──
col_a1, col_a2 = st.sidebar.columns(2)
with col_a1:
    label_btn_a = "✅ Mode actif" if st.session_state.mode_carte == "A" else "🗺️ Pointer A"
    if st.button(label_btn_a, key="btn_carte_a", use_container_width=True):
        st.session_state.mode_carte = None if st.session_state.mode_carte == "A" else "A"
        st.rerun()
with col_a2:
    if st.session_state.mode_carte == "A":
        if st.button("❌ Annuler", key="btn_cancel_a", use_container_width=True):
            st.session_state.mode_carte = None
            st.rerun()

if st.session_state.mode_carte == "A":
    st.sidebar.info("🖱️ Cliquez sur un point de la carte pour définir le **Point A**.")

st.sidebar.markdown("---")

# ─────────────────────────────────────────────
# SIDEBAR — POINT B
# ─────────────────────────────────────────────
st.sidebar.markdown("### Point B")

type_b_new = st.sidebar.radio(
    "Type Point B",
    options=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"],
    index=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"].index(
        st.session_state.type_b
    ),
    key="radio_type_b"
)
if type_b_new != st.session_state.type_b:
    st.session_state.type_b = type_b_new
    if st.session_state.mode_carte == "B":
        st.session_state.mode_carte = None

# Liste filtrée pour B
if st.session_state.type_b == "🏭 Entrepôt (ENT)":
    liste_b = entrepots_ok
elif st.session_state.type_b == "🏪 Magasin / Drive":
    liste_b = magasins_ok
else:
    liste_b = tous_ok

if st.session_state.point_b not in liste_b:
    st.session_state.point_b = liste_b[0] if liste_b else tous_ok[0]

idx_b = liste_b.index(st.session_state.point_b) if st.session_state.point_b in liste_b else 0
point_b_select = st.sidebar.selectbox(
    "📍 Point B — liste",
    options=liste_b,
    index=idx_b,
    key="select_b"
)

if st.session_state.mode_carte != "B":
    st.session_state.point_b = point_b_select

# ── Boutons mode carte B ──
col_b1, col_b2 = st.sidebar.columns(2)
with col_b1:
    label_btn_b = "✅ Mode actif" if st.session_state.mode_carte == "B" else "🗺️ Pointer B"
    if st.button(label_btn_b, key="btn_carte_b", use_container_width=True):
        st.session_state.mode_carte = None if st.session_state.mode_carte == "B" else "B"
        st.rerun()
with col_b2:
    if st.session_state.mode_carte == "B":
        if st.button("❌ Annuler", key="btn_cancel_b", use_container_width=True):
            st.session_state.mode_carte = None
            st.rerun()

if st.session_state.mode_carte == "B":
    st.sidebar.info("🖱️ Cliquez sur un point de la carte pour définir le **Point B**.")

# ─────────────────────────────────────────────
# LECTURE DES POINTS (après toute la sidebar)
# ─────────────────────────────────────────────
point_a = st.session_state.point_a
point_b = st.session_state.point_b

# ─────────────────────────────────────────────
# BANNIÈRE MODE ACTIF
# ─────────────────────────────────────────────
if st.session_state.mode_carte == "A":
    st.warning(f"🗺️ **Mode sélection carte — Point A** | Seuls les points *{st.session_state.type_a}* sont affichés. Cliquez sur un marqueur.")
elif st.session_state.mode_carte == "B":
    st.warning(f"🗺️ **Mode sélection carte — Point B** | Seuls les points *{st.session_state.type_b}* sont affichés. Cliquez sur un marqueur.")

# ─────────────────────────────────────────────
# DISTANCE
# ─────────────────────────────────────────────
def get_distance(df, origine, destination):
    row = df[
        ((df["De"] == origine)     & (df["Vers"] == destination)) |
        ((df["De"] == destination) & (df["Vers"] == origine))
    ]
    if not row.empty:
        return row.iloc[0]["Km"], row.iloc[0]["Minutes"]
    return None, None

km, minutes = get_distance(df, point_a, point_b)

# ─────────────────────────────────────────────
# MÉTRIQUES
# ─────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info(f"**📍 Point A**\n\n{point_a}")
with col2:
    st.info(f"**📍 Point B**\n\n{point_b}")
with col3:
    if km is not None:
        st.success(f"**📏 Distance**\n\n{km:.1f} km")
    else:
        st.warning("**📏 Distance**\n\nNon disponible")
with col4:
    if minutes is not None:
        heures    = int(minutes) // 60
        mins      = int(minutes) % 60
        duree_str = f"{heures}h{mins:02d}" if heures > 0 else f"{int(mins)} min"
        st.success(f"**⏱️ Durée**\n\n{duree_str} ({int(minutes)} min)")
    else:
        st.warning("**⏱️ Durée**\n\nNon disponible")

st.markdown("---")

# ─────────────────────────────────────────────
# CONSTRUCTION DE LA CARTE
# ─────────────────────────────────────────────
lat_a, lon_a = coords.get(point_a, (None, None))
lat_b, lon_b = coords.get(point_b, (None, None))

if lat_a and lat_b:
    centre_lat = (lat_a + lat_b) / 2
    centre_lon = (lon_a + lon_b) / 2
elif lat_a:
    centre_lat, centre_lon = lat_a, lon_a
else:
    centre_lat, centre_lon = 50.0, 2.5

m = folium.Map(
    location=[centre_lat, centre_lon],
    zoom_start=7,
    tiles="CartoDB positron"
)

# ── Points visibles selon le mode ──
mode_carte = st.session_state.mode_carte

if mode_carte == "A":
    if st.session_state.type_a == "🏭 Entrepôt (ENT)":
        afficher_entrepots = entrepots_ok
        afficher_magasins  = []
    elif st.session_state.type_a == "🏪 Magasin / Drive":
        afficher_entrepots = []
        afficher_magasins  = magasins_ok
    else:
        afficher_entrepots = entrepots_ok
        afficher_magasins  = magasins_ok
elif mode_carte == "B":
    if st.session_state.type_b == "🏭 Entrepôt (ENT)":
        afficher_entrepots = entrepots_ok
        afficher_magasins  = []
    elif st.session_state.type_b == "🏪 Magasin / Drive":
        afficher_entrepots = []
        afficher_magasins  = magasins_ok
    else:
        afficher_entrepots = entrepots_ok
        afficher_magasins  = magasins_ok
else:
    afficher_entrepots = entrepots_ok
    afficher_magasins  = magasins_ok

# ── Tracé des cercles ──
for ent in afficher_entrepots:
    lat, lon = coords[ent]
    is_selected = (ent == point_a or ent == point_b)
    folium.CircleMarker(
        location=[lat, lon],
        radius=9 if is_selected else 6,
        color="#1565C0",
        fill=True,
        fill_color="#1E88E5",
        fill_opacity=1.0 if is_selected else 0.7,
        tooltip=ent,          # ← tooltip = nom exact du tag
        popup=folium.Popup(f"<b>🏭 {ent}</b>", max_width=250)
    ).add_to(m)

for mag in afficher_magasins:
    lat, lon = coords[mag]
    is_selected = (mag == point_a or mag == point_b)
    folium.CircleMarker(
        location=[lat, lon],
        radius=8 if is_selected else 5,
        color="#2E7D32",
        fill=True,
        fill_color="#43A047",
        fill_opacity=1.0 if is_selected else 0.6,
        tooltip=mag,          # ← tooltip = nom exact du tag
        popup=folium.Popup(f"<b>🏪 {mag}</b>", max_width=250)
    ).add_to(m)

# ── Marqueurs A et B ──
if lat_a:
    folium.Marker(
        location=[lat_a, lon_a],
        tooltip=f"📍 A — {point_a}",
        popup=folium.Popup(f"<b>📍 POINT A</b><br>{point_a}", max_width=300),
        icon=folium.Icon(
            color="blue" if point_a.startswith("ENT") else "green",
            icon="industry" if point_a.startswith("ENT") else "shopping-cart",
            prefix="fa"
        )
    ).add_to(m)

if lat_b and point_b != point_a:
    folium.Marker(
        location=[lat_b, lon_b],
        tooltip=f"📍 B — {point_b}",
        popup=folium.Popup(f"<b>📍 POINT B</b><br>{point_b}", max_width=300),
        icon=folium.Icon(
            color="blue" if point_b.startswith("ENT") else "green",
            icon="industry" if point_b.startswith("ENT") else "shopping-cart",
            prefix="fa"
        )
    ).add_to(m)

# ── Trait A → B ──
if lat_a and lat_b and point_a != point_b:
    duree_str = ""
    label     = ""
    if km is not None and minutes is not None:
        heures    = int(minutes) // 60
        mins      = int(minutes) % 60
        duree_str = f"{heures}h{mins:02d}" if heures > 0 else f"{int(mins)} min"
        label     = f"{km:.1f} km — {duree_str}"

    folium.PolyLine(
        locations=[[lat_a, lon_a], [lat_b, lon_b]],
        color="#E53935",
        weight=4,
        opacity=0.9,
        tooltip=label
    ).add_to(m)

    if km is not None:
        mid_lat = (lat_a + lat_b) / 2
        mid_lon = (lon_a + lon_b) / 2
        folium.Marker(
            location=[mid_lat, mid_lon],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    background-color:#E53935;color:white;
                    padding:5px 10px;border-radius:12px;
                    font-size:12px;font-weight:bold;
                    white-space:nowrap;
                    box-shadow:2px 2px 6px rgba(0,0,0,0.4);
                ">
                    📏 {km:.1f} km &nbsp;|&nbsp; ⏱️ {duree_str}
                </div>
                """,
                icon_size=(220, 34),
                icon_anchor=(110, 17)
            )
        ).add_to(m)

# ── Légende ──
legend_html = """
<div style="
    position:fixed;bottom:30px;left:30px;
    background-color:white;border:2px solid #ccc;
    border-radius:8px;padding:10px 14px;
    font-size:13px;z-index:1000;
    box-shadow:2px 2px 6px rgba(0,0,0,0.2);
">
    <b>Légende</b><br>
    <span style="color:#1E88E5;">●</span> Entrepôt (ENT)<br>
    <span style="color:#43A047;">●</span> Magasin / Drive<br>
    <span style="color:#E53935;">—</span> Trajet sélectionné
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ─────────────────────────────────────────────
# AFFICHAGE CARTE — retourne le clic
# ─────────────────────────────────────────────
carte_result = st_folium(
    m,
    width="100%",
    height=600,
    returned_objects=["last_object_clicked_tooltip", "last_object_clicked"]
)

# ─────────────────────────────────────────────
# TRAITEMENT DU CLIC — APRÈS affichage carte
# ─────────────────────────────────────────────
if mode_carte in ("A", "B") and carte_result:

    # Récupération du tooltip cliqué (méthode principale)
    clicked = carte_result.get("last_object_clicked_tooltip")

    # Fallback : si tooltip vide, on ignore
    if not clicked:
        clicked = None

    # Vérification que le tag cliqué existe dans les coordonnées
    liste_autorisee = afficher_entrepots + afficher_magasins

    if clicked and clicked in coords and clicked in liste_autorisee:
        # Eviter de re-traiter le même clic (anti-boucle)
        if clicked != st.session_state.last_clicked:
            st.session_state.last_clicked = clicked

            if mode_carte == "A":
                st.session_state.point_a    = clicked
                st.session_state.mode_carte = None
            else:
                st.session_state.point_b    = clicked
                st.session_state.mode_carte = None

            st.rerun()

# ─────────────────────────────────────────────
# TABLEAU DES DISTANCES DEPUIS POINT A
# ─────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📋 Toutes les distances depuis **{point_a}**")

df_filtre = df[(df["De"] == point_a) | (df["Vers"] == point_a)].copy()

def normalise(row, ref):
    dest = row["Vers"] if row["De"] == ref else row["De"]
    return pd.Series({"Destination": dest, "Km": row["Km"], "Minutes": row["Minutes"]})

df_display = df_filtre.apply(lambda r: normalise(r, point_a), axis=1)
df_display = df_display[df_display["Destination"] != point_a]
df_display = df_display.drop_duplicates(subset="Destination")
df_display = df_display.sort_values("Km").reset_index(drop=True)
df_display["Km"]      = df_display["Km"].round(1)
df_display["Minutes"] = df_display["Minutes"].astype(int)

def fmt_duree(mn):
    h  = mn // 60
    m_ = mn % 60
    return f"{h}h{m_:02d}" if h > 0 else f"{m_} min"

df_display["Durée"] = df_display["Minutes"].apply(fmt_duree)
df_display = df_display[["Destination", "Km", "Durée", "Minutes"]]

def highlight_selected(row):
    if row["Destination"] == point_b:
        return ["background-color: #FFF176; font-weight: bold"] * len(row)
    return [""] * len(row)

st.dataframe(
    df_display.style.apply(highlight_selected, axis=1),
    use_container_width=True,
    hide_index=True
)
