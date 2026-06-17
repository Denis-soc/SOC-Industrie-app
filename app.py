import streamlit as st
import pandas as pd
import sqlalchemy
import numpy as np

# ... (Après vos imports et st.set_page_config)

# 1. Connexion (Engine)
engine = init_connection()

# 2. Définition des fonctions de chargement
def charger_materiel():
    query = 'SELECT ... FROM materiel;' # Votre requête ici
    return pd.read_sql(query, engine)

def charger_demandes():
    query = 'SELECT ... FROM demandes_collaborateurs;' # Votre requête ici
    return pd.read_sql(query, engine)

# 3. INITIALISATION DES DONNÉES (CRUCIAL)
# Ces deux lignes doivent être placées ICI, avant la création des onglets
try:
    df_materiel_reel = charger_materiel()
    df_demandes_reel = charger_demandes()
except Exception as e:
    st.error("Erreur lors du chargement des données. Vérifiez votre connexion SQL.")
    st.stop()

# 4. Création des onglets
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 Tableau de Bord Olivier", 
    "🛒 Catalogues EPI/Consommables/Outillage", 
    "📦 Matériels Commun", 
    "📅 Réservation matériel",
    "📍 Carte de localisation du matériel"
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
