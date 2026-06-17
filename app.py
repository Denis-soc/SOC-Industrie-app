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
if 'db_materiel' not in st.session_state:
    st.session_state.db_materiel = pd.DataFrame([
        {"ID": "MAT-001", "Nom": "Meuleuse d'angle Ø230", "Catégorie": "Outillage Électroportatif", "Statut": "En Chantier", "Détenteur": "Yannick", "Date Contrôle": datetime(2026, 1, 15).date(), "Intervalle (mois)": 6, "Prochain Contrôle": datetime(2026, 7, 15).date()},
        {"ID": "MAT-002", "Nom": "Poste à souder TIG", "Catégorie": "Soudage", "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": datetime(2025, 11, 10).date(), "Intervalle (mois)": 12, "Prochain Contrôle": datetime(2026, 11, 10).date()},
        {"ID": "MAT-003", "Nom": "Appareil de métrologie", "Catégorie": "Mesure", "Statut": "Disponible", "Détenteur": "Atelier / Agence", "Date Contrôle": datetime(2026, 5, 20).date(), "Intervalle (mois)": 1, "Prochain Contrôle": datetime(2026, 6, 20).date()}
    ])

if 'db_demandes_collaborateurs' not in st.session_state:
    st.session_state.db_demandes_collaborateurs = pd.DataFrame([
        {"Date": "15/06/2026", "Collaborateur": "Yannick", "Type": "🦺 EPI", "Désignation": "Gants de soudure T10", "Code Imputation": "CH-MILLET-2025", "Détails / Dates": "Taille: L x1", "Statut": "En attente"},
        {"Date": "16/06/2026", "Collaborateur": "David", "Type": "🪵 Consommable", "Désignation": "Électrodes Inox Ø2.5", "Code Imputation": "CH-ANGERS-2026", "Détails / Dates": "Boîte de 50 x2", "Statut": "En attente"}
    ])

# INITIALISATION DU PANIER COLLABORATEUR
if 'panier' not in st.session_state:
    st.session_state.panier = []

# DEFINITION DU CATALOGUE EPI & CONSOMMABLES (Avec vrais détails et photos d'illustration)
CATALOGUE = [
    {
        "id": "EPI-01", "type": "🦺 EPI", "nom": "Gants de soudure Haute Protection", "marque": "Singer Safety",
        "ref": "TIG-500", "tailles": ["M (8)", "L (9)", "XL (10)", "XXL (11)"], "photo": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=150&q=80",
        "desc": "Cuir de chèvre supérieur, coutures Kevlar. Idéal pour soudure TIG/MIG."
    },
    {
        "id": "EPI-02", "type": "🦺 EPI", "nom": "Chaussures de Sécurité S3 Basse", "marque": "Caterpillar",
        "ref": "CAT-LITE", "tailles": ["41", "42", "43", "44", "45"], "photo": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=150&q=80",
        "desc": "Coque composite sans métal, semelle anti-perforation, imperméable."
    },
    {
        "id": "EPI-03", "type": "🦺 EPI", "nom": "Casque de chantier avec Visière", "marque": "Petzl",
        "ref": "VERTEX-BEST", "tailles": ["Taille Unique"], "photo": "https://images.unsplash.com/photo-1508962914676-134849a727f0?w=150&q=80",
        "desc": "Protection optimale pour les travaux en hauteur et l'industrie."
    },
    {
        "id": "CON-01", "type": "🪵 Consommable", "nom": "Électrodes de Soudage Inox Ø2.5", "marque": "Gys",
        "ref": "E308L-16", "tailles": ["Étui de 50 pièces", "Blister de 10 pièces"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150&q=80",
        "desc": "Électrodes enrobées rutiles pour le soudage des aciers inoxydables."
    },
    {
        "id": "CON-02", "type": "🪵 Consommable", "nom": "Disque à tronçonner Acier/Inox Ø125", "marque": "Norton Abrasifs",
        "ref": "NOR-125-1", "tailles": ["Lot de 5 disques", "Boîte de 25 disques"], "photo": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=150&q=80",
        "desc": "Épaisseur 1mm pour une coupe ultra-rapide et précise sans bavure."
    }
]

# Répartition des modules par Onglets
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 ESPACE OLIVIER : Centralisation & Logistique",
    "🛒 CATALOGUE & MAGASIN (EPI / Consommables)",
    "🛠️ Registre & Gestion du Matériel", 
    "📅 Sorties & Mouvements Terrain", 
    "📍 Carte des Chantiers"
])

# ==========================================
# ONGLET 0 : ESPACE OLIVIER (RECEPTION DES COMMANDES DU PANIER)
# ==========================================
with tab0:
    st.header("👑 Tableau de Bord Logistique d'Olivier")
    st.write("Retrouvez ici les étalonnages prioritaires ainsi que les bons de commande complets générés par le catalogue.")
    
    st.subheader("📥 Bons de commande et demandes reçus")
    if not st.session_state.db_demandes_collaborateurs.empty:
        st.dataframe(st.session_state.db_demandes_collaborateurs, use_container_width=True, hide_index=True)
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            demande_a_traiter = st.selectbox("Sélectionner une ligne à archiver / traiter :", 
                                             st.session_state.db_demandes_collaborateurs["Collaborateur"] + " - " + st.session_state.db_demandes_collaborateurs["Désignation"])
        with col_v2:
            action_decision = st.radio("Action :", ["Laisser en attente", "Valider / Matériel Prêt", "Supprimer / Archiver la ligne"], horizontal=True)
            
        if st.button("Confirmer l'action"):
            idx_demande = st.session_state.db_demandes_collaborateurs[
                (st.session_state.db_demandes_collaborateurs["Collaborateur"] == demande_a_traiter.split(" - ")[0]) & 
                (st.session_state.db_demandes_collaborateurs["Désignation"] == demande_a_traiter.split(" - ")[1])
            ].index
            
            if action_decision == "Supprimer / Archiver la ligne":
                st.session_state.db_demandes_collaborateurs = st.session_state.db_demandes_collaborateurs.drop(idx_demande).reset_index(drop=True)
                st.success("Ligne mise à jour.")
            elif action_decision != "Laisser en attente":
                st.session_state.db_demandes_collaborateurs.loc[idx_demande, "Statut"] = action_decision
                st.success(f"Statut changé en : {action_decision}")
            st.rerun()
    else:
        st.success("✅ Aucun bon de commande en attente dans le magasin.")

    st.markdown("---")
    # Section Étalonnages
    st.subheader("🚨 Alertes Étalonnages (< 90 jours)")
    aujourdhui = datetime.now().date()
    lignes_alertes = []
    for idx, row in st.session_state.db_materiel.iterrows():
        jours_restants = (row["Prochain Contrôle"] - aujourdhui).days
        if jours_restants <= 90:
            lignes_alertes.append({"Urgence": "🔴 RETARD" if jours_restants < 0 else "🟡 Échéance proche", "ID": row["ID"], "Matériel": row["Nom"], "Détenteur": row["Détenteur"], "Date Limite": row["Prochain Contrôle"]})
    if lignes_alertes:
        st.dataframe(pd.DataFrame(lignes_alertes), use_container_width=True, hide_index=True)


# ==========================================
# ONGLET 1 : CATALOGUE INTERACTIF & PANIER E-COMMERCE
# ==========================================
with tab1:
    st.header("🛒 Catalogue Officiel SOC Industrie")
    st.write("Sélectionnez vos EPI et consommables de marque, ajustez vos tailles et validez votre panier global.")

    # Design en 2 colonnes : À gauche le catalogue, à droite le Panier en temps réel
    col_cat, col_panier = st.columns([3, 2])

    with col_cat:
        st.subheader("📦 Articles disponibles au stock")
        
        # Filtre par catégorie rapide
        filtre_type = st.radio("Filtrer par type :", ["Tous", "🦺 EPI", "🪵 Consommable"], horizontal=True)

        for prod in CATALOGUE:
            if filtre_type != "Tous" and prod["type"] != filtre_type:
                continue
                
            # Container visuel pour chaque article (façon fiche produit)
            with st.container(border=True):
                c_img, c_txt, c_form = st.columns([1, 2, 1.5])
                
                with c_img:
                    st.image(prod["photo"], width=110)
                
                with c_txt:
                    st.markdown(f"### {prod['nom']}")
                    st.markdown(f"**Marque :** {prod['marque']} | **Réf :** `{prod['ref']}`")
                    st.caption(prod["desc"])
                
                with c_form:
                    # Sélecteurs uniques en utilisant l'ID produit pour éviter les conflits Streamlit
                    taille_choisie = st.selectbox("Taille / Conditionnement", prod["tailles"], key=f"taille_{prod['id']}")
                    qte_choisie = st.number_input("Quantité", min_value=1, max_value=50, value=1, key=f"qte_{prod['id']}")
                    
                    if st.button("➕ Ajouter au panier", key=f"btn_{prod['id']}", use_container_width=True):
                        # Enregistrement dans le panier temporaire
                        item_panier = {
                            "type": prod["type"],
                            "designation": f"{prod['nom']} ({prod['marque']} - Réf: {prod['ref']})",
                            "taille": taille_choisie,
                            "qte": qte_choisie
                        }
                        st.session_state.panier.append(item_panier)
                        st.toast(f"Ajouté : {prod['nom']} (x{qte_choisie})", icon="🛒")
                        st.rerun()

    # SECTION DE DROITE : LE PANIER RECAPITULATIF ET ENVOI
    with col_panier:
        st.subheader("🛒 Mon Panier en cours")
        
        if len(st.session_state.panier) == 0:
            st.info("Votre panier est vide. Cliquez sur 'Ajouter au panier' à gauche pour le remplir.")
        else:
            # Transformation du panier en tableau lisible
            df_panier = pd.DataFrame(st.session_state.panier)
            st.dataframe(df_panier[["type", "designation", "taille", "qte"]], use_container_width=True, hide_index=True)
            
            if st.button("🗑️ Vider entièrement le panier", use_container_width=True):
                st.session_state.panier = []
                st.rerun()
                
            st.markdown("---")
            st.subheader("🔏 Validation Obligatoire")
            
            # Formulaire final de commande avec validation des données critiques
            with st.form("form_validation_panier"):
                nom_collaborateur = st.text_input("Votre Nom et Prénom")
                code_imputation_general = st.text_input("Code Imputation Obligatoire (ex: CH-MILLET-2025)")
                commentaires = st.text_area("Notes ou degré d'urgence (optionnel)")
                
                submit_commande = st.form_submit_button("🚀 Envoyer le Bon de Commande à Olivier", use_container_width=True)
                
                if submit_commande:
                    if not nom_collaborateur.strip() or not code_imputation_general.strip():
                        st.error("🛑 Erreur : Vous devez renseigner votre Nom ET le Code Imputation pour valider la commande.")
                    else:
                        # On injecte chaque élément du panier comme une ligne de demande pour Olivier
                        nouvelles_lignes = []
                        for article in st.session_state.panier:
                            ligne = {
                                "Date": datetime.now().strftime("%d/%m/%Y"),
                                "Collaborateur": nom_collaborateur.strip(),
                                "Type": article["type"],
                                "Désignation": article["designation"],
                                "Code Imputation": code_imputation_general.upper().strip(),
                                "Détails / Dates": f"Taille: {article['taille']} | Qté: {article['qte']} | {commentaires}",
                                "Statut": "En attente"
                            }
                            nouvelles_lignes.append(ligne)
                        
                        # Ajout à la BDD globale d'Olivier
                        st.session_state.db_demandes_collaborateurs = pd.concat([
                            st.session_state.db_demandes_collaborateurs, 
                            pd.DataFrame(nouvelles_lignes)
                        ], ignore_index=True)
                        
                        # Remise à zéro du panier après commande réussie
                        st.session_state.panier = []
                        st.success("🎉 Parfait ! Votre bon de commande a été validé et envoyé sur le tableau de bord d'Olivier.")
                        st.rerun()


# ==========================================
# LES AUTRES ONGLETS DE L'APPLI (RESTE INCHANGÉ)
# ==========================================
with tab2:
    st.header("🛠️ Registre Général du Parc Matériel")
    st.dataframe(st.session_state.db_materiel, use_container_width=True, hide_index=True)

with tab3:
    st.header("📅 Sorties Opérationnelles Directes")
    st.write("Utilisez cet onglet uniquement pour les transferts directs d'outillage lourd de technicien à technicien.")

with tab4:
    st.header("📍 Cartographie des Chantiers")
    map_data = pd.DataFrame(np.random.randn(3, 2) / [50, 50] + [47.33, -0.40], columns=['lat', 'lon'])
    st.map(map_data, zoom=10)

# Barre latérale
st.sidebar.image("https://img.icons8.com/clouds/100/000000/crane.png",
