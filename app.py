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
    admin_action = st.radio("Action :", ["Créer une fiche", "Modifier une fiche", "Supprimer une fiche"], key="main_radio")

    # Fonction qui dessine le formulaire (vide ou rempli)
    def afficher_formulaire(donnees=None):
        with st.form("form_partage"):
            col1, col2 = st.columns(2)
            # Si 'donnees' existe, on pré-remplit les champs
            id_val = donnees['id'] if donnees else ""
            nom_val = donnees['nom'] if donnees else ""
            # ... (idem pour les autres champs)
            
            num_interne = col1.text_input("Numéro interne", value=id_val, disabled=(donnees is not None))
            nom = col1.text_input("Nom de l'article", value=nom_val)
            # ... le reste des champs
            
            btn_label = "Mettre à jour" if donnees else "Enregistrer"
            if st.form_submit_button(btn_label):
                # Logique INSERT ou UPDATE ici
                pass

    if admin_action == "Créer une fiche":
        afficher_formulaire() # Appelé sans données = mode création
        
    elif admin_action == "Modifier une fiche":
        id_select = st.selectbox("Choisir l'ID :", ...)
        data = pd.read_sql(f"SELECT * FROM materiel WHERE id = '{id_select}'", engine).iloc[0]
        afficher_formulaire(donnees=data) # Appelé avec données = mode modification
    # --- BLOC CRÉATION ---
    if admin_action == "Créer une fiche":
        with st.form("form_creation_admin"):
            col1, col2 = st.columns(2)
            with col1:
                num_interne = st.text_input("Numéro interne", key="in_id")
                nom = st.text_input("Nom de l'article", key="in_nom")
                fournisseur = st.text_input("Fournisseur", key="in_fourn")
            with col2:
                categorie = st.selectbox(
                    "Catégorie :", 
                    ["Catalogue EPI", "Catalogue Consommables", "Catalogue Outillage", "Catalogue Matériel Commun"], 
                    key="in_cat"
                )
                ref = st.text_input("Référence", key="in_ref")
                num_serie = st.text_input("N° de Série", key="in_serie")
            
            # --- maintenance ---
            st.subheader("📅 Suivi et Maintenance")
            soumis_verif = st.checkbox("Soumis à contrôle ou étalonnage ?", key="check_ctrl")
            date_c, perio = None, 0
            if soumis_verif:
                c1, c2 = st.columns(2)
                date_c = c1.date_input("Date du dernier contrôle")
                perio = c2.number_input("Périodicité (mois)", value=12)

            # --- photo ---
            st.subheader("📸 Photo du matériel")
            source_photo = st.radio("Source :", ["Aucune", "Fichier", "Caméra"], horizontal=True, key="photo_source_admin")
            if source_photo == "Fichier":
                st.file_uploader("Déposer une image", type=['png', 'jpg'], key="file_upload_admin")
            elif source_photo == "Caméra":
                st.camera_input("Prendre une photo", key="camera_admin")

            # --- soumission ---
            if st.form_submit_button("Enregistrer"):
                try:
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
                    st.success("Fiche créée avec succès !")
                except Exception as e:
                    st.error(f"Erreur technique : {e}")



    elif admin_action == "Supprimer une fiche":
        st.subheader("⚠️ Supprimer un matériel")
        
        # 1. On récupère la liste des IDs pour choisir ce qu'on supprime
        df_list = pd.read_sql("SELECT id FROM materiel", engine)
        id_a_supprimer = st.selectbox("Sélectionner l'ID à supprimer :", df_list['id'].tolist(), key="select_del")
        
        # 2. Bouton de confirmation (sécurité indispensable pour éviter les erreurs)
        if st.button("Confirmer la suppression définitive"):
            try:
                query_del = sqlalchemy.text("DELETE FROM materiel WHERE id = :id")
                with engine.begin() as conn:
                    conn.execute(query_del, {"id": id_a_supprimer})
                st.success(f"Le matériel {id_a_supprimer} a été supprimé.")
                st.rerun() # Recharge pour mettre à jour la liste
            except Exception as e:
                st.error(f"Erreur lors de la suppression : {e}")
