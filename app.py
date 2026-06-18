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
    
    # Récupération sécurisée
    try:
        response = supabase.table("materiel").select("*").execute()
        df_admin = pd.DataFrame(response.data).fillna("").astype(str)
    except:
        df_admin = pd.DataFrame()

    mode = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

    # --- FONCTION FORMULAIRE COMPLÈTE ---
    def afficher_formulaire(item=None):
        with st.form("form_materiel"):
            col1, col2 = st.columns(2)
            with col1:
                num_int = st.text_input("N° Interne", value=item["num_interne"] if item else "", disabled=(item is not None))
                nom = st.text_input("Nom du matériel", value=item["Nom du Matériel"] if item else "")
                cat = st.selectbox("Catégorie", ["EPI", "Outillage", "Consommables", "Soudage", "Mesure"], 
                                   index=0) # Vous pouvez ajouter une logique d'index ici
                taille = st.text_input("Taille (si EPI)", value=item["taille"] if item and "taille" in item else "")
            with col2:
                ref = st.text_input("Référence", value=item["reference"] if item else "")
                num_serie = st.text_input("N° de série", value=item["num_serie"] if item and "num_serie" in item else "")
                fournisseur = st.text_input("Fournisseur", value=item["fournisseur"] if item and "fournisseur" in item else "")
                perio = st.number_input("Périodicité contrôle (mois)", value=int(float(item["periodicite_controle"])) if item and item.get("periodicite_controle") else 0)
                photo = st.file_uploader("Photo", type=['png', 'jpg', 'jpeg'])
            
            submit = st.form_submit_button("Valider")
            return submit, num_int, nom, cat, taille, ref, num_serie, fournisseur, perio, photo

    # --- LOGIQUE D'ACTION ---
   if mode == "Ajouter":
        submit, num, nom, cat, taille, ref, ns, fourn, perio, photo = afficher_formulaire()
        if submit:
            if not num:
                st.error("Le N° interne est obligatoire.")
            else:
                try:
                    url_photo = ""
                    # 1. Traitement de la photo
                    if photo is not None:
                        file_path = f"materiel/{num}.png"
                        # Upload
                        supabase.storage.from_("photos_materiel").upload(file_path, photo.getvalue(), {"upsert": "true"})
                        # Récupération de l'URL publique
                        url_photo = supabase.storage.from_("photos_materiel").get_public_url(file_path)
                        st.write(f"DEBUG: URL générée = {url_photo}") # À retirer une fois que ça marche
                    
                    # 2. Préparation des données
                    data = {
                        "num_interne": num,
                        "Nom du Matériel": nom,
                        "categorie": cat,
                        "taille": taille,
                        "reference": ref,
                        "num_serie": ns,
                        "fournisseur": fourn,
                        "periodicite_controle": perio,
                        "photo_url": url_photo  # Cette fois-ci, c'est bien transmis !
                    }
                    
                    # 3. Insertion
                    response = supabase.table("materiel").insert(data).execute()
                    st.success("Matériel ajouté avec succès !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'ajout : {e}")

    elif mode == "Modifier":
        if not df_admin.empty:
            selection = st.selectbox("Choisir le N° Interne à modifier", df_admin["num_interne"].tolist())
            item = df_admin[df_admin["num_interne"] == selection].iloc[0]
            
            submit, num, nom, cat, taille, ref, ns, fourn, perio, photo = afficher_formulaire(item=item)
            if submit:
                update_data = {"Nom du Matériel": nom, "categorie": cat, "taille": taille, "reference": ref, "num_serie": ns, "fournisseur": fourn, "periodicite_controle": perio}
                supabase.table("materiel").update(update_data).eq("num_interne", num).execute()
                st.success("Modifié !")
                st.rerun()
