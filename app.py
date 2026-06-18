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
    
    # 1. Chargement et Nettoyage immédiat
    response = supabase.table("materiel").select("*").execute()
    df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
    
    if not df.empty:
        # Remplacer tous les NULL par du texte vide pour stabiliser le DataFrame
        df = df.fillna("")
        
        # 2. Filtrage pour ne garder que les articles valides (Nom non vide)
        df = df[df["Nom du Matériel"] != "Sans nom"]
        
        # Sélecteur
        cat_choisie = st.selectbox("Choisir le catalogue :", ["Tous"] + sorted(list(set(df["categorie"]))))
        df_filtre = df if cat_choisie == "Tous" else df[df["categorie"] == cat_choisie]
        
        # 3. Grille propre
        cols = st.columns(6)
        for i, (idx, row) in enumerate(df_filtre.reset_index().iterrows()):
            with cols[i % 6]:
                st.markdown(f"**{row['Nom du Matériel']}**")
                
                # Image seulement si URL valide
                url = str(row.get("photo_url", ""))
                if url.startswith("http"):
                    st.image(url, use_container_width=True)
                else:
                    # On affiche une zone vide de taille fixe pour garder l'alignement
                    st.write("") 
                
                st.caption(f"Ref: {row.get('reference', 'N/A')}")
                if st.button("Détails", key=f"btn_{idx}"):
                    st.info(f"N° Interne: {row.get('num_interne', '')}")
    else:
        st.write("Aucun matériel enregistré.")
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
    
    # 1. Chargement des données pour le selectbox
    response = supabase.table("materiel").select("num_interne, 'Nom du Matériel'").execute()
    liste_materiel = {item['num_interne']: item['Nom du Matériel'] for item in response.data}
    
    action = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

    with st.form("form_admin"):
        if action == "Ajouter":
            num = st.text_input("N° Interne (Unique)")
        else:
            num = st.selectbox("Choisir le matériel à gérer", list(liste_materiel.keys()), format_func=lambda x: f"{x} - {liste_materiel[x]}")
        
        nom = st.text_input("Nom du matériel")
        cat = st.selectbox("Catégorie", ["EPI", "Outillage", "Soudage", "Autre"])
        ref = st.text_input("Référence")
        url_photo = st.text_input("URL de la photo")
        
        submit = st.form_submit_button("Valider l'action")

    if submit and num:
        # Préparation du dictionnaire de données
        # Note: Nous utilisons le nom exact de la colonne dans votre base
        data = {
            "num_interne": num,
            "Nom du Matériel": nom,
            "categorie": cat,
            "reference": ref,
            "photo_url": url_photo
        }
        
        try:
            if action == "Ajouter":
                supabase.table("materiel").insert(data).execute()
                st.success(f"Article {num} ajouté avec succès !")
            
            elif action == "Modifier":
                supabase.table("materiel").update(data).eq("num_interne", num).execute()
                st.success(f"Article {num} modifié avec succès !")
            
            elif action == "Supprimer":
                supabase.table("materiel").delete().eq("num_interne", num).execute()
                st.success(f"Article {num} supprimé !")
            
            # Rafraîchissement pour voir les changements
            st.rerun()
            
        except Exception as e:
            st.error(f"Erreur lors de l'opération : {e}")
            st.write("Vérifiez que le nom de la colonne 'Nom du Matériel' correspond bien à la base.")
