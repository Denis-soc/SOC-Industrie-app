import streamlit as st
import sqlalchemy
import pandas as pd
import numpy as np

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="SOC Industrie — Gestion Interne",
    page_icon="🏗️",
    layout="wide"
)

# TITRE PRINCIPAL
st.title("🏗️ SOC Industrie — Gestion Interne")

# 2. CONNEXION À LA BASE DE DONNÉES (POOLER)
# Remplacez 'VotreMotDePasse' par votre vrai mot de passe Supabase
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

# 3. LECTURE DES DONNÉES DE LA TABLE MATERIEL (SANS BLOCAGE)
st.header("📦 Données de l'application")
try:
    query = "SELECT * FROM materiel LIMIT 10;"
    df = pd.read_sql(query, conn)
    
    if df.empty:
        st.info("La table 'materiel' est connectée mais ne contient aucune donnée pour le moment.")
    else:
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.warning(f"Note : Impossible de lire la table 'materiel' (Vérifiez si elle contient des lignes ou si le RLS est désactivé) : {e}")


# 4. MODULE : GÉOLOCALISATION DU MATÉRIEL (CARTE)
st.header("📍 Localisation du Matériel de Chantier")
st.write("Visualisez la position géographique de vos équipements et conteneurs sur vos différents sites d'intervention.")

# Création de coordonnées fictives centrées sur votre région opérationnelle (Maine-et-Loire / Pays de la Loire) pour l'affichage de la carte
# (Ces données seront à remplacer par vos lignes de base de données plus tard)
map_data = pd.DataFrame(
    np.random.randn(5, 2) / [50, 50] + [47.33, -0.40],  # Centré autour de l'Anjou / Notre-Dame-d'Allençon
    columns=['lat', 'lon']
)
map_data['Nom'] = ['Conteneur Outillage principal', 'Échafaudage Lot A', 'Groupe Électrogène 1', 'Compresseur de chantier', 'Piping Kit DN400']

# Affichage de la carte interactive Streamlit
st.map(map_data, zoom=10)

# Petit tableau récapitulatif sous la carte
st.subheader("📋 Liste des équipements géolocalisés")
st.table(map_data[['Nom', 'lat', 'lon']])


# 5. MODULE : SUIVI DES EPI (ÉQUIPEMENTS DE PROTECTION INDIVIDUELLE)
st.header("🦺 Suivi et Attribution des EPI")
st.write("Registre de sécurité pour la distribution des équipements de protection individuelle aux équipes techniques.")

# Structure du tableau de bord de suivi des EPI
epi_data = pd.DataFrame({
    "Salarié / Équipe": ["Équipe Tuyauterie (Acier/Inox)", "Chef de chantier", "Technicien Site Angers", "Nouvelle recrue (Saint-Macaire)", "Intervenant Extérieur"],
    "Casque & Lunettes": ["✅ Distribué", "✅ Distribué", "✅ Distribué", "⚠️ À attribuer", "✅ Distribué"],
    "Chaussures de Sécurité": ["✅ Valide", "✅ Valide", "❌ À renouveler", "⚠️ À attribuer", "✅ Valide"],
    "Gants & Protections Auditives": ["✅ Distribué", "✅ Distribué", "✅ Distribué", "⚠️ À attribuer", "❌ Manquant"],
    "Dernier Contrôle": ["Juin 2026", "Mai 2026", "Avril 2026", "En attente", "Juin 2026"]
})

st.dataframe(epi_data, use_container_width=True)

# Barre latérale d'information pour la navigation rapide
st.sidebar.image("https://img.icons8.com/clouds/100/000000/crane.png", width=60)
st.sidebar.title("Navigation")
st.sidebar.info("Application Interne v1.2 — SOC Industrie. Utilisez ce panneau pour basculer entre vos différents modules d'inventaire.")
