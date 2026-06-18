import streamlit as st
import pandas as pd
from supabase import create_client
import uuid # Mettez-le ici avec les autres imports

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
    
    try:
        response = supabase.table("materiel").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            df = df.fillna("").astype(str)
            
            # Filtres
            col1, col2 = st.columns(2)
            with col1:
                categories = ["Toutes"] + sorted(df['categorie'].unique().tolist())
                choix_cat = st.selectbox("Filtrer par catégorie", categories)
            with col2:
                recherche = st.text_input("🔍 Rechercher un matériel", "")
            
            # Application des filtres
            df_filtre = df.copy()
            if choix_cat != "Toutes":
                df_filtre = df_filtre[df_filtre['categorie'] == choix_cat]
            if recherche:
                df_filtre = df_filtre[df_filtre['Nom du Matériel'].str.contains(recherche, case=False, na=False)]
            
            st.write(f"--- *{len(df_filtre)} article(s) affiché(s)* ---")
            
            # Affichage Grille
            cols = st.columns(3)
            for i, (idx, row) in enumerate(df_filtre.reset_index().iterrows()):
                with cols[i % 3]:
                    # Affichage photo
                    if 'photo_url' in row and row['photo_url'] not in ['None', 'nan', '']:
                        st.image(row['photo_url'], use_column_width=True)
                    else:
                        st.warning("📷 Pas de photo")
                    
                    st.markdown(f"**{row['Nom du Matériel']}**")
                    st.caption(f"Catégorie: {row['categorie']}")
                    st.caption(f"ID: {row['num_interne']}")
                    
                    if st.button(f"Voir détail", key=f"btn_{i}"):
                        st.info("Fonctionnalité en cours de développement.")
                    st.write("---")
        else:
            st.info("Le catalogue est vide.")
            
    except Exception as e:
        st.error(f"Erreur : {e}")
with tab2:
    st.subheader("Matériels en stock")
    df_materiel = supabase.table("materiel").select("*").execute()
    st.dataframe(pd.DataFrame(df_materiel.data))
with tab5:
    st.header("⚙️ Administration du Matériel")
    
    # 1. Choix du mode : Ajout, Modification ou Suppression
    mode = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)
    
    # Récupération des données pour les menus déroulants
    try:
        response = supabase.table("materiel").select("*").execute()
        df_admin = pd.DataFrame(response.data)
        liste_materiel = df_admin["Nom du Matériel"].tolist() if not df_admin.empty else []
    except:
        liste_materiel = []

    # --- AJOUT ---
    if mode == "Ajouter":
        with st.form("ajout_form"):
            # ... (Utilisez ici le même formulaire d'ajout que précédemment)
            st.info("Utilisez le formulaire d'ajout habituel.")
            # (Vous pouvez copier-coller votre bloc d'ajout ici)

    # --- MODIFICATION ---
    elif mode == "Modifier":
        choix = st.selectbox("Sélectionner le matériel à modifier", liste_materiel)
        if choix:
            item = df_admin[df_admin["Nom du Matériel"] == choix].iloc[0]
            with st.form("modif_form"):
                nouveau_nom = st.text_input("Nouveau nom", value=item["Nom du Matériel"])
                nouvelle_cat = st.selectbox("Catégorie", ["EPI", "Outillage", "Consommables"], index=0)
                submit_modif = st.form_submit_button("Enregistrer les modifications")
                
                if submit_modif:
                    supabase.table("materiel").update({"Nom du Matériel": nouveau_nom, "categorie": nouvelle_cat}).eq("num_interne", item["num_interne"]).execute()
                    st.success("Fiche mise à jour !")

    # --- SUPPRESSION ---
    elif mode == "Supprimer":
        choix_supp = st.selectbox("Sélectionner le matériel à supprimer", liste_materiel)
        if st.button("Confirmer la suppression définitive"):
            item_supp = df_admin[df_admin["Nom du Matériel"] == choix_supp].iloc[0]
            supabase.table("materiel").delete().eq("num_interne", item_supp["num_interne"]).execute()
            st.warning(f"{choix_supp} a été supprimé.")
            st.rerun() # Rafraîchit l'interface pour voir la suppression
