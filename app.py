import streamlit as st
import sqlalchemy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import urllib.parse
import base64

# --- 1. DÉFINITION DES DONNÉES (Placé en haut pour éviter les NameError) ---
CATALOGUE = [
    {"id": "EPI-01", "type": "EPI", "nom": "Gants de soudure Haute Protection", "marque": "Singer Safety", "ref": "TIG-500", "tailles": ["M (8)", "L (9)", "XL (10)", "XXL (11)"], "photo": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=150&q=80", "desc": "Cuir de chèvre supérieur, coutures Kevlar."},
    {"id": "EPI-02", "type": "EPI", "nom": "Chaussures de Sécurité S3 Basse", "marque": "Caterpillar", "ref": "CAT-LITE", "tailles": ["41", "42", "43", "44", "45"], "photo": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=150&q=80", "desc": "Coque composite sans métal."},
    {"id": "CON-01", "type": "Consommable", "nom": "Électrodes de Soudage Inox Ø2.5", "marque": "Gys", "ref": "E308L-16", "tailles": ["Étui 50p", "Blister 10p"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150&q=80", "desc": "Électrodes rutiles."},
    {"id": "CON-02", "type": "Consommable", "nom": "Disque à tronçonner Acier/Inox Ø125", "marque": "Norton Abrasifs", "ref": "NOR-125-1", "tailles": ["Lot 5", "Boîte 25"], "photo": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=150&q=80", "desc": "Épaisseur 1mm."}
]

CATALOGUE_OUTILLAGE = [
    {"id": "OUT-01", "type": "🛠️ Outillage", "nom": "Perceuse Visseuse Bosch Pro", "marque": "Bosch", "ref": "GSR-18V", "tailles": ["Machine nue", "Pack 2 batteries"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150&q=80", "desc": "Puissante et compacte."},
    {"id": "OUT-02", "type": "🛠️ Outillage", "nom": "Meuleuse d'angle 125mm", "marque": "Makita", "ref": "DGA504", "tailles": ["Standard", "Variateur"], "photo": "https://images.unsplash.com/photo-1534224039826-c7a0dea0e66a?w=150&q=80", "desc": "Performance professionnelle."}
]

CATALOGUE_COMPLET = CATALOGUE + CATALOGUE_OUTILLAGE

# --- 2. CONFIGURATION ET CONNEXION ---
st.set_page_config(page_title="SOC Industrie — Gestion Interne", page_icon="🏗️", layout="wide")
st.title("🏗️ SOC Industrie — Gestion Interne")

# IMPORTANT : Utilisez st.secrets pour la sécurité (à configurer dans l'interface Cloud)
try:
    engine = sqlalchemy.create_engine(st.secrets["DB_URL"])
except:
    st.error("Erreur de connexion : Vérifiez que DB_URL est bien renseigné dans les secrets Streamlit.")
    st.stop()

# --- 3. FONCTIONS DE CHARGEMENT ---
def charger_materiel():
    query = 'SELECT id AS "ID", nom AS "Nom", categorie AS "Catégorie", statut AS "Statut", detenteur AS "Détenteur", date_controle AS "Date Contrôle", intervalle_mois AS "Intervalle (mois)", prochain_controle AS "Prochain Contrôle", photo_base64 AS "Photo", marque AS "Marque", reference AS "Référence", num_serie AS "N° de Série" FROM materiel;'
    return pd.read_sql(query, engine)

def charger_demandes():
    query = 'SELECT date_demande AS "Date", collaborateur AS "Collaborateur", type_demande AS "Type", designation AS "Désignation", code_imputation AS "Code Imputation", details AS "Détails / Dates", statut AS "Statut" FROM demandes_collaborateurs;'
    return pd.read_sql(query, engine)

df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

if 'panier' not in st.session_state: st.session_state.panier = []

# --- 4. INTERFACE ---
tab0, tab1, tab2, tab3, tab4 = st.tabs(["👑 ESPACE OLIVIER", "🛒 CATALOGUE MAGASIN", "🛠️ PARC MATÉRIEL", "📅 SORTIES", "📍 CARTE"])

with tab0:
    st.header("👑 Tableau de Bord Logistique d'Olivier")
    # ... (Ajoutez votre logique de tableau et alertes ici) ...

with tab1:
    st.header("🛒 Catalogue Magasin SOC Industrie")
    filtre = st.radio("Filtrer :", ["Tous", "EPI", "Consommable", "🛠️ Outillage"], horizontal=True)
    for prod in CATALOGUE_COMPLET:
        if filtre != "Tous" and prod["type"] != filtre: continue
        with st.container(border=True):
            st.write(f"### {prod['nom']} - {prod['marque']}")
            # ... (Ajoutez le reste du formulaire ici) ...

with tab2:
    st.header("🛠️ Catalogue Commun du Parc Matériel")
    # ... (Ajoutez votre logique de catalogue et admin ici) ...

with tab3: st.header("📅 Sorties")
with tab4: st.header("📍 Carte")
