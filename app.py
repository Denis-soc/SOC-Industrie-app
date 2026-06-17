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

# 3. SIMULATION DU PARC MATÉRIEL
if 'db_materiel' not in st.session_state:
    st.session_state.db_materiel = pd.DataFrame([
        {
            "ID": "MAT-001", "Nom": "Meuleuse d'angle Ø230", "Catégorie": "Outillage Électroportatif", 
            "Statut": "En Chantier", "Détenteur": "Yannick", "Date Contrôle": datetime(2026, 1, 15).date(), 
            "Intervalle (mois)": 6, "Prochain Contrôle": datetime(2026, 7, 15).date()
        },
        {
            "ID": "MAT-002", "Nom": "Poste à souder TIG", "Catégorie": "Soudage", 
            "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": datetime(2025, 11, 10).date(), 
            "Intervalle (mois)": 12, "Prochain Contrôle": datetime(2026, 11, 10).date()
        },
        {
            "ID": "MAT-003", "Nom": "Appareil de métrologie", "Catégorie": "Mesure", 
            "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": datetime(2026, 5, 20).date(), 
            "Intervalle (mois)": 1, "Prochain Contrôle": datetime(2026, 6, 20).date()
        },
        {
            "ID": "MAT-004", "Nom": "Appareil test Tuyauterie Inox", "Catégorie": "Mesure", 
            "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": datetime(2026, 4, 1).date(), 
            "Intervalle (mois)": 4, "Prochain Contrôle": datetime(2026, 8, 1).date()
        }
    ])

# Séparation des modules par onglets (On place les Alertes d'Olivier en premier)
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "🚨 Espace Olivier : Alertes Étalonnage (-3 mois)",
    "🛠️ Registre & Gestion du Matériel", 
    "📅 Réservations & Logistique", 
    "🪵 Consommables & Stocks EPI", 
    "📍 Carte des Chantiers"
])

# ==========================================
# ONGLET 0 : ESPACE ALERTE OLIVIER (ANTICIPATION 3 MOIS)
# ==========================================
with tab0:
    st.header("🚨 Suivi des Échéances et Étalonnages à 3 mois")
    st.write("Cet espace permet à Olivier de visualiser les contrôles réglementaires dépassés ou à planifier dans les 90 prochains jours.")
    
    aujourdhui = datetime.now().date()
    horizon_3_mois = aujourdhui + timedelta(days=90)
    
    lignes_alertes = []
    
    for idx, row in st.session_state.db_materiel.iterrows():
        jours_restants = (row["Prochain Contrôle"] - aujourdhui).days
        
        # Filtre : On prend tout ce qui est dépassé OU qui arrive dans les 90 jours (3 mois)
        if jours_restants <= 90:
            if jours_restants < 0:
                Urgence = "🔴 DÉPASSÉ"
            elif jours_restants <= 30:
                Urgence = "🟠 Moins de 30 jours"
            else:
                Urgence = "🟡 Anticipation (1 à 3 mois)"
                
            lignes_alertes.append({
                "Urgence": Urgence,
                "ID": row["ID"],
                "Matériel": row["Nom"],
                "Détenteur Actuel": row["Détenteur"],
                "Date Limite": row["Prochain Contrôle"],
                "Jours Restants": jours_restants
            })
            
    if lignes_alertes:
        df_alertes = pd.DataFrame(lignes_alertes).sort_values(by="Jours Restants")
        
        # Affichage du résumé sous forme de compteurs visuels
        nb_critique = len(df_alertes[df_alertes["Jours Restants"] < 0])
        nb_trente_jours = len(df_alertes[(df_alertes["Jours Restants"] >= 0) & (df_alertes["Jours Restants"] <= 30)])
        nb_anticip = len(df_alertes[df_alertes["Jours Restants"] > 30])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Contrôles en RETARD 🔴", nb_critique)
        c2.metric("Échéances < 30 jours 🟠", nb_trente_jours)
        c3.metric("À planifier sous 3 mois 🟡", nb_anticip)
        
        st.subheader("📋 Liste des équipements à contrôler")
        st.dataframe(df_alertes, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Tout est en ordre ! Aucun matériel ne nécessite de contrôle dans les 3 prochains mois.")

# ==========================================
# ONGLET 1 : REGISTRE GENERAL
# ==========================================
with tab1:
    st.header("🛠️ Registre Général du Parc")
    st.dataframe(st.session_state.db_materiel, use_container_width=True)
    
    st.subheader("⚙️ Actions sur le parc")
    action = st.radio("Sélectionnez une action :", ["Ajouter un matériel", "Modifier / Étalonner un matériel", "Supprimer un matériel"], horizontal=True)
    
    if action == "Ajouter un matériel":
        with st.form("form_ajout"):
            col_a, col_b = st.columns(2)
            with col_a:
                new_id = st.text_input("Identifiant Unique (ex: MAT-005)")
                new_nom = st.text_input("Nom du matériel")
                new_cat = st.selectbox("Catégorie", ["Outillage Électroportatif", "Manutention", "Soudage", "Mesure"])
            with col_b:
                new_date = st.date_input("Date du dernier contrôle", aujourdhui)
                new_intervalle = st.number_input("Intervalle de contrôle (en mois)", min_value=1, value=12)
            
            if st.form_submit_button("Ajouter au parc"):
                prochain = new_date + timedelta(days=new_intervalle * 30)
                new_row = {
                    "ID": new_id, "Nom": new_nom, "Catégorie": new_cat, "Statut": "Disponible", 
                    "Détenteur": "Atelier / Agence", "Date Contrôle": new_date, "Intervalle (mois)": new_intervalle, "Prochain Contrôle": prochain
                }
                st.session_state.db_materiel = pd.concat([st.session_state.db_materiel, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Matériel enregistré.")
                st.rerun()

    elif action == "Modifier / Étalonner un matériel":
        mat_to_mod = st.selectbox("Choisir le matériel à modifier :", st.session_state.db_materiel["ID"] + " - " + st.session_state.db_materiel["Nom"])
        id_mod = mat_to_mod.split(" - ")[0]
        current_data = st.session_state.db_materiel[st.session_state.db_materiel["ID"] == id_mod].iloc[0]
        
        with st.form("form_modif"):
            col_c, col_d = st.columns(2)
            with col_c:
                mod_nom = st.text_input("Nom du matériel", value=current_data["Nom"])
                mod_statut = st.selectbox("Statut", ["Disponible", "En Chantier", "En Maintenance"], index=["Disponible", "En Chantier", "En Maintenance"].index(current_data["Statut"]))
                mod_detenteur = st.text_input("Détenteur actuel", value=current_data["Détenteur"])
            with col_d:
                mod_date = st.date_input("Date du dernier contrôle", value=current_data["Date Contrôle"])
                mod_intervalle = st.number_input("Intervalle (mois)", min_value=1, value=int(current_data["Intervalle (mois)"]))
            
            if st.form_submit_button("Enregistrer les modifications"):
                prochain_mod = mod_date + timedelta(days=mod_intervalle * 30)
                st.session_state.db_materiel.loc[st.session_state.db_materiel["ID"] == id_mod, ["Nom", "Statut", "Détenteur", "Date Contrôle", "Intervalle (mois)", "Prochain Contrôle"]] = [mod_nom, mod_statut, mod_detenteur, mod_date, mod_intervalle, prochain_mod]
                st.success("Fiche mise à jour.")
                st.rerun()

    elif action == "Supprimer un matériel":
        mat_to_del = st.selectbox("Choisir le matériel à retirer :", st.session_state.db_materiel["ID"] + " - " + st.session_state.db_materiel["Nom"])
        id_del = mat_to_del.split(" - ")[0]
        if st.button("⚠️ Confirmer la suppression"):
            st.session_state.db_materiel = st.session_state.db_materiel[st.session_state.db_materiel["ID"] != id_del]
            st.success("Supprimé.")
            st.rerun()

# ==========================================
# ONGLET 2 : RÉSERVATIONS & MOUVEMENTS
# ==========================================
with tab2:
    st.header("📅 Demandes d'Utilisation et Flux Matériel")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Nouvelle sortie matériel (Technicien)")
        with st.form("form_reservation"):
            tech_name = st.text_input("Nom du Technicien")
            mat_sel = st.selectbox("Matériel demandé", st.session_state.db_materiel[st.session_state.db_materiel["Statut"] == "Disponible"]["Nom"])
            st.date_input("Date de début")
            st.date_input("Date de fin prévue")
            
            if st.form_submit_button("Valider la sortie"):
                st.session_state.db_materiel.loc[st.session_state.db_materiel["Nom"] == mat_sel, ["Statut", "Détenteur"]] = ["En Chantier", tech_name]
                st.success(f"{mat_sel} affecté à {tech_name}.")
                st.rerun()

    with col2:
        st.subheader("🔄 Retour ou Transfert direct")
        mat_en_cours = st.selectbox("Matériel en mouvement :", st.session_state.db_materiel[st.session_state.db_materiel["Statut"] == "En Chantier"]["Nom"])
        mouvement = st.radio("Mouvement", ["Réintégration à l'agence", "Transfert à un collègue"])
        
        if mouvement == "Transfert à un collègue":
            receveur = st.text_input("Nom du collègue")
            
        if st.button("Valider le mouvement"):
            if mouvement == "Réintégration à l'agence":
                st.session_state.db_materiel.loc[st.session_state.db_materiel["Nom"] == mat_en_cours, ["Statut", "Détenteur"]] = ["Disponible", "Atelier / Agence"]
            else:
                st.session_state.db_materiel.loc[st.session_state.db_materiel["Nom"] == mat_en_cours, ["Détenteur"]] = [receveur]
            st.success("Mouvement enregistré.")
            st.rerun()

# ==========================================
# ONGLET 3 : CONSOMMABLES & EPI
# ==========================================
with tab3:
    st.header("🪵 Consommables & Stocks EPI")
    st.info("Formulaires et suivi des consommables de quincaillerie et des distributions d'EPI.")

# ==========================================
# ONGLET 4 : CARTOGRAPHIE
# ==========================================
with tab4:
    st.header("📍 Localisation du Matériel")
    map_data = pd.DataFrame(np.random.randn(3, 2) / [50, 50] + [47.33, -0.40], columns=['lat', 'lon'])
    st.map(map_data, zoom=10)

# Barre latérale
st.sidebar.image("https://img.icons8.com/clouds/100/000000/crane.png", width=60)
st.sidebar.title("Navigation")
st.sidebar.info("Application Interne v1.5 — SOC Industrie. Vue 'Anticipation Étalonnages 3 mois' active pour la direction.")
