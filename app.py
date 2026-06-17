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

    # --- FONCTION FORMULAIRE (Partagé pour Création/Modification) ---
    def afficher_formulaire(donnees=None):
        with st.form("form_partage"):
            col1, col2 = st.columns(2)
            
            # Pré-remplissage en mode modification
            id_v = donnees['id'] if donnees is not None else ""
            nom_v = donnees['nom'] if donnees is not None else ""
            fourn_v = donnees['fournisseur'] if donnees is not None else ""
            ref_v = donnees['reference'] if donnees is not None else ""
            serie_v = donnees['num_serie'] if donnees is not None else ""
            
            num_interne = col1.text_input("Numéro interne", value=id_v, disabled=(donnees is not None))
            nom = col1.text_input("Nom de l'article", value=nom_v)
            fournisseur = col1.text_input("Fournisseur", value=fourn_v)
            
            ref = col2.text_input("Référence / Modèle", value=ref_v)
            num_serie = col2.text_input("N° de Série", value=serie_v)
            
            btn_label = "Mettre à jour" if donnees is not None else "Enregistrer"
            
            if st.form_submit_button(btn_label):
                try:
                    with engine.begin() as conn:
                        if donnees is None: # MODE CRÉATION
                            query = sqlalchemy.text("""
                                INSERT INTO materiel (id, nom, fournisseur, reference, num_serie) 
                                VALUES (:id, :nom, :fourn, :ref, :serie)
                            """)
                            conn.execute(query, {"id": num_interne, "nom": nom, "fourn": fournisseur, "ref": ref, "serie": num_serie})
                            st.success("Matériel créé avec succès !")
                        else: # MODE MODIFICATION
                            query = sqlalchemy.text("""
                                UPDATE materiel SET nom = :nom, fournisseur = :fourn, reference = :ref, num_serie = :serie 
                                WHERE id = :id
                            """)
                            conn.execute(query, {"nom": nom, "fourn": fournisseur, "ref": ref, "serie": num_serie, "id": num_interne})
                            st.success("Matériel mis à jour !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur technique : {e}")

    # --- LOGIQUE D'ACTION ---
    if admin_action == "Créer une fiche":
        afficher_formulaire()
        
    elif admin_action == "Modifier une fiche":
        df_list = pd.read_sql("SELECT id FROM materiel", engine)
        if not df_list.empty:
            id_select = st.selectbox("Choisir l'ID à modifier :", df_list['id'].tolist())
            data = pd.read_sql(f"SELECT * FROM materiel WHERE id = '{id_select}'", engine).iloc[0]
            afficher_formulaire(donnees=data)
        else:
            st.warning("Aucun matériel en base.")
            
    elif admin_action == "Supprimer une fiche":
        df_list = pd.read_sql("SELECT id FROM materiel", engine)
        id_del = st.selectbox("Choisir l'ID à supprimer :", df_list['id'].tolist())
        if st.button("Confirmer la suppression"):
            with engine.begin() as conn:
                conn.execute(sqlalchemy.text("DELETE FROM materiel WHERE id = :id"), {"id": id_del})
            st.success("Supprimé !")
            st.rerun()
