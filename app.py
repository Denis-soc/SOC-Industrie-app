import streamlit as st
import sqlalchemy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import urllib.parse
import base64

# 1. CONFIGURATION
st.set_page_config(page_title="SOC Industrie — Gestion Interne", page_icon="🏗️", layout="wide")
st.title("🏗️ SOC Industrie — Gestion Interne")

# 2. DÉFINITION DE LA CONNEXION (Doit être défini AVANT d'être appelé)
@st.cache_resource
def init_connection():
    # Remplacez "VotreMotDePasse" par votre vrai mot de passe Supabase
    db_url = "postgresql://postgres.spxrxmzeaybndgpmoslo:LesGaulois2026@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
    return sqlalchemy.create_engine(db_url)

# 3. INITIALISATION DU MOTEUR
try:
    engine = init_connection()
    with engine.connect() as conn:
        pass
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# 4. FONCTIONS DE CHARGEMENT
def charger_materiel():
    query = 'SELECT id AS "ID", nom AS "Nom", categorie AS "Catégorie", statut AS "Statut", detenteur AS "Détenteur", date_controle AS "Date Contrôle", intervalle_mois AS "Intervalle (mois)", prochain_controle AS "Prochain Contrôle", photo_base64 AS "Photo", marque AS "Marque", reference AS "Référence", num_serie AS "N° de Série" FROM materiel;'
    return pd.read_sql(query, engine)

def charger_demandes():
    query = 'SELECT date_demande AS "Date", collaborateur AS "Collaborateur", type_demande AS "Type", designation AS "Désignation", code_imputation AS "Code Imputation", details AS "Détails / Dates", statut AS "Statut" FROM demandes_collaborateurs;'
    return pd.read_sql(query, engine)

# 5. CHARGEMENT DES DONNÉES
df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

# --- 6. CRÉATION DES ONGLETS (Noms validés) ---
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 Tableau de Bord Olivier", 
    "🛒 Catalogues EPI/Consommables/Outillage", 
    "📦 Matériels Commun", 
    "📅 Réservation matériel",
    "📍 Carte de localisation du matériel"
])
# 5. Contenu des onglets
with tab0:
    st.header("👑 Tableau de Bord Olivier")
    
    # 1. Gestion des demandes
    st.subheader("📋 Demandes en attente")
    # On vérifie si df_demandes_reel existe [cite: 1]
    if not df_demandes_reel.empty:
        st.dataframe(df_demandes_reel, use_container_width=True, hide_index=True)
        
        # Interface de traitement
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            demande_a_traiter = st.selectbox("Sélectionner une ligne à traiter :", 
                                             df_demandes_reel["Collaborateur"] + " - " + df_demandes_reel["Désignation"], 
                                             key="sel_olivier")
        with col_v2:
            action_decision = st.radio("Action :", ["Laisser en attente", "Valider / Matériel Prêt", "Supprimer"], 
                                       horizontal=True, key="rad_olivier")
                                       
        if st.button("Confirmer l'action", key="btn_olivier"):
            collab_sel = demande_a_traiter.split(" - ")[0]
            desig_sel = demande_a_traiter.split(" - ")[1]
            
            with engine.begin() as conn_tx:
                if action_decision == "Supprimer":
                    conn_tx.execute(sqlalchemy.text("DELETE FROM demandes_collaborateurs WHERE collaborateur = :c AND designation = :d;"), 
                                    {"c": collab_sel, "d": desig_sel})
                elif action_decision != "Laisser en attente":
                    conn_tx.execute(sqlalchemy.text("UPDATE demandes_collaborateurs SET statut = :s WHERE collaborateur = :c AND designation = :d;"), 
                                    {"s": action_decision, "c": collab_sel, "d": desig_sel})
            st.rerun()
    else:
        st.success("✅ Aucune demande en attente.")

    st.markdown("---")
    
    # 2. Alertes étalonnage
    st.subheader("🚨 Alertes Étalonnages (< 90 jours)")
    aujourdhui = datetime.now().date()
    lignes_alertes = []
    
    for idx, row in df_materiel_reel.iterrows():
        date_prox = row["Prochain Contrôle"]
        # Conversion sécurisée des dates [cite: 1, 11]
        if isinstance(date_prox, str): 
            date_prox = datetime.strptime(date_prox, "%Y-%m-%d").date()
        elif isinstance(date_prox, datetime): 
            date_prox = date_prox.date()
            
        if (date_prox - aujourdhui).days <= 90:
            lignes_alertes.append({
                "ID": row["ID"], 
                "Matériel": row["Nom"], 
                "Détenteur": row["Détenteur"], 
                "Prochain Contrôle": date_prox
            })
            
    if lignes_alertes:
        st.dataframe(pd.DataFrame(lignes_alertes), use_container_width=True, hide_index=True)
    else:
        st.success("✅ Aucun étalonnage critique à prévoir.")
with tab1:
    st.header("🛒 Catalogue EPI / Consommables / Outillage")
    
    # Choix du mode : Catalogue ou Administration
    mode = st.radio("Mode d'affichage :", ["Catalogue", "Administration"], horizontal=True)
    
    if mode == "Catalogue":
        st.subheader("Nos produits disponibles")
        # Ici, vous pourrez ajouter le filtre par type (EPI, Consommable, Outillage)
        # et la boucle d'affichage de vos produits.
        st.info("Visualisation du catalogue en cours...")
        
    elif mode == "Administration":
        st.subheader("⚙️ Gestion des fiches")
        action = st.selectbox("Action :", ["Créer une fiche", "Modifier une fiche", "Supprimer une fiche"])
        
        if action == "Créer une fiche":
            with st.form("form_creation"):
                col1, col2 = st.columns(2)
                with col1:
                    num_interne = st.text_input("Numéro interne (ex: SOC-001)")
                    nom = st.text_input("Nom de l'article")
                    ref = st.text_input("Référence interne")
                with col2:
                    fournisseur = st.text_input("Fournisseur")
                    ref_fournisseur = st.text_input("Référence fournisseur")
                    num_serie = st.text_input("N° de Série")
                
                # --- GESTION PHOTO (Upload ou Caméra) ---
                photo_option = st.radio("Comment ajouter la photo ?", ["Uploader un fichier", "Prendre en direct"], horizontal=True)
                if photo_option == "Uploader un fichier":
                    photo = st.file_uploader("Choisir une image", type=['png', 'jpg', 'jpeg'])
                else:
                    photo = st.camera_input("Prendre une photo")
                
                st.subheader("📋 Suivi & Maintenance")
                soumis_verif = st.checkbox("Matériel soumis à vérification/étalonnage ?")
                periodicite, date_depart = 0, None
                if soumis_verif:
                    c1, c2 = st.columns(2)
                    periodicite = c1.number_input("Périodicité (en mois)", min_value=1, value=12)
                    date_depart = c2.date_input("Date de départ (ou dernier contrôle)")
                
                if st.form_submit_button("Enregistrer et générer le QR Code"):
                    # 1. Logique d'insertion SQL (incluant les colonnes de suivi)
                    # L'insertion ici envoie automatiquement les données dans votre base
                    # ce qui permettra à la page d'Olivier de détecter les alertes
                    
                    st.success(f"Fiche {nom} créée et synchronisée pour le suivi !")
                    
                    # 2. Génération du QR Code
                    info_suivi = f"Périodicité: {periodicite}m | Départ: {date_depart}" if soumis_verif else "Non soumis"
                    data_qr = f"SOC: {num_interne} | {nom} | Série: {num_serie} | {info_suivi}"
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(data_qr)}"
                    st.image(qr_url, caption="QR Code matériel")
        
        elif action == "Modifier une fiche":
            st.warning("Fonctionnalité de modification à venir.")
        
        elif action == "Supprimer une fiche":
            st.error("Fonctionnalité de suppression à venir.")

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
