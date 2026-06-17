import streamlit as st
import sqlalchemy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import urllib.parse

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
    with engine.connect() as conn:
        pass
except Exception as e:
    st.error(f"Erreur de connexion à la base de données : {e}")
    st.stop()

# 3. RECUPERATION DES DONNEES REELLES (SUPABASE)
def charger_materiel():
    query = "SELECT id AS \"ID\", nom AS \"Nom\", categorie AS \"Catégorie\", statut AS \"Statut\", detenteur AS \"Détenteur\", date_controle AS \"Date Contrôle\", intervalle_mois AS \"Intervalle (mois)\", prochain_controle AS \"Prochain Contrôle\" FROM materiel;"
    return pd.read_sql(query, engine)

def charger_demandes():
    query = "SELECT date_demande AS \"Date\", collaborateur AS \"Collaborateur\", type_demande AS \"Type\", designation AS \"Désignation\", code_imputation AS \"Code Imputation\", details AS \"Détails / Dates\", statut AS \"Statut\" FROM demandes_collaborateurs;"
    return pd.read_sql(query, engine)

df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

# INITIALISATION DU PANIER COLLABORATEUR
if 'panier' not in st.session_state:
    st.session_state.panier = []

# DICTIONNAIRE DE PHOTOS PAR DÉFAUT POUR LE MATÉRIEL DU PARC
PHOTOS_MATERIEL = {
    "Soudage": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=300&q=80",
    "Outillage Électroportatif": "https://images.unsplash.com/photo-1534224039826-c7a0dea0e66a?w=300&q=80",
    "Mesure": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=300&q=80",
    "Manutention": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=300&q=80"
}

# CATALOGUE MAGASIN (EPI & CONSOMMABLES)
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

tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 ESPACE OLIVIER : Centralisation & Logistique",
    "🛒 CATALOGUE MAGASIN (EPI / Consommables)",
    "🛠️ CATALOGUE VISUEL & REGISTRE MATÉRIEL", 
    "📅 Sorties & Mouvements Terrain", 
    "📍 Carte des Chantiers"
])

# ==========================================
# ONGLET 0 : ESPACE OLIVIER
# ==========================================
with tab0:
    st.header("👑 Tableau de Bord Logistique d'Olivier")
    
    st.subheader("📥 Demandes de consommables et réservations reçues")
    if not df_demandes_reel.empty:
        st.dataframe(df_demandes_reel, use_container_width=True, hide_index=True)
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            demande_a_traiter = st.selectbox("Sélectionner une ligne à archiver / traiter :", 
                                             df_demandes_reel["Collaborateur"] + " - " + df_demandes_reel["Désignation"], key="sel_olivier")
        with col_v2:
            action_decision = st.radio("Action :", ["Laisser en attente", "Valider / Matériel Prêt", "Supprimer / Archiver la ligne"], horizontal=True, key="rad_olivier")
            
        if st.button("Confirmer l'action sur la demande", key="btn_olivier"):
            collab_sel = demande_a_traiter.split(" - ")[0]
            desig_sel = demande_a_traiter.split(" - ")[1]
            with engine.begin() as conn_tx:
                if action_decision == "Supprimer / Archiver la ligne":
                    conn_tx.execute(sqlalchemy.text("DELETE FROM demandes_collaborateurs WHERE collaborateur = :c AND designation = :d;"), {"c": collab_sel, "d": desig_sel})
                elif action_decision != "Laisser en attente":
                    conn_tx.execute(sqlalchemy.text("UPDATE demandes_collaborateurs SET statut = :s WHERE collaborateur = :c AND designation = :d;"), {"s": action_decision, "c": collab_sel, "d": desig_sel})
            st.rerun()
    else:
        st.success("✅ Aucune commande ou réservation en attente.")

    st.markdown("---")
    st.subheader("🚨 Alertes Étalonnages (< 90 jours)")
    aujourdhui = datetime.now().date()
    lignes_alertes = []
    for idx, row in df_materiel_reel.iterrows():
        date_prox = row["Prochain Contrôle"]
        if isinstance(date_prox, str): date_prox = datetime.strptime(date_prox, "%Y-%m-%d").date()
        elif isinstance(date_prox, datetime): date_prox = date_prox.date()
        jours_restants = (date_prox - aujourdhui).days
        if jours_restants <= 90:
            lignes_alertes.append({
                "Urgence": "🔴 RETARD" if jours_restants < 0 else "🟡 Échéance proche",
                "ID": row["ID"], "Matériel": row["Nom"], "Détenteur": row["Détenteur"], "Prochain Contrôle": date_prox
            })
    if lignes_alertes: st.dataframe(pd.DataFrame(lignes_alertes), use_container_width=True, hide_index=True)
    else: st.success("✅ Aucun étalonnage critique à prévoir.")

# ==========================================
# ONGLET 1 : CATALOGUE MAGASIN (EPI / CONSOMMABLES)
# ==========================================
with tab1:
    st.header("🛒 Catalogue Magasin SOC Industrie")
    col_cat, col_panier = st.columns([3, 2])

    with col_cat:
        filtre_type = st.radio("Filtrer par type :", ["Tous", "🦺 EPI", "🪵 Consommable"], horizontal=True)
        for prod in CATALOGUE:
            if filtre_type != "Tous" and prod["type"] != filtre_type: continue
            with st.container(border=True):
                c_img, c_txt, c_form = st.columns([1, 2, 1.5])
                with c_img: st.image(prod["photo"], width=100)
                with c_txt:
                    st.markdown(f"### {prod['nom']}")
                    st.caption(f"**Marque :** {prod['marque']} | **Ref :** {prod['ref']}\n\n{prod['desc']}")
                with c_form:
                    t_choisie = st.selectbox("Option / Taille", prod["tailles"], key=f"t_{prod['id']}")
                    q_choisie = st.number_input("Quantité", min_value=1, value=1, key=f"q_{prod['id']}")
                    if st.button("➕ Ajouter", key=f"b_{prod['id']}", use_container_width=True):
                        st.session_state.panier.append({"type": prod["type"], "designation": f"{prod['nom']} ({prod['marque']})", "taille": t_choisie, "qte": q_choisie})
                        st.rerun()

    with col_panier:
        st.subheader("🛒 Mon Panier")
        if not st.session_state.panier: st.info("Panier vide.")
        else:
            st.dataframe(pd.DataFrame(st.session_state.panier), use_container_width=True, hide_index=True)
            if st.button("🗑️ Vider", use_container_width=True):
                st.session_state.panier = []
                st.rerun()
            
            st.markdown("---")
            with st.form("form_panier"):
                nom_c = st.text_input("Votre Nom")
                code_i = st.text_input("Code Imputation Obligatoire")
                if st.form_submit_button("🚀 Envoyer la commande", use_container_width=True):
                    if nom_c.strip() and code_i.strip():
                        with engine.begin() as conn_tx:
                            for art in st.session_state.panier:
                                details = f"Option: {art['taille']} | Qté: {art['qte']}"
                                conn_tx.execute(sqlalchemy.text("INSERT INTO demandes_collaborateurs (date_demande, collaborateur, type_demande, designation, code_imputation, details, statut) VALUES (:dt, :col, :ty, :des, :cod, :det, 'En attente');"),
                                                {"dt": datetime.now().strftime("%d/%m/%Y"), "col": nom_c.strip(), "ty": art["type"], "des": art["designation"], "cod": code_i.upper().strip(), "det": details})
                        st.session_state.panier = []
                        st.success("Commande transmise à Olivier !")
                        st.rerun()
                    else: st.error("Champs obligatoires manquants.")

# ==========================================
# ONGLET 2 : CATALOGUE VISUEL DU MATÉRIEL & QR CODES (CORRIGÉ)
# ==========================================
with tab2:
    st.header("🛠️ Catalogue Commun du Parc Matériel")
    st.write("Recherchez un équipement, consultez sa localisation en temps réel ou scannez son QR code pour obtenir sa fiche.")

    # Barre de recherche globale pour le matériel lourd
    recherche = st.text_input("🔍 Rechercher un matériel (ex: Meuleuse, TIG, MAT-001...)", "").strip().lower()

    # Moteur d'affichage sous forme de fiches visuelles (Grid)
    st.subheader("📦 Fiches Équipements & Disponibilités")
    
    # Filtrer le dataframe selon la recherche utilisateur
    df_filtre = df_materiel_reel.copy()
    if recherche:
        df_filtre = df_filtre[
            df_filtre["Nom"].str.lower().str.contains(recherche) | 
            df_filtre["ID"].str.lower().str.contains(recherche) |
            df_filtre["Catégorie"].str.lower().str.contains(recherche)
        ]

    if df_filtre.empty:
        st.info("Aucun matériel ne correspond à votre recherche.")
    else:
        # Affichage en grille de 3 colonnes pour l'aspect visuel
        cols_grid = st.columns(3)
        for idx, row in df_filtre.iterrows():
            col_case = cols_grid[idx % 3]
            
            with col_case:
                with st.container(border=True):
                    # Récupération de l'image correspondante à la catégorie
                    img_url = PHOTOS_MATERIEL.get(row["Catégorie"], "https://images.unsplash.com/photo-1534224039826-c7a0dea0e66a?w=300&q=80")
                    st.image(img_url, use_container_width=True)
                    
                    # Titre et ID
                    st.markdown(f"### {row['Nom']}")
                    st.markdown(f"**Code Unique :** `{row['ID']}`")
                    
                    # Badge de statut de localisation couleur
                    statut = row["Statut"]
                    if statut == "Disponible":
                        st.success(f"📍 {statut} (Stock Atelier)")
                    elif statut == "En Chantier":
                        st.warning(f"🏗️ {statut} chez **{row['Détenteur']}**")
                    else:
                        st.info(f"🔄 {statut} — {row['Détenteur']}")
                        
                    # Infos de contrôle réglementaire
                    st.caption(f"📅 Prochain contrôle obligatoire : {row['Prochain Contrôle']}")
                    
                    # SYSTEME QR CODE : Génération automatique d'un texte d'information
                    texte_qr = f"SOC Industrie\nID: {row['ID']}\nNom: {row['Nom']}\nStatut: {statut}\nResponsable: {row['Détenteur']}\nCtrl: {row['Prochain Contrôle']}"
                    texte_encode = urllib.parse.quote(texte_qr)
                    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={texte_encode}"
                    
                    # Expanders interactifs
                    with st.expander("📱 Afficher le QR Code de l'appareil"):
                        st.image(qr_api_url, caption="À coller sur l'appareil pour scan terrain", width=130)
                        st.caption("Flashez ce code avec un téléphone pour extraire instantanément le statut complet de la machine.")

                    # LIGNE 243 CORRIGÉE : Changement de 'St.expander' par 'st.expander'
                    with st.expander("📅 Faire une demande de réservation"):
                        with st.form(key=f"reserve_{row['ID']}"):
                            nom_demandeur = st.text_input("Votre Prénom/Nom", key=f"u_{row['ID']}")
                            code_imput = st.text_input("Code Imputation Chantier cible", key=f"i_{row['ID']}")
                            date_besoin = st.date_input("Date prévue d'utilisation", aujourdhui, key=f"d_{row['ID']}")
                            
                            if st.form_submit_button("Valider la demande de réservation"):
                                if nom_demandeur.strip() and code_imput.strip():
                                    details_res = f"Réservation Matériel Lourd | Date d'utilisation prévue : {date_besoin.strftime('%d/%m/%Y')}"
                                    with engine.begin() as conn_tx:
                                        conn_tx.execute(
                                            sqlalchemy.text("""
                                                INSERT INTO demandes_collaborateurs (date_demande, collaborateur, type_demande, designation, code_imputation, details, statut)
                                                VALUES (:dt, :col, '⚙️ Réservation', :des, :cod, :det, 'En attente');
                                            """),
                                            {
                                                "dt": datetime.now().strftime("%d/%m/%Y"),
                                                "col": nom_demandeur.strip(),
                                                "des": f"Réservation {row['Nom']} [{row['ID']}]",
                                                "cod": code_imput.upper().strip(),
                                                "det": details_res
                                            }
                                        )
                                    st.success("Demande de réservation envoyée à Olivier !")
                                    st.toast("Demande enregistrée !", icon="⚙️")
                                    st.rerun()
                                else:
                                    st.error("Le nom et le code imputation sont obligatoires.")

    st.markdown("---")
    st.subheader("⚙️ Administration : Ajouter une nouvelle référence au parc")
    with st.form("form_ajout_reel"):
        col_a, col_b = st.columns(2)
        with col_a:
            new_id = st.text_input("Identifiant Unique (ex: MAT-004)")
            new_nom = st.text_input("Nom du matériel")
            new_cat = st.selectbox("Catégorie", ["Outillage Électroportatif", "Manutention", "Soudage", "Mesure"])
        with col_b:
            new_date = st.date_input("Date du dernier contrôle", aujourdhui)
            new_intervalle = st.number_input("Intervalle de contrôle (en mois)", min_value=1, value=12)
        
        if st.form_submit_button("Ajouter définitivement au parc"):
            if new_id.strip() and new_nom.strip():
                prochain_calcul = new_date + timedelta(days=int(new_intervalle) * 30)
                with engine.begin() as conn_tx:
                    conn_tx.execute(
                        sqlalchemy.text("""
                            INSERT INTO materiel (id, nom, categorie, statut, detenteur, date_controle, intervalle_mois, prochain_controle)
                            VALUES (:id, :nom, :cat, 'Disponible', 'Atelier / Agence', :dt, :inv, :prox);
                        """),
                        {"id": new_id.strip(), "nom": new_nom.strip(), "cat": new_cat, "dt": new_date, "inv": int(new_intervalle), "prox": prochain_calcul}
                    )
                st.success("Matériel ajouté en base de données.")
                st.rerun()
            else: st.error("Champs manquants.")

# ==========================================
# ONGLETS CHANTIERS & DIRECT
# ==========================================
with tab3:
    st.header("📅 Sorties Opérationnelles Directes")
    st.info("Espace de transit de matériel lourd d'artisan à artisan.")

with tab4:
    st.header("📍 Cartographie des Chantiers")
    map_data = pd.DataFrame(np.random.randn(3, 2) / [50, 50] + [47.33, -0.40], columns=['lat', 'lon'])
    st.map(map_data, zoom=10)

# Barre latérale
st.sidebar.image("https://img.icons8.com/clouds/100/000000/crane.png", width=60)
st.sidebar.title("Navigation")
st.sidebar.info("Application Interne v2.3 — SOC Industrie. Catalogue Visuel & QR Codes Actifs.")
