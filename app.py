import streamlit as st
import pandas as pd
import sqlalchemy
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="SOC Industrie", layout="wide")

# Ajout du logo dans la barre latérale
st.sidebar.image("Logo SOC INDUSTRIE COULEUR - Copie.png", width=150) # Remplacez par l'URL de votre vrai logo si besoin
st.sidebar.title("SOC Industrie")
st.sidebar.info("Gestion interne du parc matériel.")

st.title("🏗️ SOC Industrie — Gestion Interne")

# --- CONNEXION BDD ---
@st.cache_resource
def init_connection():
    try:
        return sqlalchemy.create_engine(st.secrets["DB_URL"])
    except:
        return None

engine = init_connection()

# --- ONGLETS ---
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 Tableau de Bord Olivier", 
    "🛒 Catalogues EPI/Consommables/Outillage", 
    "📦 Matériels Commun", 
    "📅 Réservation matériel",
    "📍 Carte de localisation du matériel"
])

# --- STRUCTURE DES ONGLETS ---
with tab0:
    st.header("👑 Tableau de Bord Olivier")
    st.write("Espace centralisé de suivi.")

with tab1:
    st.header("🛒 Catalogues EPI/Consommables/Outillage")
    st.write("Gestion des commandes.")

with tab2:
    st.header("📦 Matériels Commun")
    st.write("Gestion du matériel partagé.")

with tab3:
    st.header("📅 Réservation matériel")
    st.write("Suivi des réservations terrain.")

with tab4:
    st.header("📍 Carte de localisation du matériel")
    st.write("Visualisation des chantiers et du matériel sur le terrain.")
    # Exemple de carte interactive (à remplacer par vos données réelles)
    map_data = pd.DataFrame(
        np.random.randn(5, 2) / [50, 50] + [47.33, -0.40], 
        columns=['lat', 'lon']
    )
    st.map(map_data, zoom=10)
