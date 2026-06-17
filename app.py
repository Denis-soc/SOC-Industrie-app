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
            
            # --- GESTION PHOTO ---
            st.subheader("📸 Photo du matériel")
            source_photo = st.radio("Source :", ["Aucune", "Fichier", "Caméra"], horizontal=True, key="photo_source")
            photo_file = None
            if source_photo == "Fichier":
                photo_file = st.file_uploader("Déposer une image", type=['png', 'jpg'], key="uploader")
            elif source_photo == "Caméra":
                photo_file = st.camera_input("Prendre une photo", key="camera")
            
            # --- SUIVI ---
            st.subheader("📅 Suivi et Maintenance")
            soumis_verif = st.checkbox("Soumis à contrôle ou étalonnage ?")
            date_controle, periodicite = None, 0
            if soumis_verif:
                c1, c2 = st.columns(2)
                date_controle = c1.date_input("Date du dernier contrôle")
                periodicite = c2.number_input("Périodicité (mois)", value=12)

            if st.form_submit_button("Enregistrer et générer QR Code"):
                try:
                    # Insertion
                    query = sqlalchemy.text("""
                        INSERT INTO materiel (id, nom, categorie, num_serie, date_controle, intervalle_mois)
                        VALUES (:id, :nom, :cat, :serie, :date_c, :perio)
                    """)
                    with engine.begin() as conn:
                        conn.execute(query, {
                            "id": num_interne, "nom": nom, "cat": categorie, 
                            "serie": num_serie, "date_c": date_controle, "perio": periodicite
                        })
                    st.success("Matériel enregistré !")
                    
                    # Génération QR Code
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(num_interne)}"
                    st.image(qr_url, caption="QR Code")
                except Exception as e:
                    st.error(f"Erreur : {e}")
                except Exception as e:
                    st.error(f"Erreur SQL : {e}")
