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
tous_lieux  = sorted(set(df["De"].unique()) | set(df["Vers"].unique()))
entrepots   = sorted([l for l in tous_lieux if l.startswith("ENT")])
magasins    = sorted([l for l in tous_lieux if not l.startswith("ENT")])

# Filtrer uniquement les lieux avec coordonnées connues
entrepots_ok = [e for e in entrepots if e in coords]
magasins_ok  = [m for m in magasins  if m in coords]
tous_ok      = sorted([l for l in tous_lieux if l in coords])

# ─────────────────────────────────────────────
# SIDEBAR — SÉLECTION
# ─────────────────────────────────────────────
st.sidebar.header("📍 Sélection des points")

# Filtre type Point A
type_a = st.sidebar.radio(
    "Type Point A",
    options=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"],
    index=0,
    key="type_a"
)

if type_a == "🏭 Entrepôt (ENT)":
    liste_a = entrepots_ok
elif type_a == "🏪 Magasin / Drive":
    liste_a = magasins_ok
else:
    liste_a = tous_ok

point_a = st.sidebar.selectbox(
    "📍 Point A",
    options=liste_a,
    index=0,
    key="point_a"
)

st.sidebar.markdown("---")

# Filtre type Point B
type_b = st.sidebar.radio(
    "Type Point B",
    options=["🏭 Entrepôt (ENT)", "🏪 Magasin / Drive", "🔀 Tous"],
    index=1,
    key="type_b"
)

if type_b == "🏭 Entrepôt (ENT)":
    liste_b = entrepots_ok
elif type_b == "🏪 Magasin / Drive":
    liste_b = magasins_ok
else:
    liste_b = tous_ok

point_b = st.sidebar.selectbox(
    "📍 Point B",
    options=liste_b,
    index=0,
    key="point_b"
)

# ─────────────────────────────────────────────
# RECHERCHE DE LA DISTANCE
# ─────────────────────────────────────────────
def get_distance(df, origine, destination):
    """Cherche la distance dans les deux sens."""
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
# CARTE FOLIUM
# ─────────────────────────────────────────────
lat_a, lon_a = coords.get(point_a, (None, None))
lat_b, lon_b = coords.get(point_b, (None, None))

# Centre de la carte
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

# ── Tous les entrepôts (bleus) ─────────────────
for ent in entrepots_ok:
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

# ── Tous les magasins (verts) ──────────────────
for mag in magasins_ok:
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

# ── Marqueur Point A (sélectionné) ────────────
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

# ── Marqueur Point B (sélectionné) ────────────
if lat_b:
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

# ── Trait entre A et B ─────────────────────────
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

    # ── Étiquette au milieu du trait ──────────
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

# ── Affichage de la carte ──────────────────────
st_folium(m, width="100%", height=600, returned_objects=[])

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
    h = m // 60
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
