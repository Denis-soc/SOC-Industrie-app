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
    
    # 1. Chargement et nettoyage
    try:
        response = supabase.table("materiel").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df = df.fillna("").astype(str)
            
            # 2. Recherche
            recherche = st.text_input("🔍 Rechercher un matériel", "")
            if recherche:
                df = df[df['Nom du Matériel'].str.contains(recherche, case=False, na=False)]
            
            # 3. Affichage en Grille (3 colonnes)
            st.write("---")
            cols = st.columns(3) # Création de 3 colonnes pour la grille
            
            for index, row in df.iterrows():
                # On utilise le modulo pour faire tourner les colonnes (col 0, 1, 2, 0, 1...)
                with cols[index % 3]:
                    # Affichage photo si disponible, sinon une icône par défaut
                    if 'photo_url' in row and row['photo_url'] not in ['None', 'nan', '']:
                        st.image(row['photo_url'], use_column_width=True)
                    else:
                        st.warning("📷 Pas de photo")
                    
                    # Infos sous la photo
                    st.markdown(f"**{row['Nom du Matériel']}**")
                    st.caption(f"Catégorie: {row['categorie']}")
                    st.caption(f"ID: {row['num_interne']}")
                    
                    if st.button(f"Voir détail", key=f"btn_{index}"):
                        st.info(f"Détails pour {row['Nom du Matériel']}...")
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
            
        photo_file = st.file_uploader("Prendre une photo ou télécharger une image", type=['png', 'jpg', 'jpeg'])
        
        submitted = st.form_submit_button("Ajouter au catalogue")
        
        if submitted:
            # Préparation des données - ATTENTION : les clés doivent correspondre aux noms dans Supabase
            data = {
                "categorie": categorie,
                "Nom du Matériel": nom, # D'après votre visualiseur, la colonne s'appelle "Nom du Matériel"
                "reference": ref_materiel,
                "num_interne": num_interne,
                "taille": taille,
                "num_serie": num_serie,
                "date_achat_etalonnage": str(date_achat),
                "periodicite_controle": periodicite
            }

            # Gestion photo
            if photo_file is not None:
                try:
                    import uuid
                    file_extension = photo_file.name.split('.')[-1]
                    file_name = f"materiel-{uuid.uuid4()}.{file_extension}"
                    file_data = photo_file.read()
                    
                    supabase.storage.from_("photos_materiel").upload(file_name, file_data)
                    data["photo_url"] = supabase.storage.from_("photos_materiel").get_public_url(file_name)
                except Exception as e:
                    st.error(f"Erreur image: {e}")
                    st.stop()

            # Insertion
            try:
                supabase.table("materiel").insert(data).execute()
                st.success("Matériel ajouté avec succès !")
            except Exception as e:
                st.error(f"Erreur lors de l'insertion : {e}")
