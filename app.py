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
                
            # --- GESTION PHOTO SIMPLIFIÉE ---
            st.subheader("📸 Photo du matériel")
            # Au lieu de la caméra ou de l'uploader, on utilise un champ texte
            # Cela permet de copier-coller un lien d'image (ex: depuis un cloud ou drive)
            url_photo = st.text_input("URL de l'image (Lien web direct) :", placeholder="https://exemple.com/image.jpg")
            
            # Prévisualisation immédiate
            if url_photo:
                st.image(url_photo, width=200)

            # Suivi Maintenance
            soumis_verif = st.checkbox("Soumis à contrôle ou étalonnage ?")
            if soumis_verif:
                c1, c2 = st.columns(2)
                periodicite = c1.number_input("Périodicité (mois)", min_value=1, value=12)
                date_controle = c2.date_input("Date du dernier contrôle")
                # Calcul échéance : date + périodicité
                # L'alerte sera gérée côté Olivier par une requête filtrant prochain_controle <= date.today() + 90 jours
            else:
                periodicite, date_controle = None, None

            if st.form_submit_button("Enregistrer et générer QR Code"):
                # 1. Enregistrement SQL
                query = """
                INSERT INTO materiel (id, nom, categorie, reference, num_serie, fournisseur, date_controle, intervalle_mois)
                VALUES (:id, :nom, :cat, :ref, :serie, :fourn, :date_c, :perio)
                """
                with engine.begin() as conn:
                    conn.execute(sqlalchemy.text(query), {
                        "id": num_interne, "nom": nom, "cat": destination, "ref": ref, 
                        "serie": num_serie, "fourn": fournisseur, "date_c": date_controle, "perio": periodicite
                    })
                
                # 2. Génération QR Code
                data_qr = f"SOC: {num_interne} | {nom} | Série: {num_serie} | Fourn: {fournisseur}"
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(data_qr)}"
                st.image(qr_url, caption="QR Code à imprimer")
                st.success("Matériel enregistré et synchronisé avec le tableau d'Olivier !")
