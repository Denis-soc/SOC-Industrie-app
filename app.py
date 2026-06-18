import streamlit as st
import pandas as pd
import sqlalchemy
import base64

# --- FONCTION CATALOGUE ---
def afficher_catalogue(categorie_nom):
    try:
        query = f"SELECT * FROM materiel WHERE categorie = '{categorie_nom}'"
        df = pd.read_sql(query, engine)
        if df.empty:
            st.info(f"Aucun matériel trouvé dans : {categorie_nom}")
        else:
            for _, row in df.iterrows():
                with st.container(border=True):
                    st.subheader(row['nom'])
                    st.write(f"**Réf :** {row['reference']} | **Fournisseur :** {row['fournisseur']}")
    except Exception as e:
        st.error(f"Erreur catalogue : {e}")

# --- FONCTION FORMULAIRE (SANS PHOTO POUR STABILISER) ---
def afficher_formulaire(donnees=None):
    # Gestion sécurisée des données par défaut
    valeurs = {
        'id': "", 'nom': "", 'fournisseur': "", 'reference': "", 'num_serie': "", 
        'date_controle': None, 'intervalle_mois': 12, 'photo_data': None
    }
    if donnees is not None:
        valeurs.update(donnees.to_dict()) # Convertit la ligne SQL en dict

    with st.form("form_partage"):
        col1, col2 = st.columns(2)
        num_interne = col1.text_input("Numéro interne", value=valeurs['id'], disabled=(donnees is not None))
        nom = col1.text_input("Nom de l'article", value=valeurs['nom'])
        fournisseur = col1.text_input("Fournisseur", value=valeurs['fournisseur'])
        categorie = col2.selectbox("Catégorie :", ["Catalogue EPI", "Catalogue Consommables", "Catalogue Outillage", "Catalogue Matériel Commun"])
        ref = col2.text_input("Référence / Modèle", value=valeurs['reference'])
        num_serie = col2.text_input("N° de Série", value=valeurs['num_serie'])
        
        # Gestion Photo
        st.subheader("📸 Photo du matériel")
        if valeurs['photo_data']:
            st.image(base64.b64decode(valeurs['photo_data']), width=150, caption="Photo actuelle")
        uploaded_file = st.file_uploader("Modifier/Ajouter une image", type=['png', 'jpg'])
        
        # Bouton de soumission OBLIGATOIRE dans le form
        if st.form_submit_button("Enregistrer"):
            pdata = valeurs['photo_data']
            if uploaded_file:
                pdata = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
            
            with engine.begin() as conn:
                if donnees is None:
                    query = sqlalchemy.text("""INSERT INTO materiel (id, nom, categorie, fournisseur, reference, num_serie, photo_data) 
                                              VALUES (:id, :nom, :cat, :fourn, :ref, :serie, :pdata)""")
                    conn.execute(query, {"id": num_interne, "nom": nom, "cat": categorie, "fourn": fournisseur, "ref": ref, "serie": num_serie, "pdata": pdata})
                else:
                    query = sqlalchemy.text("""UPDATE materiel SET nom=:nom, categorie=:cat, fournisseur=:fourn, reference=:ref, 
                                              num_serie=:serie, photo_data=:pdata WHERE id=:id""")
                    conn.execute(query, {"nom": nom, "cat": categorie, "fourn": fournisseur, "ref": ref, "serie": num_serie, "pdata": pdata, "id": num_interne})
            st.success("Enregistré !")
            st.rerun()
      # 1. CONFIGURATION
st.set_page_config(page_title="SOC Industrie — Gestion", page_icon="🏗️", layout="wide")

# 2. CONNEXION BDD
@st.cache_resource
def init_connection():
    db_url = "postgresql://postgres.spxrxmzeaybndgpmoslo:LesGaulois2026@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
    return sqlalchemy.create_engine(db_url)

engine = init_connection()

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
# ... Onglet N°1...
# ... Onglet N°5...
with tab5:
    st.header("⚙️ Administration Matériel")
    admin_action = st.radio("Action :", ["Créer une fiche", "Modifier une fiche", "Supprimer une fiche"])

    if admin_action == "Créer une fiche":
        afficher_formulaire()
        
 elif admin_action == "Modifier une fiche":
        ids = pd.read_sql("SELECT id FROM materiel", engine)['id'].tolist()
        if ids:
            id_select = st.selectbox("Choisir l'ID :", ids)
            df_result = pd.read_sql(f"SELECT * FROM materiel WHERE id = '{id_select}'", engine)
            if not df_result.empty:
                afficher_formulaire(donnees=df_result.iloc[0])
            else:
                st.error("Données introuvables.")
            
    elif admin_action == "Supprimer une fiche":
        ids = pd.read_sql("SELECT id FROM materiel", engine)['id'].tolist()
        if ids:
            id_del = st.selectbox("ID à supprimer :", ids)
            if st.button("Confirmer"):
                with engine.begin() as conn:
                    conn.execute(sqlalchemy.text("DELETE FROM materiel WHERE id = :id"), {"id": id_del})
                st.rerun()
