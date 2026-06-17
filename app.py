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

# 3. INITIALISATION DES BASES DE DONNÉES TEMPORAIRES (SESSION STATE)
# Parc Matériel principal
if 'db_materiel' not in st.session_state:
    st.session_state.db_materiel = pd.DataFrame([
        {"ID": "MAT-001", "Nom": "Meuleuse d'angle Ø230", "Catégorie": "Outillage Électroportatif", "Statut": "En Chantier", "Détenteur": "Yannick", "Date Contrôle": datetime(2026, 1, 15).date(), "Intervalle (mois)": 6, "Prochain Contrôle": datetime(2026, 7, 15).date()},
        {"ID": "MAT-002", "Nom": "Poste à souder TIG", "Catégorie": "Soudage", "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": datetime(2025, 11, 10).date(), "Intervalle (mois)": 12, "Prochain Contrôle": datetime(2026, 11, 10).date()},
        {"ID": "MAT-003", "Nom": "Appareil de métrologie", "Catégorie": "Mesure", "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": datetime(2026, 5, 20).date(), "Intervalle (mois)": 1, "Prochain Contrôle": datetime(2026, 6, 20).date()}
    ])

# Registre central des demandes des collaborateurs pour Olivier
if 'db_demandes_collaborateurs' not in st.session_state:
    st.session_state.db_demandes_collaborateurs = pd.DataFrame([
        {"Date": "15/06/2026", "Collaborateur": "Yannick", "Type": "🦺 EPI", "Désignation": "Gants de soudure T10", "Détails / Dates": "Urgents - Usés sur chantier", "Statut": "En attente"},
        {"Date": "16/06/2026", "Collaborateur": "David", "Type": "🪵 Consommable", "Désignation": "Électrodes Inox Ø2.5", "Détails / Dates": "2 paquets pour Chantier Angers", "Statut": "En attente"},
        {"Date": "17/06/2026", "Collaborateur": "Mathieu", "Type": "🛠️ Outillage", "Désignation": "Poste à souder TIG", "Détails / Dates": "Du 22/06 au 26/06", "Statut": "En attente"}
    ])


# Répartition des modules par Onglets
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 ESPACE OLIVIER : Centralisation & Alertes",
    "🛠️ Registre & Gestion du Matériel", 
    "📅 Sorties & Mouvements Terrain", 
    "🪵 Consommables & Stocks EPI", 
    "📍 Carte des Chantiers"
])

# ==========================================
# ONGLET 0 : ESPACE OLIVIER (CENTRALISATION TOTALE)
# ==========================================
with tab0:
    st.header("👑 Tableau de Bord Général d'Olivier")
    st.write("Suivi des obligations réglementaires et validation des demandes logistiques des collaborateurs.")
    
    # --- PARTIE A : RÉCAPITULATIF DES DEMANDES ÉQUIPES ---
    st.subheader("📥 Demandes de Matériels, EPI et Consommables reçues")
    if not st.session_state.db_demandes_collaborateurs.empty:
        # Affichage du tableau des demandes
        st.dataframe(st.session_state.db_demandes_collaborateurs, use_container_width=True, hide_index=True)
        
        # Actions de validation rapide
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            demande_a_traiter = st.selectbox("Sélectionner une demande à traiter :", 
                                             st.session_state.db_demandes_collaborateurs["Collaborateur"] + " - " + st.session_state.db_demandes_collaborateurs["Désignation"])
        with col_v2:
            action_decision = st.radio("Décision :", ["Valider / Prêt pour départ", "Refuser / Non disponible", "Supprimer la ligne traitée"], horizontal=True)
            
        if st.button("Confirmer le traitement de la demande"):
            idx_demande = st.session_state.db_demandes_collaborateurs[
                (st.session_state.db_demandes_collaborateurs["Collaborateur"] == demande_a_traiter.split(" - ")[0]) & 
                (st.session_state.db_demandes_collaborateurs["Désignation"] == demande_a_traiter.split(" - ")[1])
            ].index
            
            if action_decision == "Supprimer la ligne traitée":
                st.session_state.db_demandes_collaborateurs = st.session_state.db_demandes_collaborateurs.drop(idx_demande).reset_index(drop=True)
                st.success("Ligne archivée.")
            else:
                st.session_state.db_demandes_collaborateurs.loc[idx_demande, "Statut"] = action_decision
                st.success(f"Statut mis à jour : {action_decision}")
            st.rerun()
    else:
        st.success("✅ Aucune demande en attente de préparation.")

    st.markdown("---")
    
    # --- PARTIE B : ALERTES ÉTALONNAGE (-3 MOIS) ---
    st.subheader("🚨 Alertes Étalonnages et Contrôles Périodiques (< 90 jours)")
    aujourdhui = datetime.now().date()
    lignes_alertes = []
    
    for idx, row in st.session_state.db_materiel.iterrows():
        jours_restants = (row["Prochain Contrôle"] - aujourdhui).days
        if jours_restants <= 90:
            if jours_restants < 0:
                Urgence = "🔴 DÉPASSÉ"
            elif jours_restants <= 30:
                Urgence = "🟠 Moins de 30 jours"
            else:
                Urgence = "🟡 Dans les 3 mois"
                
            lignes_alertes.append({
                "Urgence": Urgence, "ID": row["ID"], "Matériel": row["Nom"],
                "Détenteur Actuel": row["Détenteur"], "Date Limite": row["Prochain Contrôle"], "Jours Restants": jours_restants
            })
            
    if lignes_alertes:
        df_alertes = pd.DataFrame(lignes_alertes).sort_values(by="Jours Restants")
        c1, c2, c3 = st.columns(3)
        c1.metric("Contrôles en RETARD 🔴", len(df_alertes[df_alertes["Jours Restants"] < 0]))
        c2.metric("Échéances < 30 jours 🟠", len(df_alertes[(df_alertes["Jours Restants"] >= 0) & (df_alertes["Jours Restants"] <= 30)]))
        c3.metric("À planifier sous 3 mois 🟡", len(df_alertes[df_alertes["Jours Restants"] > 30]))
        st.dataframe(df_alertes, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Aucun étalonnage à prévoir d'ici 3 mois.")


# ==========================================
# ONGLET 1 : REGISTRE GENERAL MATÉRIEL
# ==========================================
with tab1:
    st.header("🛠️ Registre Général du Parc Matériel")
    st.dataframe(st.session_state.db_materiel, use_container_width=True, hide_index=True)
    
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
                new_row = {"ID": new_id, "Nom": new_nom, "Catégorie": new_cat, "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": new_date, "Intervalle (mois)": new_intervalle, "Prochain Contrôle": prochain}
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
                mod_statut = st.selectbox("Statut", ["Disponible", "En Chantier", "En Maintenance"])
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
# ONGLET 2 : SORTIES & MOUVEMENTS (ALIMENTE L'ESPACE OLIVIER)
# ==========================================
with tab2:
    st.header("📅 Demandes d'Utilisation et Transferts")
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.subheader("🎯 Poser une option / Demande d'Outillage")
        with st.form("form_demande_outillage"):
            nom_tech_out = st.text_input("Nom du Technicien")
            out_choisi = st.selectbox("Matériel souhaité", st.session_state.db_materiel["Nom"])
            date_d = st.date_input("Date de début")
            date_f = st.date_input("Date de fin")
            
            if st.form_submit_button("Envoyer la demande à Olivier"):
                nouvelle_demande = {
                    "Date": datetime.now().strftime("%d/%m/%m"),
                    "Collaborateur": nom_tech_out, "Type": "🛠️ Outillage",
                    "Désignation": out_choisi, "Détails / Dates": f"Du {date_d} au {date_f}", "Statut": "En attente"
                }
                st.session_state.db_demandes_collaborateurs = pd.concat([st.session_state.db_demandes_collaborateurs, pd.DataFrame([nouvelle_demande])], ignore_index=True)
                st.success("Demande d'outillage transmise dans l'Espace d'Olivier !")

    with col_m2:
        st.subheader("🔄 Mouvements directs (Retour / Transfert)")
        mat_en_cours = st.selectbox("Matériel en mouvement (Sur chantier) :", st.session_state.db_materiel[st.session_state.db_materiel["Statut"] == "En Chantier"]["Nom"], key="mvmt")
        mouvement = st.radio("Mouvement", ["Réintégration à l'agence", "Transfert à un collègue"], key="rad_mv")
        if movimiento := (mouvement == "Transfert à un collègue"):
            receveur = st.text_input("Nom du collègue qui récupère")
            
        if st.button("Valider le mouvement"):
            if mouvement == "Réintégration à l'agence":
                st.session_state.db_materiel.loc[st.session_state.db_materiel["Nom"] == mat_en_cours, ["Statut", "Détenteur"]] = ["Disponible", "Atelier / Agence"]
            else:
                st.session_state.db_materiel.loc[st.session_state.db_materiel["Nom"] == mat_en_cours, ["Détenteur"]] = [receveur]
            st.success("Mouvement enregistré.")
            st.rerun()


# ==========================================
# ONGLET 3 : CONSUMIBLES & EPI (ALIMENTE L'ESPACE OLIVIER)
# ==========================================
with tab3:
    st.header("🪵 Demandes de Consommables & Dotations EPI")
    st.write("Section réservée aux techniciens pour déclarer leurs besoins avant de passer à l'agence.")
    
    col_e1, col_e2 = st.columns(2)
    
    with col_e1:
        st.subheader("🦺 Demander un Équipement de Protection (EPI)")
        with st.form("form_demande_epi"):
            nom_tech_epi = st.text_input("Nom du Collaborateur")
            epi_demande = st.text_input("EPI nécessaire (ex: Chaussures de sécu T43, Lunettes)")
            raison_epi = st.text_input("Motif / Précision", "Renouvellement annuel / Vol / Perte")
            
            if st.form_submit_button("Transmettre la demande d'EPI"):
                nouvelle_demande = {
                    "Date": datetime.now().strftime("%d/%m/%Y"),
                    "Collaborateur": nom_tech_epi, "Type": "🦺 EPI",
                    "Désignation": epi_demande, "Détails / Dates": raison_epi, "Statut": "En attente"
                }
                st.session_state.db_demandes_collaborateurs = pd.concat([st.session_state.db_demandes_collaborateurs, pd.DataFrame([nouvelle_demande])], ignore_index=True)
                st.success("Demande d'EPI envoyée dans l'Espace d'Olivier !")

    with col_e2:
        st.subheader("📦 Demander du Consommable (Quincaillerie / Soudure)")
        with st.form("form_demande_cons"):
            nom_tech_cons = st.text_input("Nom du Collaborateur", key="tech_c")
            cons_demande = st.text_input("Désignation du consommable & Quantité (ex: 5 disques à tronçonner Ø125)")
            chantier_cons = st.text_input("Chantier concerné")
            
            if st.form_submit_button("Transmettre la demande de stock"):
                nouvelle_demande = {
                    "Date": datetime.now().strftime("%d/%m/%Y"),
                    "Collaborateur": nom_tech_cons, "Type": "🪵 Consommable",
                    "Désignation": cons_demande, "Détails / Dates": f"Pour Chantier : {chantier_cons}", "Statut": "En attente"
                }
                st.session_state.db_demandes_collaborateurs = pd.concat([st.session_state.db_demandes_collaborateurs, pd.DataFrame([nouvelle_demande])], ignore_index=True)
                st.success("Besoin consommable envoyé dans l'Espace d'Olivier !")


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
st.sidebar.info("Application Interne v1.6 — SOC Industrie. Le guichet unique logistique d'Olivier est maintenant actif.")
