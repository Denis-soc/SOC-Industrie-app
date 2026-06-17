import streamlit as st
import sqlalchemy
import pandas as pd
from datetime import datetime
import urllib.parse

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

tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 Tableau de Bord Olivier", 
    "🛒 Catalogues EPI/Consommables/Outillage", 
    "📦 Matériels Commun", 
    "📅 Réservation matériel",
    "📍 Carte de localisation du matériel"
])
# ... après la définition de tab0, tab1...

with tab0:
    st.header("👑 Tableau de Bord Olivier")
    
    # 1. Gestion des demandes
    st.subheader("📋 Demandes en attente")
    # On vérifie si df_demandes_reel existe [cite: 1]
    if not df_demandes_reel.empty:
        st.dataframe(df_demandes_reel, use_container_width=True, hide_index=True)
        
        # Interface de traitement
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            demande_a_traiter = st.selectbox("Sélectionner une ligne à traiter :", 
                                             df_demandes_reel["Collaborateur"] + " - " + df_demandes_reel["Désignation"], 
                                             key="sel_olivier")
        with col_v2:
            action_decision = st.radio("Action :", ["Laisser en attente", "Valider / Matériel Prêt", "Supprimer"], 
                                       horizontal=True, key="rad_olivier")
                                       
        if st.button("Confirmer l'action", key="btn_olivier"):
            collab_sel = demande_a_traiter.split(" - ")[0]
            desig_sel = demande_a_traiter.split(" - ")[1]
            
            with engine.begin() as conn_tx:
                if action_decision == "Supprimer":
                    conn_tx.execute(sqlalchemy.text("DELETE FROM demandes_collaborateurs WHERE collaborateur = :c AND designation = :d;"), 
                                    {"c": collab_sel, "d": desig_sel})
                elif action_decision != "Laisser en attente":
                    conn_tx.execute(sqlalchemy.text("UPDATE demandes_collaborateurs SET statut = :s WHERE collaborateur = :c AND designation = :d;"), 
                                    {"s": action_decision, "c": collab_sel, "d": desig_sel})
            st.rerun()
    else:
        st.success("✅ Aucune demande en attente.")

    st.markdown("---")
    
    # 2. Alertes étalonnage
    st.subheader("🚨 Alertes Étalonnages (< 90 jours)")
    aujourdhui = datetime.now().date()
    lignes_alertes = []
    
    for idx, row in df_materiel_reel.iterrows():
        date_prox = row["Prochain Contrôle"]
        # Conversion sécurisée des dates [cite: 1, 11]
        if isinstance(date_prox, str): 
            date_prox = datetime.strptime(date_prox, "%Y-%m-%d").date()
        elif isinstance(date_prox, datetime): 
            date_prox = date_prox.date()
            
        if (date_prox - aujourdhui).days <= 90:
            lignes_alertes.append({
                "ID": row["ID"], 
                "Matériel": row["Nom"], 
                "Détenteur": row["Détenteur"], 
                "Prochain Contrôle": date_prox
            })
            
    if lignes_alertes:
        st.dataframe(pd.DataFrame(lignes_alertes), use_container_width=True, hide_index=True)
    else:
        st.success("✅ Aucun étalonnage critique à prévoir.")
# 5. CONTENU TAB1 (Administration)
with tab1:
    mode = st.radio("Mode d'affichage :", ["Catalogue", "Administration"], horizontal=True)
    if mode == "Administration":
        action = st.selectbox("Action :", ["Créer une fiche", "Modifier une fiche", "Supprimer une fiche"])
        
        if action == "Créer une fiche":
            with st.form("form_creation"):
                col1, col2 = st.columns(2)
                with col1:
                    num_interne = st.text_input("Numéro interne (ex: MAT-001)")
                    nom = st.text_input("Nom de l'article")
                    categorie = st.selectbox("Catégorie :", ["EPI", "Outillage", "Consommables", "Matériel Commun"])
                with col2:
                    ref = st.text_input("Référence interne")
                    num_serie = st.text_input("N° de Série")
                
                st.subheader("📋 Suivi & Maintenance")
                soumis_verif = st.checkbox("Matériel soumis à vérification/étalonnage ?")
                periodicite, date_depart = 12, datetime.now().date()
                
                if soumis_verif:
                    c1, c2 = st.columns(2)
                    periodicite = c1.number_input("Périodicité (en mois)", min_value=1, value=12)
                    date_depart = c2.date_input("Date de départ")
                
                if st.form_submit_button("Enregistrer la fiche"):
                    query = "INSERT INTO materiel (id, nom, categorie, reference, num_serie, date_controle, intervalle_mois) VALUES (:id, :nom, :cat, :ref, :serie, :date_d, :perio)"
                    try:
                        with engine.begin() as conn:
                            conn.execute(sqlalchemy.text(query), {
                                "id": num_interne, "nom": nom, "cat": categorie, "ref": ref, 
                                "serie": num_serie, "date_d": date_depart, "perio": periodicite
                            })
                        st.success(f"Fiche {nom} créée !")
                    except Exception as e:
                        st.error(f"Erreur technique : {e}")
