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
    with engine.connect() as conn:
        pass
    st.success("Connexion établie avec succès à la base de données Supabase !")
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

# DEFINITION DU CATALOGUE ENRICHI (EPI, CONSOMMABLES & OUTILLAGE)
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
    },
    {
        "id": "OUT-01", "type": "🛠️ Outillage", "nom": "Meuleuse d'angle filaire 125mm", "marque": "Bosch Professional",
        "ref": "GWS 7-125", "tailles": ["Standard (Mallette)", "Version nue"], "photo": "https://images.unsplash.com/photo-1534224039826-c7a0dea0e66a?w=150&q=80",
        "desc": "Meuleuse compacte de 720W, protection contre le redémarrage intempestif."
    },
    {
        "id": "OUT-02", "type": "🛠️ Outillage", "nom": "Perceuse Visseuse à percussion 18V", "marque": "Makita",
        "ref": "DHP482Z", "tailles": ["Avec 2 batteries 5.0Ah", "Outil Nu"], "photo": "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=150&q=80",
        "desc": "Perceuse robuste et rapide pour les perçages et vissages intensifs sur chantier."
    }
]

# Répartition des modules par Onglets
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 ESPACE OLIVIER : Centralisation & Logistique",
    "🛒 CATALOGUE & MAGASIN (EPI / Consommables / Outillage)",
    "🛠️ Registre & Gestion du Matériel", 
    "📅 Sorties & Mouvements Terrain", 
    "📍 Carte des Chantiers"
])

# ==========================================
# ONGLET 0 : ESPACE OLIVIER
# ==========================================
with tab0:
    st.header("👑 Tableau de Bord Logistique d'Olivier")
    st.write("Retrouvez ici les obligations réglementaires ainsi que les bons de commande complets générés par le catalogue.")
    
    st.subheader("📥 Bons de commande et demandes reçus")
    if not df_demandes_reel.empty:
        st.dataframe(df_demandes_reel, use_container_width=True, hide_index=True)
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            demande_a_traiter = st.selectbox("Sélectionner une ligne à archiver / traiter :", 
                                             df_demandes_reel["Collaborateur"] + " - " + df_demandes_reel["Désignation"])
        with col_v2:
            action_decision = st.radio("Action :", ["Laisser en attente", "Valider / Matériel Prêt", "Supprimer / Archiver la ligne"], horizontal=True)
            
        if st.button("Confirmer l'action sur la demande"):
            collab_sel = demande_a_traiter.split(" - ")[0]
            desig_sel = demande_a_traiter.split(" - ")[1]
            
            with engine.begin() as conn_tx:
                if action_decision == "Supprimer / Archiver la ligne":
                    conn_tx.execute(
                        sqlalchemy.text("DELETE FROM demandes_collaborateurs WHERE collaborateur = :c AND designation = :d;"),
                        {"c": collab_sel, "d": desig_sel}
                    )
                    st.success("Ligne archivée avec succès.")
                elif action_decision != "Laisser en attente":
                    conn_tx.execute(
                        sqlalchemy.text("UPDATE demandes_collaborateurs SET statut = :s WHERE collaborateur = :c AND designation = :d;"),
                        {"s": action_decision, "c": collab_sel, "d": desig_sel}
                    )
                    st.success(f"Statut changé en : {action_decision}")
            st.rerun()
    else:
        st.success("✅ Aucun bon de commande en attente dans le magasin.")

    st.markdown("---")
    
    st.subheader("🚨 Alertes Étalonnages et Contrôles Périodiques (< 90 jours)")
    aujourdhui = datetime.now().date()
    lignes_alertes = []
    
    for idx, row in df_materiel_reel.iterrows():
        date_prox = row["Prochain Contrôle"]
        if isinstance(date_prox, str):
            date_prox = datetime.strptime(date_prox, "%Y-%m-%d").date()
        elif isinstance(date_prox, datetime):
            date_prox = date_prox.date()
            
        jours_restants = (date_prox - aujourdhui).days
        if jours_restants <= 90:
            lignes_alertes.append({
                "Urgence": "🔴 RETARD" if jours_restants < 0 else "🟡 Échéance proche",
                "ID": row["ID"], "Matériel": row["Nom"], "Détenteur": row["Détenteur"],
                "Date Limite": date_prox, "Jours Restants": jours_restants
            })
            
    if lignes_alertes:
        st.dataframe(pd.DataFrame(lignes_alertes), use_container_width=True, hide_index=True)
    else:
        st.success("✅ Aucun étalonnage à prévoir d'ici 3 mois.")


# ==========================================
# ONGLET 1 : CATALOGUE INTERACTIF & PANIER MULTI-CATEGORIES
# ==========================================
with tab1:
    st.header("🛒 Catalogue Officiel SOC Industrie")
    st.write("Sélectionnez vos EPI, consommables et outillages, ajustez vos choix et validez le panier de chantier.")

    col_cat, col_panier = st.columns([3, 2])

    with col_cat:
        st.subheader("📦 Articles disponibles au stock")
        # Extension du filtre pour inclure l'outillage
        filtre_type = st.radio("Filtrer par type :", ["Tous", "🦺 EPI", "🪵 Consommable", "🛠️ Outillage"], horizontal=True)

        for prod in CATALOGUE:
            if filtre_type != "Tous" and prod["type"] != filtre_type:
                continue
                
            with st.container(border=True):
                c_img, c_txt, c_form = st.columns([1, 2, 1.5])
                with c_img:
                    st.image(prod["photo"], width=110)
                with c_txt:
                    st.markdown(f"### {prod['nom']}")
                    st.markdown(f"**Marque :** {prod['marque']} | **Réf :** `{prod['ref']}`")
                    st.caption(prod["desc"])
                with c_form:
                    taille_choisie = st.selectbox("Option / Configuration", prod["tailles"], key=f"taille_{prod['id']}")
                    qte_choisie = st.number_input("Quantité", min_value=1, max_value=50, value=1, key=f"qte_{prod['id']}")
                    
                    if st.button("➕ Ajouter au panier", key=f"btn_{prod['id']}", use_container_width=True):
                        item_panier = {
                            "type": prod["type"],
                            "designation": f"{prod['nom']} ({prod['marque']})",
                            "taille": taille_choisie,
                            "qte": qte_choisie
                        }
                        st.session_state.panier.append(item_panier)
                        st.toast(f"Ajouté : {prod['nom']} (x{qte_choisie})", icon="🛒")
                        st.rerun()

    with col_panier:
        st.subheader("🛒 Mon Panier en cours")
        if len(st.session_state.panier) == 0:
            st.info("Votre panier est vide. Cliquez sur 'Ajouter' à gauche pour le remplir.")
        else:
            df_p = pd.DataFrame(st.session_state.panier)
            st.dataframe(df_p[["type", "designation", "taille", "qte"]], use_container_width=True, hide_index=True)
            
            if st.button("🗑️ Vider entièrement le panier", use_container_width=True):
                st.session_state.panier = []
                st.rerun()
                
            st.markdown("---")
            st.subheader("🔏 Validation Obligatoire")
            
            with st.form("form_validation_panier"):
                nom_collaborateur = st.text_input("Votre Nom et Prénom")
                code_imputation_general = st.text_input("Code Imputation Obligatoire (ex: CH-MILLET-2025)")
                commentaires = st.text_area("Notes particulières (optionnel)")
                
                submit_commande = st.form_submit_button("🚀 Envoyer le Bon de Commande à Olivier", use_container_width=True)
                
                if submit_commande:
                    if not nom_collaborateur.strip() or not code_imputation_general.strip():
                        st.error("🛑 Erreur : Vous devez renseigner votre Nom ET le Code Imputation pour valider.")
                    else:
                        with engine.begin() as conn_tx:
                            for article in st.session_state.panier:
                                details_str = f"Option: {article['taille']} | Qté: {article['qte']} | {commentaires}"
                                conn_tx.execute(
                                    sqlalchemy.text("""
                                        INSERT INTO demandes_collaborateurs (date_demande, collaborateur, type_demande, designation, code_imputation, details, statut)
                                        VALUES (:date, :collab, :type, :desig, :code, :det, 'En attente');
                                    """),
                                    {
                                        "date": datetime.now().strftime("%d/%m/%Y"),
                                        "collab": nom_collaborateur.strip(),
                                        "type": article["type"],
                                        "desig": article["designation"],
                                        "code": code_imputation_general.upper().strip(),
                                        "det": details_str
                                    }
                                )
                        st.session_state.panier = []
                        st.success("🎉 Bon de commande enregistré dans la base Supabase d'Olivier !")
                        st.rerun()


# ==========================================
# ONGLET 2 : REGISTRE GENERAL MATÉRIEL
# ==========================================
with tab2:
    st.header("🛠️ Registre Général du Parc Matériel")
    st.dataframe(df_materiel_reel, use_container_width=True, hide_index=True)
    
    st.subheader("⚙️ Enregistrer un nouveau matériel en base")
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
            if not new_id.strip() or not new_nom.strip():
                st.error("Veuillez remplir l'ID et le Nom.")
            else:
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


# ==========================================
# ONGLETS COMPLÉMENTAIRES
# ==========================================
with tab3:
    st.header("📅 Sorties Opérationnelles Directes")
    st.info("Espace de transfert de matériel lourd d'artisan à artisan.")

with tab4:
    st.header("📍 Cartographie des Chantiers")
    map_data = pd.DataFrame(np.random.randn(3, 2) / [50, 50] + [47.33, -0.40], columns=['lat', 'lon'])
    st.map(map_data, zoom=10)

# Barre latérale
st.sidebar.image("https://img.icons8.com/clouds/100/000000/crane.png", width=60)
st.sidebar.title("Navigation")
st.sidebar.info("Application Interne v2.1 — SOC Industrie. Catalogue complet actif.")
