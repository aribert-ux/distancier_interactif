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
if "point_a"         not in st.session_state:
    st.session_state.point_a         = entrepots_ok[0] if entrepots_ok else tous_ok[0]
if "point_b"         not in st.session_state:
    st.session_state.point_b         = magasins_ok[0]  if magasins_ok  else tous_ok[0]
if "mode_carte"      not in st.session_state:
    st.session_state.mode_carte      = None   # None | "A" | "B"
if "type_a"          not in st.session_state:
    st.session_state.type_a          = "🏭 Entrepôt (ENT)"
if "type_b"          not in st.session_state:
    st.session_state.type_b          = "🏪 Magasin / Drive"

# ─────────────────────────────────────────────
# SIDEBAR — SÉLECTION
# ─────────────────────────────────────────────
st.sidebar.header("📍 Sélection des points")

# ── POINT A ───────────────────────────────────
st.sidebar.markdown("### Point A")

type_a = st.sidebar.radio(
    "Type Point A",
    options=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"],
    index=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"].index(st.session_state.type_a),
    key="radio_type_a"
)
# Mise à jour du type si changé → reset mode carte
if type_a != st.session_state.type_a:
    st.session_state.type_a     = type_a
    if st.session_state.mode_carte == "A":
        st.session_state.mode_carte = None

if type_a == "🏭 Entrepôt (ENT)":
    liste_a = entrepots_ok
elif type_a == "🏪 Magasin / Drive":
    liste_a = magasins_ok
else:
    liste_a = tous_ok

# Sécurité : si point_a n'est plus dans la liste après changement de type
if st.session_state.point_a not in liste_a:
    st.session_state.point_a = liste_a[0] if liste_a else tous_ok[0]

# Selectbox Point A (barre de recherche native Streamlit)
point_a_select = st.sidebar.selectbox(
    "📍 Point A — liste",
    options=liste_a,
    index=liste_a.index(st.session_state.point_a) if st.session_state.point_a in liste_a else 0,
    key="select_a"
)
# Synchronisation selectbox → session_state (hors mode carte actif sur A)
if st.session_state.mode_carte != "A":
    if point_a_select != st.session_state.point_a:
        st.session_state.point_a = point_a_select
        st.rerun()

# Bouton "Pointer sur la carte" pour A
col_btn_a1, col_btn_a2 = st.sidebar.columns(2)
with col_btn_a1:
    if st.button(
        "🗺️ Pointer A" if st.session_state.mode_carte != "A" else "✅ Mode actif",
        key="btn_carte_a",
        type="primary" if st.session_state.mode_carte == "A" else "secondary",
        use_container_width=True
    ):
        st.session_state.mode_carte = "A" if st.session_state.mode_carte != "A" else None
        st.rerun()
with col_btn_a2:
    if st.session_state.mode_carte == "A":
        if st.button("❌ Annuler", key="btn_cancel_a", use_container_width=True):
            st.session_state.mode_carte = None
            st.rerun()

if st.session_state.mode_carte == "A":
    st.sidebar.info(f"🖱️ Cliquez sur un point **{type_a}** sur la carte pour définir le **Point A**.")

st.sidebar.markdown("---")

# ── POINT B ───────────────────────────────────
st.sidebar.markdown("### Point B")

type_b = st.sidebar.radio(
    "Type Point B",
    options=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"],
    index=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"].index(st.session_state.type_b),
    key="radio_type_b"
)
if type_b != st.session_state.type_b:
    st.session_state.type_b     = type_b
    if st.session_state.mode_carte == "B":
        st.session_state.mode_carte = None

if type_b == "🏭 Entrepôt (ENT)":
    liste_b = entrepots_ok
elif type_b == "🏪 Magasin / Drive":
    liste_b = magasins_ok
else:
    liste_b = tous_ok

if st.session_state.point_b not in liste_b:
    st.session_state.point_b = liste_b[0] if liste_b else tous_ok[0]

# Selectbox Point B (barre de recherche native Streamlit)
point_b_select = st.sidebar.selectbox(
    "📍 Point B — liste",
    options=liste_b,
    index=liste_b.index(st.session_state.point_b) if st.session_state.point_b in liste_b else 0,
    key="select_b"
)
if st.session_state.mode_carte != "B":
    if point_b_select != st.session_state.point_b:
        st.session_state.point_b = point_b_select
        st.rerun()

# Bouton "Pointer sur la carte" pour B
col_btn_b1, col_btn_b2 = st.sidebar.columns(2)
with col_btn_b1:
    if st.button(
        "🗺️ Pointer B" if st.session_state.mode_carte != "B" else "✅ Mode actif",
        key="btn_carte_b",
        type="primary" if st.session_state.mode_carte == "B" else "secondary",
        use_container_width=True
    ):
        st.session_state.mode_carte = "B" if st.session_state.mode_carte != "B" else None
        st.rerun()
with col_btn_b2:
    if st.session_state.mode_carte == "B":
        if st.button("❌ Annuler", key="btn_cancel_b", use_container_width=True):
            st.session_state.mode_carte = None
            st.rerun()

if st.session_state.mode_carte == "B":
    st.sidebar.info(f"🖱️ Cliquez sur un point **{type_b}** sur la carte pour définir le **Point B**.")

# ─────────────────────────────────────────────
# VARIABLES LOCALES (depuis session_state)
# ─────────────────────────────────────────────
point_a = st.session_state.point_a
point_b = st.session_state.point_b

# ─────────────────────────────────────────────
# BANNIÈRE MODE CARTE ACTIF
# ─────────────────────────────────────────────
if st.session_state.mode_carte == "A":
    type_label = st.session_state.type_a
    st.warning(f"🗺️ **Mode sélection carte actif — Point A** | Seuls les points *{type_label}* sont affichés. Cliquez sur un point pour le sélectionner.")
elif st.session_state.mode_carte == "B":
    type_label = st.session_state.type_b
    st.warning(f"🗺️ **Mode sélection carte actif — Point B** | Seuls les points *{type_label}* sont affichés. Cliquez sur un point pour le sélectionner.")

# ─────────────────────────────────────────────
# RECHERCHE DE LA DISTANCE
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
# MÉTRIQUES EN ÉVIDENCE
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

# ── Détermination des points à afficher selon le mode ──
mode_carte = st.session_state.mode_carte

if mode_carte == "A":
    # N'afficher que les points du type sélectionné pour A
    if st.session_state.type_a == "🏭 Entrepôt (ENT)":
        points_visibles = entrepots_ok
    elif st.session_state.type_a == "🏪 Magasin / Drive":
        points_visibles = magasins_ok
    else:
        points_visibles = tous_ok
    afficher_entrepots = [e for e in entrepots_ok if e in points_visibles]
    afficher_magasins  = [m_ for m_ in magasins_ok if m_ in points_visibles]

elif mode_carte == "B":
    if st.session_state.type_b == "🏭 Entrepôt (ENT)":
        points_visibles = entrepots_ok
    elif st.session_state.type_b == "🏪 Magasin / Drive":
        points_visibles = magasins_ok
    else:
        points_visibles = tous_ok
    afficher_entrepots = [e for e in entrepots_ok if e in points_visibles]
    afficher_magasins  = [m_ for m_ in magasins_ok if m_ in points_visibles]

else:
    # Mode normal : tous les points
    afficher_entrepots = entrepots_ok
    afficher_magasins  = magasins_ok

# ── Entrepôts (bleus) ──────────────────────────
for ent in afficher_entrepots:
    lat, lon = coords[ent]
    is_selected = (ent == point_a or ent == point_b)
    folium.CircleMarker(
        location=[lat, lon],
        radius=8 if is_selected else 6,
        color="#1565C0",
        fill=True,
        fill_color="#1E88E5",
        fill_opacity=1.0 if is_selected else 0.7,
        tooltip=ent,
        popup=folium.Popup(f"<b>🏭 {ent}</b>", max_width=250)
    ).add_to(m)

# ── Magasins (verts) ───────────────────────────
for mag in afficher_magasins:
    lat, lon = coords[mag]
    is_selected = (mag == point_a or mag == point_b)
    folium.CircleMarker(
        location=[lat, lon],
        radius=7 if is_selected else 5,
        color="#2E7D32",
        fill=True,
        fill_color="#43A047",
        fill_opacity=1.0 if is_selected else 0.6,
        tooltip=mag,
        popup=folium.Popup(f"<b>🏪 {mag}</b>", max_width=250)
    ).add_to(m)

# ── Marqueur Point A ───────────────────────────
if lat_a:
    icon_a = folium.Icon(
        color="blue"  if point_a.startswith("ENT") else "green",
        icon="industry" if point_a.startswith("ENT") else "shopping-cart",
        prefix="fa"
    )
    folium.Marker(
        location=[lat_a, lon_a],
        tooltip=f"📍 A — {point_a}",
        popup=folium.Popup(f"<b>📍 POINT A</b><br>{point_a}", max_width=300),
        icon=icon_a
    ).add_to(m)

# ── Marqueur Point B ───────────────────────────
if lat_b and point_b != point_a:
    icon_b = folium.Icon(
        color="blue"  if point_b.startswith("ENT") else "green",
        icon="industry" if point_b.startswith("ENT") else "shopping-cart",
        prefix="fa"
    )
    folium.Marker(
        location=[lat_b, lon_b],
        tooltip=f"📍 B — {point_b}",
        popup=folium.Popup(f"<b>📍 POINT B</b><br>{point_b}", max_width=300),
        icon=icon_b
    ).add_to(m)

# ── Trait A → B ────────────────────────────────
if lat_a and lat_b and point_a != point_b:
    label = ""
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
        tooltip=label,
        popup=folium.Popup(
            f"<b>📏 {km:.1f} km</b><br>⏱️ {label}",
            max_width=200
        ) if km else None
    ).add_to(m)

    if km is not None:
        mid_lat = (lat_a + lat_b) / 2
        mid_lon = (lon_a + lon_b) / 2
        folium.Marker(
            location=[mid_lat, mid_lon],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    background-color: #E53935;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    white-space: nowrap;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.4);
                ">
                    📏 {km:.1f} km &nbsp;|&nbsp; ⏱️ {duree_str}
                </div>
                """,
                icon_size=(220, 34),
                icon_anchor=(110, 17)
            )
        ).add_to(m)

# ── Légende ────────────────────────────────────
legend_html = """
<div style="
    position: fixed;
    bottom: 30px; left: 30px;
    background-color: white;
    border: 2px solid #ccc;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    z-index: 1000;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
">
    <b>Légende</b><br>
    <span style="color:#1E88E5;">●</span> Entrepôt (ENT)<br>
    <span style="color:#43A047;">●</span> Magasin / Drive<br>
    <span style="color:#E53935;">—</span> Trajet sélectionné
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ── Affichage carte + gestion du clic ──────────
carte_result = st_folium(
    m,
    width="100%",
    height=600,
    returned_objects=["last_object_clicked_tooltip"]
)

# ── Traitement du clic sur la carte ────────────
if mode_carte in ("A", "B"):
    clicked_tooltip = carte_result.get("last_object_clicked_tooltip") if carte_result else None

    if clicked_tooltip and clicked_tooltip in coords:
        # Vérifier que le lieu cliqué appartient bien à la liste filtrée
        liste_autorisee = afficher_entrepots + afficher_magasins

        if clicked_tooltip in liste_autorisee:
            if mode_carte == "A" and clicked_tooltip != st.session_state.point_a:
                st.session_state.point_a   = clicked_tooltip
                st.session_state.mode_carte = None   # désactiver le mode après sélection
                st.rerun()
            elif mode_carte == "B" and clicked_tooltip != st.session_state.point_b:
                st.session_state.point_b   = clicked_tooltip
                st.session_state.mode_carte = None
                st.rerun()

# ─────────────────────────────────────────────
# TABLEAU DES DISTANCES DEPUIS LE POINT A
# ─────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📋 Toutes les distances depuis **{point_a}**")

df_filtre = df[
    (df["De"] == point_a) | (df["Vers"] == point_a)
].copy()

def normalise(row, ref):
    dest = row["Vers"] if row["De"] == ref else row["De"]
    return pd.Series({
        "Destination": dest,
        "Km":          row["Km"],
        "Minutes":     row["Minutes"]
    })

df_display = df_filtre.apply(lambda r: normalise(r, point_a), axis=1)
df_display = df_display[df_display["Destination"] != point_a]
df_display = df_display.drop_duplicates(subset="Destination")
df_display = df_display.sort_values("Km").reset_index(drop=True)
df_display["Km"]      = df_display["Km"].round(1)
df_display["Minutes"] = df_display["Minutes"].astype(int)

def fmt_duree(m):
    h  = m // 60
    mn = m % 60
    return f"{h}h{mn:02d}" if h > 0 else f"{mn} min"

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
