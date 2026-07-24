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
    return dict(zip(coords_df["tag"], zip(coords_df["latitude"], coords_df["longitude"])))

df     = load_data()
coords = load_coordinates()

# ─────────────────────────────────────────────
# LISTES DE LIEUX
# ─────────────────────────────────────────────
tous_lieux   = sorted(set(df["De"].unique()) | set(df["Vers"].unique()))
entrepots_ok = sorted([l for l in tous_lieux if l.startswith("ENT") and l in coords])
magasins_ok  = sorted([l for l in tous_lieux if not l.startswith("ENT") and l in coords])
tous_ok      = sorted([l for l in tous_lieux if l in coords])

def get_liste(type_str):
    if type_str == "🏭 Entrepôt (ENT)":
        return entrepots_ok
    elif type_str == "🏪 Magasin / Drive":
        return magasins_ok
    return tous_ok

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "point_a":    entrepots_ok[0] if entrepots_ok else tous_ok[0],
    "point_b":    magasins_ok[0]  if magasins_ok  else tous_ok[0],
    "type_a":     "🏭 Entrepôt (ENT)",
    "type_b":     "🏪 Magasin / Drive",
    "mode_carte": None,   # None | "A" | "B"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# SIDEBAR — POINT A
# ─────────────────────────────────────────────
st.sidebar.header("📍 Sélection des points")
st.sidebar.markdown("### Point A")

# Radio type A
type_a = st.sidebar.radio(
    "Type Point A",
    options=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"],
    index=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"].index(st.session_state.type_a),
    key="radio_type_a"
)
if type_a != st.session_state.type_a:
    st.session_state.type_a = type_a
    st.session_state.mode_carte = None
    liste = get_liste(type_a)
    if st.session_state.point_a not in liste:
        st.session_state.point_a = liste[0]
    st.rerun()

liste_a = get_liste(st.session_state.type_a)
if st.session_state.point_a not in liste_a:
    st.session_state.point_a = liste_a[0]

# Selectbox A — index piloté par session_state, PAS de key= pour éviter le conflit
idx_a = liste_a.index(st.session_state.point_a)
nouveau_a = st.sidebar.selectbox(
    "📍 Point A",
    options=liste_a,
    index=idx_a
)
# Mise à jour uniquement si changé via la liste (pas en mode carte)
if nouveau_a != st.session_state.point_a and st.session_state.mode_carte != "A":
    st.session_state.point_a = nouveau_a
    st.rerun()

# Bouton unique toggle "Pointer sur la carte"
if st.session_state.mode_carte == "A":
    st.sidebar.warning("🖱️ **Cliquez sur un point de la carte** pour définir le Point A.")
    if st.sidebar.button("❌ Annuler la sélection carte (A)", use_container_width=True):
        st.session_state.mode_carte = None
        st.rerun()
else:
    if st.sidebar.button("🗺️ Pointer le Point A sur la carte", use_container_width=True):
        st.session_state.mode_carte = "A"
        st.rerun()

st.sidebar.markdown("---")

# ─────────────────────────────────────────────
# SIDEBAR — POINT B
# ─────────────────────────────────────────────
st.sidebar.markdown("### Point B")

type_b = st.sidebar.radio(
    "Type Point B",
    options=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"],
    index=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"].index(st.session_state.type_b),
    key="radio_type_b"
)
if type_b != st.session_state.type_b:
    st.session_state.type_b = type_b
    st.session_state.mode_carte = None
    liste = get_liste(type_b)
    if st.session_state.point_b not in liste:
        st.session_state.point_b = liste[0]
    st.rerun()

liste_b = get_liste(st.session_state.type_b)
if st.session_state.point_b not in liste_b:
    st.session_state.point_b = liste_b[0]

idx_b = liste_b.index(st.session_state.point_b)
nouveau_b = st.sidebar.selectbox(
    "📍 Point B",
    options=liste_b,
    index=idx_b
)
if nouveau_b != st.session_state.point_b and st.session_state.mode_carte != "B":
    st.session_state.point_b = nouveau_b
    st.rerun()

if st.session_state.mode_carte == "B":
    st.sidebar.warning("🖱️ **Cliquez sur un point de la carte** pour définir le Point B.")
    if st.sidebar.button("❌ Annuler la sélection carte (B)", use_container_width=True):
        st.session_state.mode_carte = None
        st.rerun()
else:
    if st.sidebar.button("🗺️ Pointer le Point B sur la carte", use_container_width=True):
        st.session_state.mode_carte = "B"
        st.rerun()

# ─────────────────────────────────────────────
# LECTURE FINALE DES POINTS
# ─────────────────────────────────────────────
point_a    = st.session_state.point_a
point_b    = st.session_state.point_b
mode_carte = st.session_state.mode_carte

# ─────────────────────────────────────────────
# BANNIÈRE MODE ACTIF
# ─────────────────────────────────────────────
if mode_carte == "A":
    st.info(f"🗺️ **Mode sélection carte actif — Point A** | Type affiché : *{st.session_state.type_a}* — Cliquez sur un marqueur de la carte.")
elif mode_carte == "B":
    st.info(f"🗺️ **Mode sélection carte actif — Point B** | Type affiché : *{st.session_state.type_b}* — Cliquez sur un marqueur de la carte.")

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
        st.success(f"**📏 Distance roulée**\n\n{km:.1f} km")
    else:
        st.warning("**📏 Distance roulée**\n\nNon disponible")
with col4:
    if minutes is not None:
        heures    = int(minutes) // 60
        mins      = int(minutes) % 60
        duree_str = f"{heures}h{mins:02d}" if heures > 0 else f"{int(mins)} min"
        st.success(f"**⏱️ Temps de route**\n\n{duree_str} ({int(minutes)} min)")
    else:
        st.warning("**⏱️ Temps de route**\n\nNon disponible")

st.markdown("---")

# ─────────────────────────────────────────────
# CONSTRUCTION CARTE
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

m = folium.Map(location=[centre_lat, centre_lon], zoom_start=7, tiles="CartoDB positron")

# Points à afficher selon le mode
if mode_carte == "A":
    liste_filtre = get_liste(st.session_state.type_a)
    aff_ent = [e for e in entrepots_ok if e in liste_filtre]
    aff_mag = [g for g in magasins_ok  if g in liste_filtre]
elif mode_carte == "B":
    liste_filtre = get_liste(st.session_state.type_b)
    aff_ent = [e for e in entrepots_ok if e in liste_filtre]
    aff_mag = [g for g in magasins_ok  if g in liste_filtre]
else:
    aff_ent = entrepots_ok
    aff_mag = magasins_ok

# Entrepôts (bleus)
for ent in aff_ent:
    lat, lon = coords[ent]
    selected = (ent == point_a or ent == point_b)
    folium.CircleMarker(
        location=[lat, lon],
        radius=9 if selected else 6,
        color="#1565C0",
        fill=True,
        fill_color="#1E88E5",
        fill_opacity=1.0 if selected else 0.7,
        tooltip=ent,
        popup=folium.Popup(f"<b>🏭 {ent}</b>", max_width=250)
    ).add_to(m)

# Magasins (verts)
for mag in aff_mag:
    lat, lon = coords[mag]
    selected = (mag == point_a or mag == point_b)
    folium.CircleMarker(
        location=[lat, lon],
        radius=8 if selected else 5,
        color="#2E7D32",
        fill=True,
        fill_color="#43A047",
        fill_opacity=1.0 if selected else 0.6,
        tooltip=mag,
        popup=folium.Popup(f"<b>🏪 {mag}</b>", max_width=250)
    ).add_to(m)

# Marqueur A
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

# Marqueur B
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

# Trait A → B
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
        color="#E53935", weight=4, opacity=0.9,
        tooltip=label
    ).add_to(m)

    if km is not None:
        folium.Marker(
            location=[(lat_a + lat_b) / 2, (lon_a + lon_b) / 2],
            icon=folium.DivIcon(
                html=f"""
                <div style="background-color:#E53935;color:white;
                    padding:5px 10px;border-radius:12px;font-size:12px;
                    font-weight:bold;white-space:nowrap;
                    box-shadow:2px 2px 6px rgba(0,0,0,0.4);">
                    📏 {km:.1f} km &nbsp;|&nbsp; ⏱️ {duree_str}
                </div>""",
                icon_size=(220, 34), icon_anchor=(110, 17)
            )
        ).add_to(m)

# Légende
m.get_root().html.add_child(folium.Element("""
<div style="position:fixed;bottom:30px;left:30px;background-color:white;
    border:2px solid #ccc;border-radius:8px;padding:10px 14px;
    font-size:13px;z-index:1000;box-shadow:2px 2px 6px rgba(0,0,0,0.2);">
    <b>Légende</b><br>
    <span style="color:#1E88E5;">●</span> Entrepôt (ENT)<br>
    <span style="color:#43A047;">●</span> Magasin / Drive<br>
    <span style="color:#E53935;">—</span> Trajet sélectionné
</div>
"""))

# ─────────────────────────────────────────────
# AFFICHAGE CARTE
# ─────────────────────────────────────────────
carte_result = st_folium(
    m,
    width="100%",
    height=600,
    returned_objects=["last_object_clicked_tooltip"]
)

# ─────────────────────────────────────────────
# TRAITEMENT DU CLIC CARTE
# ─────────────────────────────────────────────
if mode_carte in ("A", "B") and carte_result:
    tooltip_clique = carte_result.get("last_object_clicked_tooltip")

    # Le tooltip doit être un tag connu et dans la liste autorisée
    liste_autorisee = aff_ent + aff_mag

    if (
        tooltip_clique
        and isinstance(tooltip_clique, str)
        and tooltip_clique in coords
        and tooltip_clique in liste_autorisee
    ):
        if mode_carte == "A" and tooltip_clique != st.session_state.point_a:
            st.session_state.point_a    = tooltip_clique
            st.session_state.mode_carte = None
            st.rerun()

        elif mode_carte == "B" and tooltip_clique != st.session_state.point_b:
            st.session_state.point_b    = tooltip_clique
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
