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
    # Utilisation d'une clé unique pour éviter l'erreur de duplication
    admin_action = st.radio("Action :", ["Créer une fiche", "Modifier une fiche", "Supprimer une fiche"], key="admin_radio")
    
    if admin_action == "Créer une fiche":
        with st.form("form_creation_admin"):
            col1, col2 = st.columns(2)
            with col1:
                num_interne = st.text_input("Numéro interne")
                nom = st.text_input("Nom de l'article")
                fournisseur = st.text_input("Fournisseur")
            with col2:
                categorie = st.selectbox("Catégorie :", ["Catalogue EPI", "Catalogue Consommables", "Catalogue Outillage", "Catalogue Matériel Commun"])
                ref = st.text_input("Référence")
                num_serie = st.text_input("N° de Série")
            
            st.subheader("📅 Suivi et Maintenance")
            soumis_verif = st.checkbox("Soumis à contrôle ou étalonnage ?")
            date_c, perio = None, 0
            if soumis_verif:
                c1, c2 = st.columns(2)
                date_c = c1.date_input("Date du dernier contrôle")
                perio = c2.number_input("Périodicité (mois)", value=12)

            st.subheader("📸 Photo du matériel")
            source_photo = st.radio("Source :", ["Aucune", "Fichier", "Caméra"], horizontal=True, key="photo_source")
            if source_photo == "Fichier":
                uploaded_file = st.file_uploader("Déposer une image", type=['png', 'jpg'])
            elif source_photo == "Caméra":
                uploaded_file = st.camera_input("Prendre une photo")

            if st.form_submit_button("Enregistrer et générer QR Code"):
                try:
                    # Requête SQL
                    query = sqlalchemy.text("""
                        INSERT INTO materiel (id, nom, categorie, reference, num_serie, fournisseur, date_controle, intervalle_mois)
                        VALUES (:id, :nom, :cat, :ref, :serie, :fourn, :date_c, :perio)
                    """)
                    
                    with engine.begin() as conn:
                        conn.execute(query, {
                            "id": num_interne, "nom": nom, "cat": categorie, 
                            "ref": ref, "serie": num_serie, "fourn": fournisseur,
                            "date_c": date_c, "perio": perio
                        })
                    st.success(f"Fiche {num_interne} enregistrée !")
                    
                    # Génération URL pour QR Code
                    # Remplacez par votre lien réel
                    base_url = "https://votre-url-app.streamlit.app" 
                    lien_fiche = f"{base_url}/?materiel_id={num_interne}"
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={urllib.parse.quote(lien_fiche)}"
                    st.image(qr_url, caption="QR Code : Scannez pour accéder à la fiche")
                    
                except Exception as e:
                    st.error(f"Erreur technique : {e}")

    # --- BLOC MODIFICATION (Aligné avec le if précédent) ---
   elif admin_action == "Modifier une fiche":
        st.subheader("Sélectionner le matériel à modifier")
        
        # 1. On récupère la liste des IDs
        df_list = pd.read_sql("SELECT id FROM materiel", engine)
        id_selectionne = st.selectbox("Choisir l'ID :", df_list['id'].tolist(), key="select_mod")
        
        # 2. On récupère les données du matériel choisi
        donnees = pd.read_sql(f"SELECT * FROM materiel WHERE id = '{id_selectionne}'", engine).iloc[0]
        
        # 3. Formulaire de modification
        with st.form("form_mod_admin"):
            # Champs pré-remplis avec 'value=donnees[...]'
            nouveau_nom = st.text_input("Nom", value=donnees['nom'])
            nouvelle_ref = st.text_input("Référence", value=donnees.get('reference', ''))
            nouveau_fourn = st.text_input("Fournisseur", value=donnees.get('fournisseur', ''))
            
            if st.form_submit_button("Mettre à jour"):
                try:
                    query_upd = sqlalchemy.text("""
                        UPDATE materiel 
                        SET nom = :nom, reference = :ref, fournisseur = :fourn 
                        WHERE id = :id
                    """)
                    with engine.begin() as conn:
                        conn.execute(query_upd, {
                            "nom": nouveau_nom, "ref": nouvelle_ref, 
                            "fourn": nouveau_fourn, "id": id_selectionne
                        })
                    st.success(f"Matériel {id_selectionne} mis à jour !")
                    st.rerun() # Rafraîchit la page pour voir les changements
                except Exception as e:
                    st.error(f"Erreur : {e}")

    # --- BLOC SUPPRESSION ---
    elif admin_action == "Supprimer une fiche":
        st.write("Section suppression en cours...")
