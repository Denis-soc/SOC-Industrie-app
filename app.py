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
# Récupération du paramètre dans l'URL
query_params = st.query_params
if "materiel_id" in query_params:
    id_recherche = query_params["materiel_id"]
    st.info(f"Recherche automatique du matériel : {id_recherche}")
    # Ici, vous pourriez ajouter une logique pour ouvrir automatiquement 
    # une fenêtre modale ou filtrer le catalogue sur cet ID
# ... Onglet N°1...
# ... Onglet N°5...
with tab5:
    st.header("⚙️ Administration Matériel")
    
    # 1. Menu d'action avec clé unique
    admin_action = st.radio("Action :", ["Créer une fiche", "Modifier une fiche", "Supprimer une fiche"], key="admin_radio")
    
    # --- BLOC CRÉATION ---
    if admin_action == "Créer une fiche":
        with st.form("form_creation_admin"):
            col1, col2 = st.columns(2)
            with col1:
                num_interne = st.text_input("Numéro interne", key="c_id")
                nom = st.text_input("Nom de l'article", key="c_nom")
                fournisseur = st.text_input("Fournisseur", key="c_fourn")
            with col2:
                categorie = st.selectbox("Catégorie :", ["Catalogue EPI", "Catalogue Consommables", "Catalogue Outillage", "Catalogue Matériel Commun"], key="c_cat")
                ref = st.text_input("Référence", key="c_ref")
                num_serie = st.text_input("N° de Série", key="c_serie")
            
            st.subheader("📅 Suivi et Maintenance")
            soumis_verif = st.checkbox("Soumis à contrôle ou étalonnage ?", key="c_maint")
            date_c, perio = None, 0
            if soumis_verif:
                c1, c2 = st.columns(2)
                date_c = c1.date_input("Date du dernier contrôle")
                perio = c2.number_input("Périodicité (mois)", value=12)

            # Votre code de photo
            st.subheader("📸 Photo du matériel")
            source_photo = st.radio("Source :", ["Aucune", "Fichier", "Caméra"], horizontal=True, key="c_photo_src")
            uploaded_file = None
            if source_photo == "Fichier":
                uploaded_file = st.file_uploader("Déposer une image", type=['png', 'jpg'], key="c_file")
            elif source_photo == "Caméra":
                uploaded_file = st.camera_input("Prendre une photo", key="c_cam")

            if st.form_submit_button("Enregistrer"):
                # Votre logique SQL ici...
                st.success("Fiche créée !")

    # --- BLOC MODIFICATION (Bien aligné avec le IF) ---
    elif admin_action == "Modifier une fiche":
        st.info("Interface de modification en construction.")
        # Le code de modification viendra ici...

    # --- BLOC SUPPRESSION ---
    elif admin_action == "Supprimer une fiche":
        st.warning("Interface de suppression en construction.")
