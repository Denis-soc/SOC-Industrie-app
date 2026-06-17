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
elif admin_action == "Modifier une fiche":
        st.subheader("Modifier une fiche existante")
        
        # 1. Sélection du matériel
        df_list = pd.read_sql("SELECT id FROM materiel", engine)
        if not df_list.empty:
            id_select = st.selectbox("Sélectionner l'ID à modifier :", df_list['id'].tolist(), key="mod_sel")
            
            # 2. Chargement des données actuelles
            data = pd.read_sql(f"SELECT * FROM materiel WHERE id = '{id_select}'", engine).iloc[0]
            
            # 3. Formulaire de modification
            with st.form("form_mod_admin"):
                col1, col2 = st.columns(2)
                # Pré-remplissage avec les données existantes
                nouveau_nom = col1.text_input("Nom de l'article", value=data['nom'])
                nouveau_fourn = col1.text_input("Fournisseur", value=data.get('fournisseur', ''))
                nouvelle_ref = col2.text_input("Référence", value=data.get('reference', ''))
                nouveau_serie = col2.text_input("N° de Série", value=data.get('num_serie', ''))
                
                if st.form_submit_button("Mettre à jour"):
                    try:
                        query_upd = sqlalchemy.text("""
                            UPDATE materiel 
                            SET nom = :nom, fournisseur = :fourn, reference = :ref, num_serie = :serie 
                            WHERE id = :id
                        """)
                        with engine.begin() as conn:
                            conn.execute(query_upd, {
                                "nom": nouveau_nom, "fourn": nouveau_fourn, 
                                "ref": nouvelle_ref, "serie": nouveau_serie, "id": id_select
                            })
                        st.success(f"Matériel {id_select} mis à jour avec succès !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la mise à jour : {e}")
        else:
            st.warning("Aucun matériel trouvé en base.")
