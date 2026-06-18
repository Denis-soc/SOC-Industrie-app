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
    with st.form("form_partage"):
        col1, col2 = st.columns(2)
        
        # Valeurs par défaut
        id_v = donnees['id'] if donnees is not None else ""
        nom_v = donnees['nom'] if donnees is not None else ""
        fourn_v = donnees['fournisseur'] if donnees is not None else ""
        ref_v = donnees['reference'] if donnees is not None else ""
        serie_v = donnees['num_serie'] if donnees is not None else ""
        
        num_interne = col1.text_input("Numéro interne", value=id_v, disabled=(donnees is not None))
        nom = col1.text_input("Nom de l'article", value=nom_v)
        fournisseur = col1.text_input("Fournisseur", value=fourn_v)
        
        categorie = col2.selectbox("Catégorie :", ["Catalogue EPI", "Catalogue Consommables", "Catalogue Outillage", "Catalogue Matériel Commun"], index=0)
        ref = col2.text_input("Référence / Modèle", value=ref_v)
        num_serie = col2.text_input("N° de Série", value=serie_v)
        
        st.subheader("📅 Suivi et Maintenance")
        soumis_verif = st.checkbox("Soumis à contrôle ou étalonnage ?", key="maint_check")
        date_c, perio = None, 12
        if soumis_verif:
            c_m1, c_m2 = st.columns(2)
            date_c = c_m1.date_input("Date dernier contrôle")
            perio = c_m2.number_input("Périodicité (mois)", value=12)

        # BOUTON SOUMISSION
        btn_label = "Mettre à jour" if donnees is not None else "Enregistrer"
        if st.form_submit_button(btn_label):
            with engine.begin() as conn:
                if donnees is None:
                    query = sqlalchemy.text("INSERT INTO materiel (id, nom, categorie, fournisseur, reference, num_serie, date_controle, intervalle_mois) VALUES (:id, :nom, :cat, :fourn, :ref, :serie, :date_c, :perio)")
                    conn.execute(query, {"id": num_interne, "nom": nom, "cat": categorie, "fourn": fournisseur, "ref": ref, "serie": num_serie, "date_c": date_c, "perio": perio})
                else:
                    query = sqlalchemy.text("UPDATE materiel SET nom=:nom, categorie=:cat, fournisseur=:fourn, reference=:ref, num_serie=:serie, date_controle=:date_c, intervalle_mois=:perio WHERE id=:id")
                    conn.execute(query, {"nom": nom, "cat": categorie, "fourn": fournisseur, "ref": ref, "serie": num_serie, "date_c": date_c, "perio": perio, "id": num_interne})
            st.success("Opération réussie !")
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
            data = pd.read_sql(f"SELECT * FROM materiel WHERE id = '{id_select}'", engine).iloc[0]
            afficher_formulaire(donnees=data)
        else:
            st.warning("Aucune donnée.")
            
    elif admin_action == "Supprimer une fiche":
        ids = pd.read_sql("SELECT id FROM materiel", engine)['id'].tolist()
        if ids:
            id_del = st.selectbox("ID à supprimer :", ids)
            if st.button("Confirmer"):
                with engine.begin() as conn:
                    conn.execute(sqlalchemy.text("DELETE FROM materiel WHERE id = :id"), {"id": id_del})
                st.rerun()
