import streamlit as st
import sqlalchemy
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CONFIGURATION
st.set_page_config(page_title="SOC Industrie — Gestion", page_icon="🏗️", layout="wide")

# 2. CONNEXION BDD
@st.cache_resource
def init_connection():
    db_url = "postgresql://postgres.spxrxmzeaybndgpmoslo:LesGaulois2026@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
    return sqlalchemy.create_engine(db_url)

engine = init_connection()

# 3. CHARGEMENT DONNÉES
def charger_materiel():
    query = 'SELECT * FROM materiel;'
    return pd.read_sql(query, engine)

def charger_demandes():
    query = 'SELECT * FROM demandes_collaborateurs;'
    return pd.read_sql(query, engine)

# Initialisation sûre des données
df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

# 4. INTERFACE
st.title("🏗️ SOC Industrie — Gestion Interne")

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👑 Tableau de Bord Olivier", 
    "🛒 Catalogues EPI/Consommables/Outillage", 
    "📦 Matériels Commun", 
    "📅 Réservation matériel",
    "📍 Carte de localisation du matériel",
    "⚙️ Administration Matériel" # Nouvel onglet
])
# ... Onglet N°1...
# ... Onglet N°5...
with tab5:
    st.header("⚙️ Administration Matériel")
    admin_action = st.radio("Action :", ["Créer une fiche", "Modifier une fiche", "Supprimer une fiche"], key="admin_radio")
    
    if admin_action == "Créer une fiche":
        with st.form("form_creation_admin"):
            col1, col2 = st.columns(2)
            with col1:
                num_interne = st.text_input("Numéro interne")
                nom = st.text_input("Nom de l'article")
            with col2:
                categorie = st.selectbox("Catégorie :", ["Catalogue EPI", "Catalogue Consommables", "Catalogue Outillage", "Catalogue Matériel Commun"])
                num_serie = st.text_input("N° de Série")
            
            # --- GESTION CONTRÔLE (Date et Périodicité) ---
            st.subheader("📅 Suivi et Maintenance")
            soumis_verif = st.checkbox("Soumis à contrôle ou étalonnage ?")
            
            date_controle = None
            periodicite = 0
            
            if soumis_verif:
                col_date, col_perio = st.columns(2)
                with col_date:
                    date_controle = st.date_input("Date du dernier contrôle")
                with col_perio:
                    periodicite = st.number_input("Périodicité (en mois)", min_value=1, value=12)

            if st.form_submit_button("Enregistrer"):
                try:
                    # Requête mise à jour avec les nouvelles colonnes
                    query = sqlalchemy.text("""
                        INSERT INTO materiel (id, nom, categorie, num_serie, date_controle, intervalle_mois)
                        VALUES (:id, :nom, :cat, :serie, :date_c, :perio)
                    """)
                    
                    with engine.begin() as conn:
                        conn.execute(query, {
                            "id": num_interne, 
                            "nom": nom, 
                            "cat": categorie, 
                            "serie": num_serie,
                            "date_c": date_controle,
                            "perio": periodicite
                        })
                    st.success(f"Fiche {nom} enregistrée !")
                except Exception as e:
                    st.error(f"Erreur SQL : {e}")
