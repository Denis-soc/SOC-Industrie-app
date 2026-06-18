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
        if not df_admin.empty:
            df_admin = df_admin.fillna("").astype(str)
    except Exception as e:
        st.error(f"Erreur connexion base : {e}")
        df_admin = pd.DataFrame()

    mode = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

    # 2. Formulaire unique pour Ajouter et Modifier
    def afficher_form_complet(item=None):
        with st.form("form_gestion"):
            col1, col2 = st.columns(2)
            with col1:
                num = st.text_input("N° Interne", value=item["num_interne"] if item else "", disabled=(item is not None))
                nom = st.text_input("Nom du matériel", value=item["Nom du Matériel"] if item else "")
                cat = st.selectbox("Catégorie", ["EPI", "Outillage", "Consommables", "Soudage", "Mesure"], index=0)
                taille = st.text_input("Taille (si EPI)", value=item.get("taille", "") if item else "")
            with col2:
                ref = st.text_input("Référence", value=item.get("reference", "") if item else "")
                ns = st.text_input("N° de série", value=item.get("num_serie", "") if item else "")
                fourn = st.text_input("Fournisseur", value=item.get("fournisseur", "") if item else "")
                perio = st.number_input("Périodicité (mois)", value=int(float(item.get("periodicite_controle", 0))) if item else 0)
                photo = st.file_uploader("Photo", type=['png', 'jpg', 'jpeg'])
            
            submit = st.form_submit_button("Valider")
            return submit, num, nom, cat, taille, ref, ns, fourn, perio, photo

    # 3. Logique des actions
    if mode == "Ajouter":
        submit, num, nom, cat, taille, ref, ns, fourn, perio, photo = afficher_form_complet()
        if submit and num:
            data = {"num_interne": num, "Nom du Matériel": nom, "categorie": cat, "taille": taille, "reference": ref, "num_serie": ns, "fournisseur": fourn, "periodicite_controle": perio}
            supabase.table("materiel").insert(data).execute()
            st.success("Matériel ajouté !")
            st.rerun()

    elif mode == "Modifier":
        if not df_admin.empty:
            selection = st.selectbox("Choisir le N° Interne", df_admin["num_interne"].tolist())
            item = df_admin[df_admin["num_interne"] == selection].iloc[0]
            submit, num, nom, cat, taille, ref, ns, fourn, perio, photo = afficher_form_complet(item=item)
            if submit:
                upd = {"Nom du Matériel": nom, "categorie": cat, "taille": taille, "reference": ref, "num_serie": ns, "fournisseur": fourn, "periodicite_controle": perio}
                supabase.table("materiel").update(upd).eq("num_interne", num).execute()
                st.success("Modifié !")
                st.rerun()

    elif mode == "Supprimer":
        if not df_admin.empty:
            choix = st.selectbox("Supprimer le N° Interne", df_admin["num_interne"].tolist())
            if st.button("Confirmer la suppression"):
                supabase.table("materiel").delete().eq("num_interne", choix).execute()
                st.rerun()
