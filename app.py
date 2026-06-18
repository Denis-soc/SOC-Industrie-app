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
    
    # 1. Récupération des données
    try:
        response = supabase.table("materiel").select("*").execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        df = pd.DataFrame()

    if not df.empty:
        # 2. Sélecteur de catalogue
        categories = ["Tous"] + df["categorie"].unique().tolist()
        cat_choisie = st.selectbox("Choisir le catalogue :", categories)
        df_filtre = df if cat_choisie == "Tous" else df[df["categorie"] == cat_choisie]
        
        # 3. Grille de 6 colonnes pour une vue dense (4x plus petit)
        cols = st.columns(6) 
        for i, (idx, row) in enumerate(df_filtre.reset_index().iterrows()):
            with cols[i % 6]:
                # Nom du matériel en petit
                st.caption(row.get("Nom du Matériel", "Sans nom"))
                
                # --- GESTION PHOTO RÉDUITE ---
                url = row.get("photo_url")
                if url and str(url).startswith("http"):
                    # width=100 fixe la taille en pixels pour garantir la réduction
                    st.image(url, width=100) 
                else:
                    st.warning("📷")
                
                # Détails compacts
                ref_val = str(row.get('reference') or '')
                st.write(f"Ref: {ref_val[:5]}...")
                
                if st.button("Détails", key=f"btn_{idx}"):
                    st.info(f"N°: {row.get('num_interne', '')}\nFourn: {row.get('fournisseur', '')}")
    else:
        st.info("Le catalogue est vide.")
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
    st.header("⚙️ Administration du Matériel")
    
    # 1. Récupération des données
    try:
        response = supabase.table("materiel").select("*").execute()
        df_admin = pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except:
        df_admin = pd.DataFrame()

    mode = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

    # 2. VOICI LE BLOC QUE VOUS CHERCHIEZ (À copier-coller)
    def afficher_form_complet(item=None):
        # Sécurisation : si 'item' est une ligne de DataFrame, on le convertit en dict
        item_dict = item.to_dict() if hasattr(item, 'to_dict') else item
        
        with st.form("form_gestion"):
            col1, col2 = st.columns(2)
            with col1:
                # Utilisation de .get() pour éviter les erreurs si la clé n'existe pas
                num = st.text_input("N° Interne", value=item_dict.get("num_interne", "") if item_dict else "", disabled=(item_dict is not None))
                nom = st.text_input("Nom du matériel", value=item_dict.get("Nom du Matériel", "") if item_dict else "")
            with col2:
                ref = st.text_input("Référence", value=item_dict.get("reference", "") if item_dict else "")
            
            submit = st.form_submit_button("Valider")
            return submit, num, nom, ref

    # 3. Utilisation dans la logique
    if mode == "Ajouter":
        submit, num, nom, ref = afficher_form_complet()
        if submit and num:
            supabase.table("materiel").insert({"num_interne": num, "Nom du Matériel": nom, "reference": ref}).execute()
            st.success("Ajouté !")
            st.rerun()

    elif mode == "Modifier":
        if not df_admin.empty:
            sel = st.selectbox("Sélectionner", df_admin["num_interne"].tolist())
            item = df_admin[df_admin["num_interne"] == sel].iloc[0]
            
            submit, num, nom, ref = afficher_form_complet(item=item)
            if submit:
                supabase.table("materiel").update({"Nom du Matériel": nom, "reference": ref}).eq("num_interne", num).execute()
                st.success("Modifié !")
                st.rerun()
