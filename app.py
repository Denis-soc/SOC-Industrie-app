import streamlit as st
import pandas as pd
from supabase import create_client

# 1. CONFIGURATION
st.set_page_config(page_title="SOC Industrie – Gestion", page_icon="🏗️", layout="wide")

# 2. CONNEXION SUPABASE
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 3. CHARGEMENT DONNÉES
def charger_materiel():
    response = supabase.table("materiel").select("*").execute()
    return pd.DataFrame(response.data)

def charger_demandes():
    response = supabase.table("demandes_collaborateurs").select("*").execute()
    return pd.DataFrame(response.data)

# Initialisation des données
df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

# 4. INTERFACE
st.title("🏗️ SOC Industrie – Gestion Interne")

# Définition des onglets
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Tableau de Bord Olivier",
    "🛒 Catalogues EPI/Consommables/Outillage",
    "📦 Matériels Commun",
    "📅 Réservation matériel",
    "📍 Carte de localisation du matériel",
    "⚙️ Administration Matériel"
])
# 5. CONTENU DES ONGLES
with tab1:
    st.header("🛒 Catalogue des Équipements")

    # 1. Récupération des données depuis Supabase
    try:
        response = supabase.table("materiel").select("*").execute()
        df_cat = pd.DataFrame(response.data)

        if not df_cat.empty:
            # 2. Barre de recherche et Filtres en colonnes
            col_search, col_filter = st.columns([2, 1])
            
            with col_search:
                recherche = st.text_input("🔍 Rechercher un article (Nom, Marque...)", "")
            
            with col_filter:
                # On récupère les catégories uniques présentes dans la base
                categories = ["Toutes"] + sorted(df_cat["categorie"].unique().tolist())
                choix_cat = st.selectbox("Filtrer par catégorie", categories)

            # 3. Application des filtres
            df_filtre = df_cat.copy()
            
            if choix_cat != "Toutes":
                df_filtre = df_filtre[df_filtre["categorie"] == choix_cat]
            
            if recherche:
                # Recherche insensible à la casse dans la colonne 'nom'
                df_filtre = df_filtre[df_filtre["nom"].str.contains(recherche, case=False, na=False)]

            # 4. Affichage du résultat
            st.write(f"**{len(df_filtre)}** articles trouvés")
            
            # Configuration de l'affichage (on cache les colonnes techniques comme l'ID si besoin)
            st.dataframe(
                df_filtre, 
                use_container_width=True,
                column_config={
                    "id": None, # Cache l'ID
                    "quantite": st.column_config.NumberColumn("Stock", format="%d 📦"),
                    "nom": "Désignation",
                    "categorie": "Type"
                }
            )

        else:
            st.warning("Le catalogue est vide. Ajoutez du matériel dans l'onglet Administration.")

    except Exception as e:
        st.error(f"Erreur de chargement du catalogue : {e}")
with tab2:
    st.subheader("Matériels en stock")
    df_materiel = supabase.table("materiel").select("*").execute()
    st.dataframe(pd.DataFrame(df_materiel.data))
with tab5:
    st.header("⚙️ Administration du Matériel")
    
    with st.form("ajout_materiel_form"):
        nom = st.text_input("Nom du matériel")
        categorie = st.selectbox("Catégorie", ["EPI", "Consommable", "Outillage"])
        quantite = st.number_input("Quantité", min_value=0)
        
        submitted = st.form_submit_button("Ajouter à la base")
        
        if submitted:
            # Envoi vers Supabase
            data = {"nom": nom, "categorie": categorie, "quantite": quantite}
            supabase.table("materiel").insert(data).execute()
            
            st.success(f"{nom} a bien été ajouté au catalogue !")
            st.rerun() # Rafraîchit l'interface pour voir la mise à jour

# Répétez ce modèle pour tab2, tab3, etc. en changeant le nom de la table
