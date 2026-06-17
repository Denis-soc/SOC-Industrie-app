import streamlit as st
import sqlalchemy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="SOC Industrie — Gestion Interne",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ SOC Industrie — Gestion Interne")

# 2. CONNEXION À LA BASE DE DONNÉES (POOLER)
@st.cache_resource
def init_connection():
    db_url = "postgresql://postgres.spxrxmzeaybndgpmoslo:LesGaulois2026@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
    return sqlalchemy.create_engine(db_url)

try:
    engine = init_connection()
    conn = engine.connect()
    st.success("Connexion établie avec succès via le Pooler !")
except Exception as e:
    st.error(f"Erreur de connexion à la base de données : {e}")
    st.stop()

# 3. SIMULATION D'UNE BASE DE DONNÉES LOCALE POUR LE MATÉRIEL
# (Pour que l'interface soit 100% fonctionnelle immédiatement avant l'écriture des tables SQL)
if 'db_materiel' not in st.session_state:
    st.session_state.db_materiel = pd.DataFrame([
        {
            "ID": "MAT-001", "Nom": "Meuleuse d'angle Ø230", "Catégorie": "Outillage Électroportatif", 
            "Statut": "En Chantier", "Détenteur": "Yannick (Site Angers)", "Date Contrôle": datetime(2026, 1, 15).date(), 
            "Intervalle (mois)": 6, "Prochain Contrôle": datetime(2026, 7, 15).date()
        },
        {
            "ID": "MAT-002", "Nom": "Poste à souder TIG", "Catégorie": "Soudage", 
            "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": datetime(2025, 11, 10).date(), 
            "Intervalle (mois)": 12, "Prochain Contrôle": datetime(2026, 11, 10).date()
        },
        {
            "ID": "MAT-003", "Nom": "Appareil de métrologie / Étalonnage", "Catégorie": "Mesure", 
            "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": datetime(2026, 5, 20).date(), 
            "Intervalle (mois)": 1, "Prochain Contrôle": datetime(2026, 6, 20).date()
        }
    ])

# Séparation des modules par onglets
tab1, tab2, tab3, tab4 = st.tabs([
    "🛠️ Gestion & Étalonnage du Matériel", 
    "📅 Réservations & Logistique", 
    "🪵 Consommables & Stocks EPI", 
    "📍 Carte des Chantiers"
])

# ==========================================
# ONGLET 1 : GESTION DU MATÉRIEL (AJOUT, MODIF, SUPPR, ÉTALONNAGE)
# ==========================================
with tab1:
    st.header("🛠️ Registre et Suivi des Étalonnages")
    
    # --- SECTION ALERTES ÉTALONNAGE ---
    st.subheader("⚠️ Alertes de Contrôle Périodique")
    aujourdhui = datetime.now().date()
    alertes = []
    
    for idx, row in st.session_state.db_materiel.iterrows():
        jours_restants = (row["Prochain Contrôle"] - aujourdhui).days
        if jours_restants <= 0:
            st.error(f"🔴 **{row['Nom']} ({row['ID']})** : Étalonnage dépassé depuis {abs(jours_restants)} jours ! (Dû le {row['Prochain Contrôle']})")
        elif jours_restants <= 15:
            st.warning(f"🟡 **{row['Nom']} ({row['ID']})** : Contrôle obligatoire dans {jours_restants} jours (le {row['Prochain Contrôle']})")
            
    # --- TABLEAU DE BORD PRINCIPAL ---
    st.subheader("📋 Liste du parc matériel")
    st.dataframe(st.session_state.db_materiel, use_container_width=True)
    
    # --- ACTIONS : AJOUTER, MODIFIER, SUPPRIMER ---
    st.subheader("⚙️ Actions sur le parc")
    action = st.radio("Sélectionnez une action :", ["Ajouter un matériel", "Modifier / Étalonner un matériel", "Supprimer un matériel"], horizontal=True)
    
    if action == "Ajouter un matériel":
        with st.form("form_ajout"):
            col_a, col_b = st.columns(2)
            with col_a:
                new_id = st.text_input("Identifiant Unique (ex: MAT-004)")
                new_nom = st.text_input("Nom du matériel")
                new_cat = st.selectbox("Catégorie", ["Outillage Électroportatif", "Manutention", "Soudage", "Équipement Chantier", "Mesure"])
            with col_b:
                new_date = st.date_input("Date d'achat ou du dernier contrôle", aujourdhui)
                new_intervalle = st.number_input("Intervalle de contrôle (en mois)", min_value=1, max_value=36, value=12)
            
            if st.form_submit_button("Ajouter au parc"):
                prochain = new_date + timedelta(days=new_intervalle * 30)
                new_row = {
                    "ID": new_id, "Nom": new_nom, "Catégorie": new_cat, "Statut": "Disponible", 
                    "Détenteur": "Atelier / Agence", "Date Contrôle": new_date, "Intervalle (mois)": new_intervalle, "Prochain Contrôle": prochain
                }
                st.session_state.db_materiel = pd.concat([st.session_state.db_materiel, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Matériel {new_nom} ajouté avec succès ! Prochain contrôle programmé le {prochain}.")
                st.rerun()

    elif action == "Modifier / Étalonner un matériel":
        mat_to_mod = st.selectbox("Choisir le matériel à modifier :", st.session_state.db_materiel["ID"] + " - " + st.session_state.db_materiel["Nom"])
        id_mod = mat_to_mod.split(" - ")[0]
        
        # Récupération des données actuelles
        current_data = st.session_state.db_materiel[st.session_state.db_materiel["ID"] == id_mod].iloc[0]
        
        with st.form("form_modif"):
            col_c, col_d = st.columns(2)
            with col_c:
                mod_nom = st.text_input("Nom du matériel", value=current_data["Nom"])
                mod_statut = st.selectbox("Statut", ["Disponible", "En Chantier", "En Maintenance"], index=["Disponible", "En Chantier", "En Maintenance"].index(current_data["Statut"]))
                mod_detenteur = st.text_input("Détenteur actuel", value=current_data["Détenteur"])
            with col_d:
                mod_date = st.date_input("Date du dernier contrôle / Étalonnage", value=current_data["Date Contrôle"])
                mod_intervalle = st.number_input("Intervalle de contrôle (mois)", min_value=1, value=int(current_data["Intervalle (mois)"]))
            
            if st.form_submit_button("Enregistrer les modifications"):
                prochain_mod = mod_date + timedelta(days=mod_intervalle * 30)
                st.session_state.db_materiel.loc[st.session_state.db_materiel["ID"] == id_mod, ["Nom", "Statut", "Détenteur", "Date Contrôle", "Intervalle (mois)", "Prochain Contrôle"]] = [mod_nom, mod_statut, mod_detenteur, mod_date, mod_intervalle, prochain_mod]
                st.success("Fiche matériel mise à jour.")
                st.rerun()

    elif action == "Supprimer un matériel":
        mat_to_del = st.selectbox("Choisir le matériel à retirer définitivement :", st.session_state.db_materiel["ID"] + " - " + st.session_state.db_materiel["Nom"])
        id_del = mat_to_del.split(" - ")[0]
        
        if st.button("⚠️ Confirmer la suppression définitive"):
            st.session_state.db_materiel = st.session_state.db_materiel[st.session_state.db_materiel["ID"] != id_del]
            st.success("Matériel supprimé du registre.")
            st.rerun()

# ==========================================
# ONGLET 2 : RÉSERVATIONS & MOUVEMENTS LOGISTIQUES
# ==========================================
with tab2:
    st.header("📅 Demandes d'Utilisation et Flux Matériel")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Nouvelle demande d'utilisation (Technicien)")
        with st.form("form_reservation"):
            tech_name = st.text_input("Nom du Technicien / Demandeur")
            mat_sel = st.selectbox("Matériel demandé", st.session_state.db_materiel[st.session_state.db_materiel["Statut"] == "Disponible"]["Nom"])
            date_deb = st.date_input("Date de début d'utilisation")
            date_f = st.date_input("Date de fin prévue")
            
            if st.form_submit_button("Valider la sortie matériel"):
                # Mise à jour automatique du détenteur et du statut dans le tableau général
                st.session_state.db_materiel.loc[st.session_state.db_materiel["Nom"] == mat_sel, ["Statut", "Détenteur"]] = ["En Chantier", tech_name]
                st.success(f"Logistique : {mat_sel} est maintenant affecté à {tech_name}.")
                st.rerun()

    with col2:
        st.subheader("🔄 Retour ou Transfert de Matériel")
        mat_en_cours = st.selectbox("Sélectionner le matériel en mouvement :", st.session_state.db_materiel[st.session_state.db_materiel["Statut"] == "En Chantier"]["Nom"])
        
        mouvement = st.radio("Quel est le mouvement ?", ["Réintégration à l'agence", "Transfert direct à un collègue"])
        
        if mouvement == "Transfert direct à un collègue":
            receveur = st.text_input("Nom du collègue qui récupère le matériel")
            
        if st.button("Valider le mouvement logistique"):
            if mouvement == "Réintégration à l'agence":
                st.session_state.db_materiel.loc[st.session_state.db_materiel["Nom"] == mat_en_cours, ["Statut", "Détenteur"]] = ["Disponible", "Atelier / Agence"]
                st.success(f"Le matériel {mat_en_cours} a été réintégré à l'atelier.")
            else:
                st.session_state.db_materiel.loc[st.session_state.db_materiel["Nom"] == mat_en_cours, ["Détenteur"]] = [receveur]
                st.success(f"Le matériel {mat_en_cours} a été transféré à {receveur} directement sur site.")
            st.rerun()

# ==========================================
# ONGLET 3 : CONSOMMABLES & STOCKS EPI
# ==========================================
with tab3:
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("🪵 Création de Consommable")
        with st.form("form_consommable"):
            st.text_input("Désignation du consommable (ex: Électrodes Inox)")
            st.selectbox("Type", ["Fournitures Atelier", "Gaz & Soudure", "Visserie"])
            st.number_input("Quantité initiale", value=100)
            st.form_submit_button("Ajouter au stock")

    with col4:
        st.subheader("🦺 Création et Stocks EPI")
        with st.form("form_epi_stock"):
            st.text_input("Désignation de l'EPI")
            st.number_input("Quantité disponible", value=50)
            st.form_submit_button("Mettre à jour le stock EPI")

# ==========================================
# ONGLET 4 : GÉOLOCALISATION
# ==========================================
with tab4:
    st.header("📍 Localisation du Matériel")
    map_data = pd.DataFrame(np.random.randn(3, 2) / [50, 50] + [47.33, -0.40], columns=['lat', 'lon'])
    st.map(map_data, zoom=10)

# Barre latérale
st.sidebar.image("https://img.icons8.com/clouds/100/000000/crane.png", width=60)
st.sidebar.title("Navigation")
st.sidebar.info("Application Interne v1.4 — SOC Industrie. Gestion complète du parc, des détenteurs et des alertes de métrologie.")
