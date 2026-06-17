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
    admin_action = st.radio("Action :", ["Créer une fiche", "Modifier une fiche", "Supprimer une fiche"])
    
    if admin_action == "Créer une fiche":
        with st.form("form_creation_admin"):
            destination = st.selectbox("Destination :", ["Catalogue EPI", "Catalogue Consommables", "Catalogue Outillage", "Catalogue Matériel Commun"])
            
            col1, col2 = st.columns(2)
            with col1:
                num_interne = st.text_input("Numéro interne")
                nom = st.text_input("Nom de l'article")
                fournisseur = st.text_input("Fournisseur")
            with col2:
                ref = st.text_input("Référence")
                num_serie = st.text_input("N° de Série")
                
            st.subheader("📸 Photo du matériel")
            source_photo = st.radio("Source :", ["Prendre une photo", "Déposer un fichier"], horizontal=True)
            
            image_a_traiter = None
            if source_photo == "Prendre une photo":
                image_a_traiter = st.camera_input("Prendre une photo maintenant", label_visibility="collapsed")
            else:
                image_a_traiter = st.file_uploader("Glisser ou sélectionner un fichier", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

            # Suivi Maintenance (on utilise les colonnes réelles de votre table)
            soumis_verif = st.checkbox("Soumis à contrôle ou étalonnage ?")
            periodicite = st.number_input("Périodicité (mois)", value=12) if soumis_verif else 0
            date_c = st.date_input("Date du dernier contrôle") if soumis_verif else None

            if st.form_submit_button("Enregistrer"):
                # REQUÊTE SQL CORRIGÉE
                # On utilise UNIQUEMENT les colonnes qui existent réellement dans votre base
                query = """
                INSERT INTO materiel (id, nom, categorie, reference, num_serie, fournisseur, date_controle, intervalle_mois)
                VALUES (:id, :nom, :cat, :ref, :serie, :fourn, :date_c, :perio)
                """
                try:
                    with engine.begin() as conn:
                        conn.execute(sqlalchemy.text(query), {
                            "id": num_interne, "nom": nom, "cat": destination, "ref": ref, 
                            "serie": num_serie, "fourn": fournisseur, "date_c": date_c, "perio": periodicite
                        })
                    st.success("Fiche enregistrée !")
                except Exception as e:
                    st.error(f"Erreur SQL : {e}")
