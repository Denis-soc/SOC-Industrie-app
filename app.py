import streamlit as st
import sqlalchemy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import urllib.parse
import base64

# --- CONFIGURATION ET CONNEXION ---
st.set_page_config(page_title="SOC Industrie — Gestion Interne", page_icon="🏗️", layout="wide")
st.title("🏗️ SOC Industrie — Gestion Interne")

@st.cache_resource
def init_connection():
    db_url = "postgresql://postgres.spxrxmzeaybndgpmoslo:LesGaulois2026@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
    return sqlalchemy.create_engine(db_url)

engine = init_connection()

# --- CHARGEMENT DONNÉES ---
def charger_materiel():
    query = 'SELECT id AS "ID", nom AS "Nom", categorie AS "Catégorie", statut AS "Statut", detenteur AS "Détenteur", date_controle AS "Date Contrôle", intervalle_mois AS "Intervalle (mois)", prochain_controle AS "Prochain Contrôle", photo_base64 AS "Photo", marque AS "Marque", reference AS "Référence", num_serie AS "N° de Série" FROM materiel;'
    return pd.read_sql(query, engine)

def charger_demandes():
    query = 'SELECT date_demande AS "Date", collaborateur AS "Collaborateur", type_demande AS "Type", designation AS "Désignation", code_imputation AS "Code Imputation", details AS "Détails / Dates", statut AS "Statut" FROM demandes_collaborateurs;'
    return pd.read_sql(query, engine)

df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

if 'panier' not in st.session_state: st.session_state.panier = []

# --- CATALOGUES ---
CATALOGUE = [
    {"id": "EPI-01", "type": "🦺 EPI", "nom": "Gants de soudure", "marque": "Singer Safety", "ref": "TIG-500", "tailles": ["M (8)", "L (9)", "XL (10)"], "photo": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=150&q=80", "desc": "Cuir de chèvre, coutures Kevlar."},
    {"id": "CON-01", "type": "🪵 Consommable", "nom": "Électrodes Inox Ø2.5", "marque": "Gys", "ref": "E308L-16", "tailles": ["Étui 50p", "Blister 10p"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150&q=80", "desc": "Électrodes rutiles."}
]

OUTILLAGE_PRO = [
    {"id": "OUT-01", "type": "🛠️ Outillage", "nom": "Meuleuse Bosch Pro", "marque": "Bosch", "ref": "GWS-18V", "tailles": ["Machine nue", "Pack batterie"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150&q=80", "desc": "Sans fil, haute performance."},
    {"id": "OUT-02", "type": "🛠️ Outillage", "nom": "Poste à souder TIG", "marque": "Gys", "ref": "TIG-220", "tailles": ["Unité seule", "Kit complet"], "photo": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=150&q=80", "desc": "TIG DC haute précision."}
]

CATALOGUE_TOTAL = CATALOGUE + OUTILLAGE_PRO

# --- INTERFACE ---
tab0, tab1, tab2, tab3, tab4 = st.tabs(["👑 Logistique", "🛒 Catalogue Magasin", "🛠️ Registre Matériel", "📅 Sorties", "📍 Carte"])

with tab1:
    st.header("🛒 Catalogue Magasin SOC Industrie")
    col_cat, col_panier = st.columns([3, 2])
    
    with col_cat:
        filtre_type = st.radio("Filtrer par type :", ["Tous", "🦺 EPI", "🪵 Consommable", "🛠️ Outillage"], horizontal=True)
        
        for prod in CATALOGUE_TOTAL:
            if filtre_type != "Tous" and prod["type"] != filtre_type: continue
            
            with st.container(border=True):
                c_img, c_txt, c_form = st.columns([1, 2, 1.5])
                with c_img: st.image(prod["photo"], width=100)
                with c_txt:
                    st.markdown(f"### {prod['nom']}")
                    st.caption(f"**Marque:** {prod['marque']} | **Ref:** {prod['ref']}\n\n{prod['desc']}")
                with c_form:
                    t_choisie = st.selectbox("Option", prod["tailles"], key=f"t_{prod['id']}")
                    q_choisie = st.number_input("Qté", min_value=1, value=1, key=f"q_{prod['id']}")
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
            with st.form("form_panier"):
                nom_c = st.text_input("Votre Nom")
                code_i = st.text_input("Code Imputation")
                if st.form_submit_button("🚀 Envoyer la commande"):
                    with engine.begin() as conn_tx:
                        for art in st.session_state.panier:
                            conn_tx.execute(sqlalchemy.text("INSERT INTO demandes_collaborateurs (date_demande, collaborateur, type_demande, designation, code_imputation, details, statut) VALUES (:dt, :col, :ty, :des, :cod, :det, 'En attente');"),
                                            {"dt": datetime.now().strftime("%d/%m/%Y"), "col": nom_c.strip(), "ty": art["type"], "des": art["designation"], "cod": code_i.upper().strip(), "det": f"Option: {art['taille']} | Qté: {art['qte']}"})
                    st.session_state.panier = []
                    st.success("Commande transmise !")
                    st.rerun()

# --- (Le reste de votre code tab0, tab2, tab3, tab4 reste identique) ---
