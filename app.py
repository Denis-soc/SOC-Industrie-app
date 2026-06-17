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
    
    if not df_demandes_reel.empty:
        st.dataframe(df_demandes_reel, use_container_width=True, hide_index=True)
        
        # Formulaire d'action pour Olivier
        with st.form("action_olivier"):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                # Création d'une liste unique pour la sélection
                liste_demandes = df_demandes_reel.index.tolist()
                selection = st.selectbox("Sélectionner la ligne (ID) à traiter :", liste_demandes)
            with col_v2:
                action_decision = st.radio("Action :", ["Laisser en attente", "Valider / Matériel Prêt", "Supprimer"], horizontal=True)
                                           
            if st.form_submit_button("Confirmer l'action"):
                try:
                    with engine.begin() as conn:
                        if action_decision == "Supprimer":
                            conn.execute(sqlalchemy.text("DELETE FROM demandes_collaborateurs WHERE id = :id;"), {"id": selection})
                        elif action_decision == "Valider / Matériel Prêt":
                            conn.execute(sqlalchemy.text("UPDATE demandes_collaborateurs SET statut = :s WHERE id = :id;"), 
                                         {"s": "Validé", "id": selection})
                    st.success("Action effectuée avec succès !")
                    st.rerun() # Recharge la page pour mettre à jour le tableau
                except Exception as e:
                    st.error(f"Erreur lors de la mise à jour : {e}")
    else:
        st.success("✅ Aucune demande en attente.")

    st.markdown("---")
    
    # 2. Alertes étalonnage
    st.subheader("🚨 Alertes Étalonnages (< 90 jours)")
    aujourdhui = datetime.now().date()
    
    # On filtre les alertes
    if not df_materiel_reel.empty:
        df_materiel_reel['prochain_controle'] = pd.to_datetime(df_materiel_reel['prochain_controle']).dt.date
        alertes = df_materiel_reel[df_materiel_reel['prochain_controle'] <= (aujourdhui + pd.Timedelta(days=90))]
        
        if not alertes.empty:
            st.dataframe(alertes[['id', 'nom', 'prochain_controle']], use_container_width=True, hide_index=True)
        else:
            st.success("✅ Aucun étalonnage critique à prévoir.")
