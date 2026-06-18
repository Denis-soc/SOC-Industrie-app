import streamlit as st
import sqlalchemy
import pandas as pd
from datetime import datetime
import urllib.parse

# 1. CONFIGURATION
st.set_page_config(page_title="SOC Industrie — Gestion", page_icon="🏗️", layout="wide")

# 2. CONNEXION BDD
from supabase import create_client

# 1. Initialisation avec les secrets (que vous venez de configurer)
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 3. CHARGEMENT DONNÉES
def charger_materiel():
    # Utilisation du client supabase au lieu de pd.read_sql
    response = supabase.table("materiel").select("*").execute()
    # On transforme la réponse en DataFrame pandas
    return pd.DataFrame(response.data)

def charger_demandes():
    # Même chose pour la table des demandes
    response = supabase.table("demandes_collaborateurs").select("*").execute()
    return pd.DataFrame(response.data)

# Initialisation sûre des données
# Ces variables sont maintenant alimentées par Supabase
df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

# Chargement initial
df_materiel_reel = charger_materiel()

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
with tab1: # Catalogue
    st.subheader("Catalogue Équipements")
    
    # Récupération des données depuis Supabase
    response = supabase.table("materiel").select("*").execute()
    df = pd.DataFrame(response.data)
    
    # Affichage interactif avec possibilité de filtrer
    st.dataframe(
        df, 
        column_config={
            "nom": "Matériel",
            "statut": st.column_config.SelectboxColumn("Statut", options=["Disponible", "En chantier", "Maintenance"]),
            "quantite": st.column_config.NumberColumn("Stock", min_value=0)
        },
        use_container_width=True
    )

    # Bouton pour ajouter un nouvel élément (simplifié)
    if st.button("Ajouter un nouvel équipement"):
        # Logique d'ajout ici
        st.write("Formulaire d'ajout à créer...")
with tab5:
    st.header("Administration du Matériel")
    
    with st.form("ajout_materiel_form"):
        nom = st.text_input("Nom du matériel")
        categorie = st.selectbox("Catégorie", ["EPI", "Consommable", "Outillage"])
        quantite = st.number_input("Quantité", min_value=0)
        
        submitted = st.form_submit_button("Ajouter à la base")
        
        if submitted:
            # Envoi vers Supabase
            data = supabase.table("materiel").insert({
                "nom": nom, 
                "categorie": categorie, 
                "quantite": quantite
            }).execute()
            
            st.success(f"{nom} a bien été ajouté au catalogue !")
            st.rerun() # Rafraîchit l'interface pour voir la mise à jour
