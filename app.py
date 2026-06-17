import streamlit as st
import pandas as pd
import sqlalchemy
import numpy as np

# Configuration de la page
st.set_page_config(page_title="SOC Industrie", layout="wide")
st.title("🏗️ SOC Industrie — Gestion Interne")

# Connexion BDD
@st.cache_resource
def init_connection():
    try:
        return sqlalchemy.create_engine(st.secrets["DB_URL"])
    except:
        return None

engine = init_connection()

# Création des 4 onglets
tab0, tab1, tab2, tab3 = st.tabs([
    "👑 Tableau de Bord Olivier", 
    "🛒 Catalogues EPI/Consommables/Outillage", 
    "📦 Matériels Commun", 
    "📅 Réservation matériel"
])

# Structure de base
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
