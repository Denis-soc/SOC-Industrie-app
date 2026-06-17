import streamlit as st
import sqlalchemy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import urllib.parse
import base64

# 1. CONFIGURATION
st.set_page_config(page_title="SOC Industrie — Gestion Interne", page_icon="🏗️", layout="wide")
st.title("🏗️ SOC Industrie — Gestion Interne")

# 2. DÉFINITION DE LA CONNEXION (Doit être défini AVANT d'être appelé)
@st.cache_resource
def init_connection():
    # Remplacez "VotreMotDePasse" par votre vrai mot de passe Supabase
    db_url = "postgresql://postgres.spxrxmzeaybndgpmoslo:LesGaulois2026@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
    return sqlalchemy.create_engine(db_url)

# 3. INITIALISATION DU MOTEUR
try:
    engine = init_connection()
    with engine.connect() as conn:
        pass
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# 4. FONCTIONS DE CHARGEMENT
def charger_materiel():
    query = 'SELECT id AS "ID", nom AS "Nom", categorie AS "Catégorie", statut AS "Statut", detenteur AS "Détenteur", date_controle AS "Date Contrôle", intervalle_mois AS "Intervalle (mois)", prochain_controle AS "Prochain Contrôle", photo_base64 AS "Photo", marque AS "Marque", reference AS "Référence", num_serie AS "N° de Série" FROM materiel;'
    return pd.read_sql(query, engine)

def charger_demandes():
    query = 'SELECT date_demande AS "Date", collaborateur AS "Collaborateur", type_demande AS "Type", designation AS "Désignation", code_imputation AS "Code Imputation", details AS "Détails / Dates", statut AS "Statut" FROM demandes_collaborateurs;'
    return pd.read_sql(query, engine)

# 5. CHARGEMENT DES DONNÉES
df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

# 6. CRÉATION DES ONGLETS
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 ESPACE OLIVIER : Centralisation & Logistique",
    "🛒 CATALOGUE MAGASIN (EPI / Consommables)",
    "🛠️ CATALOGUE VISUEL & REGISTRE MATÉRIEL", 
    "📅 Sorties & Mouvements Terrain", 
    "📍 Carte des Chantiers"
])
# 5. Contenu des onglets
with tab0:
    st.header("👑 Tableau de Bord Olivier")
    # Maintenant, df_demandes_reel est bien défini et accessible
    if not df_demandes_reel.empty:
        st.dataframe(df_demandes_reel)
    else:
        st.success("✅ Aucune demande en attente.")
    
    st.markdown("---")
    
    # 2. Alertes étalonnage
    st.subheader("🚨 Alertes Étalonnages (< 90 jours)")
    aujourdhui = datetime.now().date()
    lignes_alertes = []
    
    for idx, row in df_materiel_reel.iterrows():
        # Conversion sécurisée de la date
        date_prox = row["Prochain Contrôle"]
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

with tab1:
    st.header("🛒 Catalogues EPI/Consommables/Outillage")
    st.write("Gestion des commandes.")

with tab2:
    st.header("📦 Matériels Commun")
    st.write("Gestion du matériel partagé.")

with tab3:
    st.header("📅 Réservation matériel")
    st.write("Suivi des réservations terrain.")

with tab4:
    st.header("📍 Carte de localisation du matériel")
    st.write("Visualisation des chantiers et du matériel sur le terrain.")
    # Exemple de carte interactive (à remplacer par vos données réelles)
    map_data = pd.DataFrame(
        np.random.randn(5, 2) / [50, 50] + [47.33, -0.40], 
        columns=['lat', 'lon']
    )
    st.map(map_data, zoom=10)
