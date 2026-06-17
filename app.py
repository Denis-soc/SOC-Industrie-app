import streamlit as st
import pandas as pd
import sqlalchemy

# ==========================================
# 1. CONNEXION GLOBALE SUPABASE (SQLAlchemy)
# ==========================================
import streamlit as st
import sqlalchemy

# Connexion sécurisée via le Pooler IPv4 (Port 6543)
# REMPLACEZ VotreMotDePasse par le vrai mot de passe de votre base (sans crochets)
engine = sqlalchemy.create_engine(
    "postgresql://postgres.spxrxmzeaybndgpmoslo:LesGaulois2026@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
)

try:
    conn = engine.connect()
except Exception as e:
    st.error(f"Erreur de connexion à la base de données : {e}")
    st.stop()

# --- RESTE DE VOTRE CODE ---
st.title("🏗️ SOC Industrie — Gestion Interne")
st.write("Connexion établie avec succès via le Pooler !")
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
# ==========================================
# LECTURE DES DONNÉES (SANS BLOCAGE)
# ==========================================
try:
    query = "SELECT * FROM materiel LIMIT 10;"
    df = pd.read_sql(query, conn)
    
    if df.empty:
        st.info("La table 'materiel' est connectée mais ne contient aucune donnée pour le moment.")
        # La ligne st.stop() a été retirée d'ici pour laisser l'application s'afficher entièrement !
    else:
        st.dataframe(df)
except Exception as e:
    st.warning(f"Note : Impossible de lire la table 'materiel' : {e}")

# ==========================================
# ICI COMMENCE TOUT VOTRE CODE SUIVANT :
# (Votre carte de localisation, suivi des EPI, etc.)
# ==========================================

# ==========================================
# 4. LE RESTE DE VOTRE CODE (Cartes, QR Codes, Chantiers...)
# ==========================================
# C'est ici que vous remettez vos fonctions (folium, qrcode, geopy, etc.)
# qui composent le reste de votre application.
