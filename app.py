import streamlit as st
import pandas as pd
import sqlalchemy
import base64
import numpy as np
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="SOC Industrie", layout="wide")

# --- CONNEXION ---
@st.cache_resource
def init_connection():
    return sqlalchemy.create_engine(st.secrets["DB_URL"])
engine = init_connection()

# --- CHARGEMENT ---
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
    {"id": "EPI-01", "type": "🦺 EPI", "nom": "Gants soudure", "marque": "Singer", "ref": "TIG", "tailles": ["M", "L"], "photo": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=150", "desc": "Cuir de chèvre."},
    {"id": "CON-01", "type": "🪵 Consommable", "nom": "Électrodes", "marque": "Gys", "ref": "E308L", "tailles": ["50", "10"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150", "desc": "Soudure Inox."}
]
CATALOGUE_OUTILLAGE = [
    {"id": "OUT-01", "type": "🛠️ Outillage", "nom": "Perceuse Bosch", "marque": "Bosch", "ref": "GBH", "tailles": ["Nue"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150", "desc": "Puissante."}
]
CATALOGUE_TOTAL = CATALOGUE + CATALOGUE_OUTILLAGE

# --- INTERFACE ---
tab0, tab1, tab2, tab3, tab4 = st.tabs(["👑 Tableau de Bord", "🛒 Catalogue", "🛠️ Catalogue Visuel", "📦 Sorties", "🗺️ Carte"])

with tab0:
    st.header("👑 Tableau de Bord")
    # ... (votre code tab0 actuel fonctionne)

with tab1:
    st.header("🛒 Catalogue Magasin & Outillage")
    col_cat, col_panier = st.columns([3, 2])
    with col_cat:
        filtre_type = st.radio("Filtrer :", ["Tous", "🦺 EPI", "🪵 Consommable", "🛠️ Outillage"], horizontal=True)
        for prod in CATALOGUE_TOTAL:
            if filtre_type != "Tous" and prod["type"] != filtre_type: continue
            with st.container(border=True):
                c_img, c_txt, c_form = st.columns([1, 2, 1.5])
                c_img.image(prod.get("photo", ""), width=100)
                with c_txt:
                    st.markdown(f"### {prod['nom']}")
                    st.caption(f"{prod['marque']} - {prod['ref']}")
                with c_form:
                    t = st.selectbox("Taille", prod["tailles"], key=f"t_{prod['id']}")
                    if st.button("➕ Ajouter", key=f"b_{prod['id']}"):
                        st.session_state.panier.append({"nom": prod['nom'], "taille": t})
                        st.rerun()

    with col_panier:
        st.subheader("🛒 Mon Panier")
        if st.session_state.panier:
            st.dataframe(pd.DataFrame(st.session_state.panier))
            with st.form("form_panier"):
                nom = st.text_input("Nom")
                if st.form_submit_button("Envoyer"):
                    st.success("Envoyé !")

with tab2:
    st.header("🛠️ Catalogue Visuel")
    # ... (le code que vous aviez est correct, vérifiez juste l'alignement)
