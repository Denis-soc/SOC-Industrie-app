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
        df_cat = pd.DataFrame(response.data)

        if not df_cat.empty:
            # Recherche et filtres
            col_search, col_filter = st.columns([2, 1])
            with col_search:
                recherche = st.text_input("🔍 Rechercher un article", "")
            with col_filter:
                categories = ["Toutes"] + sorted(df_cat["categorie"].unique().tolist())
                choix_cat = st.selectbox("Filtrer par catégorie", categories)

            # Application filtres
            df_filtre = df_cat.copy()
            if choix_cat != "Toutes":
                df_filtre = df_filtre[df_filtre["categorie"] == choix_cat]
            if recherche:
                df_filtre = df_filtre[df_filtre["nom"].str.contains(recherche, case=False, na=False)]

            st.write(f"**{len(df_filtre)}** articles trouvés")
            
            # Affichage du tableau
            st.dataframe(df_filtre, use_container_width=True)

            # --- CORRECTION ICI : Affichage des photos sous le tableau ---
            st.subheader("Aperçu des articles")
            for index, row in df_filtre.iterrows():
                col_img, col_data = st.columns([1, 4])
                with col_img:
                    if 'photo_url' in row and row['photo_url']:
                        st.image(row['photo_url'], width=100)
                    else:
                        st.write("📷 Pas de photo")
                with col_data:
                    st.write(f"**{row['nom']}** ({row['categorie']})")
        else:
            st.warning("Le catalogue est vide.")

    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
with tab2:
    st.subheader("Matériels en stock")
    df_materiel = supabase.table("materiel").select("*").execute()
    st.dataframe(pd.DataFrame(df_materiel.data))
with tab5:
    st.header("⚙️ Ajout de Matériel")
    
    with st.form("ajout_complet_photo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            categorie = st.selectbox("Sélectionner le catalogue", ["EPI", "Consommable", "Outillage", "Électroportatif"])
            nom = st.text_input("Nom du matériel")
            ref_materiel = st.text_input("Référence matériel")
            num_interne = st.text_input("N° Interne (unique)")
            
        with col2:
            taille = st.text_input("Taille (si EPI)")
            num_serie = st.text_input("N° de Série")
            date_achat = st.date_input("Date d'achat / dernier étalonnage")
            periodicite = st.number_input("Périodicité contrôle (en mois)", min_value=0)
            
        # Nouveau champ : st.file_uploader permet de choisir un fichier ou de prendre une photo
        photo_file = st.file_uploader("Prendre une photo ou télécharger une image", type=['png', 'jpg', 'jpeg'])
        
        submitted = st.form_submit_button("Ajouter au catalogue")
        
        if submitted:
            # 1. Vérification du nom obligatoire
            if not nom:
                st.error("Le nom du matériel est obligatoire.")
                st.stop()

            # 2. Préparation des données textuelles
            st.write("Données envoyées à Supabase :", data)
            data = {
                "categorie": categorie,
                "nom": nom,
                "ref_materiel": ref_materiel,
                "num_interne": num_interne,
                "taille": taille,
                "num_serie": num_serie,
                "date_achat_etalonnage": str(date_achat),
                "periodicite_controle": periodicite
            }

            # 3. Logique d'envoi de l'image (si présente)
            if photo_file is not None:
                try:
                    # On crée un nom de fichier unique (ex: materiel-123.jpg)
                    import uuid
                    file_extension = photo_file.name.split('.')[-1]
                    file_name = f"materiel-{uuid.uuid4()}.{file_extension}"
                    
                    # Envoi du fichier vers le bucket 'photos_materiel'
                    # (Vous devez créer ce bucket 'photos_materiel' dans Supabase !)
                    with st.spinner("Téléchargement de l'image..."):
                        # Lecture du fichier comme binaire
                        file_data = photo_file.read()
                        
                        supabase.storage.from_("photos_materiel").upload(
                            path=file_name,
                            file=file_data,
                            file_options={"content-type": f"image/{file_extension}"}
                        )
                        
                        # On récupère l'URL publique pour la stocker dans la table
                        # (N'oubliez pas d'ajouter une colonne 'photo_url' type text dans votre table 'materiel' !)
                        photo_url = supabase.storage.from_("photos_materiel").get_public_url(file_name)
                        data["photo_url"] = photo_url
                        
                except Exception as e:
                    st.error(f"Erreur technique lors de l'upload de l'image : {e}")
                    st.stop()

            # 4. Insertion dans la table 'materiel'
            try:
                supabase.table("materiel").insert(data).execute()
                st.success(f"Matériel '{nom}' ajouté avec succès dans la catégorie : {categorie} !")
                # Optionnel : pour afficher un petit aperçu si l'upload a réussi
                if photo_file:
                    st.image(photo_file, caption="Photo enregistrée", width=150)
                st.rerun() # Rafraîchit l'interface pour vider le formulaire
            except Exception as e:
                st.error(f"Erreur technique lors de l'insertion en base de données : {e}")
