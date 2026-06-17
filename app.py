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

    # --- FONCTION FORMULAIRE PARTAGÉ ---
    def afficher_formulaire(donnees=None):
        with st.form("form_partage"):
            col1, col2 = st.columns(2)
            
            # Pré-remplissage si 'donnees' existe
            id_val = donnees['id'] if donnees is not None else ""
            nom_val = donnees['nom'] if donnees is not None else ""
            ref_val = donnees['reference'] if donnees is not None else ""
            
            num_interne = col1.text_input("Numéro interne", value=id_val, disabled=(donnees is not None))
            nom = col1.text_input("Nom de l'article", value=nom_val)
            ref = col2.text_input("Référence", value=ref_val)
            
            btn_label = "Mettre à jour" if donnees is not None else "Enregistrer"
            
            if st.form_submit_button(btn_label):
                try:
                    with engine.begin() as conn:
                        if donnees is None: # Mode CRÉATION
                            query = sqlalchemy.text("INSERT INTO materiel (id, nom, reference) VALUES (:id, :nom, :ref)")
                            conn.execute(query, {"id": num_interne, "nom": nom, "ref": ref})
                            st.success("Matériel créé !")
                        else: # Mode MODIFICATION
                            query = sqlalchemy.text("UPDATE materiel SET nom = :nom, reference = :ref WHERE id = :id")
                            conn.execute(query, {"nom": nom, "ref": ref, "id": num_interne})
                            st.success("Matériel mis à jour !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

    # --- LOGIQUE D'ACTION ---
    if admin_action == "Créer une fiche":
        afficher_formulaire()
        
    elif admin_action == "Modifier une fiche":
        # 1. Sélectionner le matériel
        df_list = pd.read_sql("SELECT id FROM materiel", engine)
        id_select = st.selectbox("Choisir l'ID :", df_list['id'].tolist())
        
        # 2. Charger les données
        data = pd.read_sql(f"SELECT * FROM materiel WHERE id = '{id_select}'", engine).iloc[0]
        
        # 3. Afficher le formulaire rempli
        afficher_formulaire(donnees=data)
