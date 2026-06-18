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
    st.header("📋 Catalogue du Matériel")
    
    # Récupération brute
    response = supabase.table("materiel").select("*").execute()
    df = pd.DataFrame(response.data) if response.data is not None else pd.DataFrame()

    if not df.empty:
        # Nettoyage automatique des colonnes vides
        df = df.fillna("") 
        
        # Sélecteur de catégorie
        categories = ["Tous"] + sorted([c for c in df["categorie"].unique() if c != ""])
        cat_choisie = st.selectbox("Choisir le catalogue :", categories)
        
        df_filtre = df if cat_choisie == "Tous" else df[df["categorie"] == cat_choisie]
        
        cols = st.columns(6)
        for i, (idx, row) in enumerate(df_filtre.reset_index().iterrows()):
            with cols[i % 6]:
                st.caption(f"**{row.get('Nom du Matériel', 'Sans nom')}**")
                
                # Affichage image avec fallback
                url = row.get("photo_url")
                if url and str(url).startswith("http"):
                    st.image(url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150?text=Pas+d'image", use_container_width=True)
                
                st.write(f"Ref: {row.get('reference', 'N/A')}")
                if st.button("Détails", key=f"btn_{row.get('num_interne', i)}"):
                    st.info(f"N° Interne: {row.get('num_interne', 'N/A')}")
    else:
        st.info("Aucun matériel trouvé.")
with tab2:
    st.header("📋 Suivi des Contrôles & Étalonnages")
    
    try:
        response = supabase.table("materiel").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            df = df.fillna(0) # Remplace les cases vides par 0
            
            # Filtre : Matériel avec une périodicité définie
            df_suivi = df[df['periodicite_controle'].astype(int) > 0]
            
            st.write("Voici la liste du matériel nécessitant un suivi régulier :")
            
            # Affichage sous forme de tableau
            st.dataframe(
                df_suivi[['num_interne', 'Nom du Matériel', 'reference', 'periodicite_controle']],
                use_container_width=True
            )
            
            st.info("💡 Les alertes de contrôle automatique seront bientôt ajoutées ici.")
        else:
            st.info("Aucun matériel dans la base.")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
with tab5:
    st.header("⚙️ Administration")
    mode = st.radio("Action", ["Ajouter", "Modifier"], horizontal=True)
    
    # Formulaire simplifié
    with st.form("form_admin"):
        num = st.text_input("N° Interne")
        nom = st.text_input("Nom du matériel")
        cat = st.selectbox("Catégorie", ["EPI", "Outillage", "Soudage"])
        ref = st.text_input("Référence")
        url_photo = st.text_input("URL de la photo (lien http)") # <--- Testez en collant un lien ici
        
        submit = st.form_submit_button("Enregistrer")

    if submit:
        data = {
            "num_interne": num,
            "Nom du Matériel": nom,
            "categorie": cat,
            "reference": ref,
            "photo_url": url_photo  # <--- Indispensable pour que l'image apparaisse
        }
        
        if mode == "Ajouter":
            supabase.table("materiel").insert(data).execute()
        else:
            supabase.table("materiel").update(data).eq("num_interne", num).execute()
            
        st.success("Opération effectuée !")
        st.rerun()
