import streamlit as st
import pandas as pd
import sqlalchemy

# ==========================================
# 1. CONNEXION GLOBALE SUPABASE (SQLAlchemy)
# ==========================================
import streamlit as st
import sqlalchemy

# Connexion via le Pooler (Port 6543) et son URL dédiée
engine = sqlalchemy.create_engine(
    "postgresql://postgres:VotreMotDePasse@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
)

try:
    conn = engine.connect()
except Exception as e:
    st.error(f"Erreur de connexion à la base de données : {e}")
    st.stop()

# ==========================================
# 2. CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(
    page_title="SOC Industrie",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ SOC Industrie — Gestion Interne")
st.write("Connexion établie avec succès à la base de données Supabase.")

# ==========================================
# 3. EXEMPLE DE LECTURE DE DONNÉES
# ==========================================
st.subheader("Données de l'application")

try:
    # Utilisation de Pandas pour lire directement via la connexion SQLAlchemy
    query = "SELECT * FROM test_table LIMIT 10;"  # Remplacez par le nom de vos vraies tables
    df = pd.read_sql(query, conn)
    
    if df.empty:
        st.info("La table est connectée mais ne contient aucune donnée pour le moment.")
    else:
        st.dataframe(df)
except Exception as e:
    st.warning(f"Impossible de lire la table de test (elle n'existe peut-être pas encore) : {e}")

# ==========================================
# 4. LE RESTE DE VOTRE CODE (Cartes, QR Codes, Chantiers...)
# ==========================================
# C'est ici que vous remettez vos fonctions (folium, qrcode, geopy, etc.)
# qui composent le reste de votre application.
