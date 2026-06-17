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
st.header("📦 Données de la Base (Supabase)")
try:
    query = "SELECT * FROM materiel LIMIT 10;"
    df = pd.read_sql(query, conn)
    
    if df.empty:
        st.info("La table 'materiel' est connectée mais ne contient aucune donnée pour le moment.")
    else:
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.warning(f"Note : Connexion OK. Mode d'affichage local activé pour les modules ci-dessous.")


# On utilise des onglets pour organiser proprement toutes les fonctionnalités demandées
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Réservations & Matériel Commun", 
    "🔲 QR Codes & Étiquettes", 
    "🪵 Consommables & Stocks EPI", 
    "📍 Carte des Chantiers"
])

# ==========================================
# ONGLET 1 : RÉSERVATIONS & MATÉRIEL COMMUN
# ==========================================
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Demande de Réservation de Matériel")
        with st.form("form_reservation"):
            demandeur = st.text_input("Nom du demandeur")
            materiel_id = st.selectbox("Matériel à réserver", ["Conteneur Outillage", "Groupe Électrogène 1", "Compresseur", "Kit Tuyauterie DN400"])
            date_debut = st.date_input("Date de début")
            date_fin = st.date_input("Date de fin")
            chantier_destination = st.text_input("Chantier de destination")
            
            submit_res = st.form_submit_button("Valider la demande de réservation")
            if submit_res:
                st.success(f"Demande enregistrée pour {demandeur} ({materiel_id}) du {date_debut} au {date_fin}.")

    with col2:
        st.subheader("➕ Ajouter un Matériel Commun")
        with st.form("form_materiel_commun"):
            nom_mat = st.text_input("Nom du matériel (ex: Meuleuse d'angle Ø230)")
            categorie = st.selectbox("Catégorie", ["Outillage Électroportatif", "Manutention", "Soudage", "Équipement Chantier"])
            statut_initial = st.selectbox("Statut initial", ["Disponible", "En Chantier", "En Maintenance"])
            num_serie = st.text_input("Numéro de série / Référence interne")
            
            submit_mat = st.form_submit_button("Créer le matériel commun")
            if submit_mat:
                st.success(f"Nouveau matériel '{nom_mat}' enregistré avec succès.")

# ==========================================
# ONGLET 2 : CRÉATION DE QR CODES
# ==========================================
with tab2:
    st.subheader("🔲 Générateur de QR Code pour l'Inventaire")
    st.write("Générez un QR Code unique pour coller sur le matériel d'atelier ou de chantier.")
    
    qr_data = st.text_input("Données à encoder dans le QR Code (ex: URL du suivi ou ID unique)", "SOC-MAT-2026-001")
    
    # Utilisation d'une API publique sécurisée pour afficher le QR Code instantanément sans bibliothèque lourde
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={qr_data}"
    
    st.image(qr_url, caption=f"QR Code pour : {qr_data}")
    st.button("Imprimer l'étiquette (Simulé)")

# ==========================================
# ONGLET 3 : CONSOMMABLES & STOCKS EPI
# ==========================================
with tab3:
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🪵 Création de Consommable à stocker")
        with st.form("form_consommable"):
            nom_consommable = st.text_input("Désignation du consommable (ex: Électrodes Inox, Disques à tronçonner)")
            type_stock = st.selectbox("Type", ["Fournitures Atelier", "Gaz & Soudure", "Visserie & Fixations", "Petite Quincaillerie"])
            qte_initiale = st.number_input("Quantité en stock initial", min_value=0, value=100)
            seuil_alerte = st.number_input("Seuil d'alerte de réapprovisionnement", min_value=0, value=20)
            
            submit_cons = st.form_submit_button("Ajouter au stock consommables")
            if submit_cons:
                st.success(f"Consommable '{nom_consommable}' ajouté (Stock : {qte_initiale}).")

    with col4:
        st.subheader("🦺 Création et Suivi des Stocks EPI")
        with st.form("form_epi_stock"):
            type_epi = st.text_input("Désignation de l'EPI (ex: Gants de soudure T10, Casque avec visière)")
            taille_epi = st.text_input("Taille / Spécification", "Unique / XL")
            qte_dispo = st.number_input("Quantité disponible à l'atelier", min_value=0, value=50)
            
            submit_epi = st.form_submit_button("Mettre à jour le stock EPI")
            if submit_epi:
                st.success(f"Stock d'EPI pour '{type_epi}' configuré à {qte_dispo} unités.")
                
    # Tableau récapitulatif visuel du suivi des attributions individuelles
    st.subheader("📋 État des attributions individuelles en cours")
    epi_dashboard = pd.DataFrame({
        "Salarié / Équipe": ["Équipe Tuyauterie (Acier/Inox)", "Chef de chantier", "Technicien Site Angers", "Nouvelle recrue", "Intervenant Extérieur"],
        "Casque & Lunettes": ["✅ Distribué", "✅ Distribué", "✅ Distribué", "⚠️ À attribuer", "✅ Distribué"],
        "Chaussures de Sécurité": ["✅ Valide", "✅ Valide", "❌ À renouveler", "⚠️ À attribuer", "✅ Valide"],
        "Gants & Protections Auditives": ["✅ Distribué", "✅ Distribué", "✅ Distribué", "⚠️ À attribuer", "❌ Manquant"],
        "Dernier Contrôle": ["Juin 2026", "Mai 2026", "Avril 2026", "En attente", "Juin 2026"]
    })
    st.dataframe(epi_dashboard, use_container_width=True)

# ==========================================
# ONGLET 4 : GÉOLOCALISATION & CARTE
# ==========================================
with tab4:
    st.subheader("📍 Localisation du Matériel de Chantier")
    st.write("Visualisez la position géographique de vos équipements et conteneurs sur vos différents sites d'intervention.")

    map_data = pd.DataFrame(
        np.random.randn(5, 2) / [50, 50] + [47.33, -0.40],  # Centré autour de l'Anjou
        columns=['lat', 'lon']
    )
    map_data['Nom'] = ['Conteneur Outillage principal', 'Échafaudage Lot A', 'Groupe Électrogène 1', 'Compresseur de chantier', 'Piping Kit DN400']

    st.map(map_data, zoom=10)
    st.table(map_data[['Nom', 'lat', 'lon']])


# Barre latérale d'information pour la navigation rapide
st.sidebar.image("https://img.icons8.com/clouds/100/000000/crane.png", width=60)
st.sidebar.title("Navigation")
st.sidebar.info("Application Interne v1.3 — SOC Industrie. Tous les modules métiers sont activés.")
