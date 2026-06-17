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

# 2. CONNEXION BDD
@st.cache_resource
def init_connection():
    db_url = "postgresql://postgres.spxrxmzeaybndgpmoslo:VotreMotDePasse@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
    return sqlalchemy.create_engine(db_url)

engine = init_connection()

# 3. FONCTIONS DONNÉES
def charger_materiel():
    query = 'SELECT id AS "ID", nom AS "Nom", categorie AS "Catégorie", statut AS "Statut", detenteur AS "Détenteur", date_controle AS "Date Contrôle", intervalle_mois AS "Intervalle (mois)", prochain_controle AS "Prochain Contrôle", photo_base64 AS "Photo", marque AS "Marque", reference AS "Référence", num_serie AS "N° de Série" FROM materiel;'
    return pd.read_sql(query, engine)

def charger_demandes():
    query = 'SELECT date_demande AS "Date", collaborateur AS "Collaborateur", type_demande AS "Type", designation AS "Désignation", code_imputation AS "Code Imputation", details AS "Détails / Dates", statut AS "Statut" FROM demandes_collaborateurs;'
    return pd.read_sql(query, engine)

df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

if 'panier' not in st.session_state: st.session_state.panier = []

# 4. CATALOGUE
CATALOGUE = [
    {"id": "EPI-01", "type": "🦺 EPI", "nom": "Gants de soudure Haute Protection", "marque": "Singer Safety", "ref": "TIG-500", "tailles": ["M", "L", "XL"], "photo": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=150", "desc": "Cuir de chèvre."},
    {"id": "CON-01", "type": "🪵 Consommable", "nom": "Électrodes Inox Ø2.5", "marque": "Gys", "ref": "E308L", "tailles": ["50", "10"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150", "desc": "Soudure Inox."}
]

# 5. INTERFACE
tab0, tab1, tab2, tab3, tab4 = st.tabs(["👑 Admin", "🛒 Catalogue", "🛠️ Matériel", "📅 Sorties", "📍 Carte"])

with tab0:
    st.header("👑 Tableau de Bord Logistique")
    st.dataframe(df_demandes_reel, use_container_width=True)

with tab1:
    st.header("🛒 Catalogue Magasin")
    col_cat, col_panier = st.columns([3, 2])
    
    with col_cat:
        for prod in CATALOGUE:
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                c1.image(prod["photo"], width=100)
                c2.markdown(f"### {prod['nom']}")
                if st.button(f"Ajouter {prod['id']}", key=f"add_{prod['id']}"):
                    st.session_state.panier.append(prod)
                    st.rerun()
                    
    with col_panier:
        st.subheader("🛒 Mon Panier")
        if st.session_state.panier:
            st.write(pd.DataFrame(st.session_state.panier))
            if st.button("Vider"):
                st.session_state.panier = []
                st.rerun()

with tab2:
    st.header("🛠️ Catalogue Matériel")
    # Logique de gestion matériel ici
    st.write("Gestion des fiches équipements...")

# Ajout des autres onglets (tab3, tab4) selon besoin...
