import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import sqlite3
import qrcode
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Suivi Matériel - Ombrières", layout="wide")
st.title("🛠️ Gestion et Traçabilité du Matériel (Option QR Code)")

# --- 1. FONCTIONS DE GESTION DE LA BASE DE DONNÉES (SQLite) ---
def connexion_db():
    return sqlite3.connect('gestion_materiel.db')

def initialiser_db():
    conn = connexion_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            statut TEXT NOT NULL,
            detenteur TEXT,
            ville TEXT,
            lat REAL,
            lon REAL,
            prochain_etalonnage TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM materiel")
    if cursor.fetchone()[0] == 0:
        donnees_demo = [
            ("Appareil de mesure d'isolement (Solaire)", "En Service", "Jean D.", "Angers", 47.4784, -0.5632, "2026-08-15"),
            ("Caméra Thermique FLIR", "Disponible", "Dépôt", "Cholet", 47.0600, -0.8800, "2026-11-20"),
            ("Testeur de courbe IV (Photovoltaïque)", "Alerte Étalonnage", "Lucas M.", "Saumur", 47.2600, -0.0800, "2026-05-01")
        ]
        cursor.executemany('''
            INSERT INTO materiel (nom, statut, detenteur, ville, lat, lon, prochain_etalonnage)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', donnees_demo)
        conn.commit()
    conn.close()

initialiser_db()

def charger_donnees():
    conn = connexion_db()
    df = pd.read_sql_query("SELECT * FROM materiel", conn)
    conn.close()
    return df

df = charger_donnees()

# --- DÉTECTION SCAN QR CODE ---
query_params = st.query_params
id_scanne = None
if "mat_id" in query_params:
    id_scanne = int(query_params["mat_id"])

# --- 2. BARRE LATÉRALE ---
st.sidebar.header("📦 État des Stocks (Consommables)")
stocks = {"Connecteurs MC4": 45, "Câble DC 4mm² (m)": 200, "Sprays traçage": 3}
for art, qte in stocks.items():
    if qte < 5:
        st.sidebar.error(f"⚠️ {art} : {qte} restants (À commander)")
    else:
        st.sidebar.success(f"✅ {art} : {qte}")

# --- 3. ONGLETS PRINCIPAUX ---
onglet1, onglet2, onglet3, onglet4, onglet5 = st.tabs([
    "🗺️ Carte & Localisation", 
    "📅 Réservations & Statuts", 
    "📐 Étalonnages", 
    "📱 Générer QR Codes",
    "➕ Ajouter du Matériel"
])

# --- ONGLET 1 : LA CARTE ---
with onglet1:
    st.subheader("Localisation du matériel sur les chantiers")
    m = folium.Map(location=[47.25, -0.3], zoom_start=9)
    for idx, row in df.iterrows():
        couleur = "green" if row['statut'] == "Disponible" else "blue" if row['statut'] == "En Service" else "red"
        texte_bulle = f"<b>{row['nom']}</b><br>Statut: {row['statut']}<br>Responsable: {row['detenteur']}<br>Lieu: {row['ville']}"
        folium.Marker([row['lat'], row['lon']], popup=texte_bulle, tooltip=row['nom'], icon=folium.Icon(color=couleur)).add_to(m)
    st_folium(m, width=1000, height=500)

# --- ONGLET 2 : RÉSERVATIONS / SCANS ---
with onglet2:
    if id_scanne:
        st.warning(f"🎯 MATÉRIEL SCANNÉ PAR QR CODE : {df[df['id'] == id_scanne]['nom'].values[0]}")
    
    st.subheader("Registre du matériel")
    st.dataframe(df[["id", "nom", "statut", "detenteur", "ville"]], use_container_width=True, hide_index=True)
    
    st.write("---")
    st.subheader("Prendre possession du matériel / Transférer")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        index_defaut = df['id'].tolist().index(id_scanne) if id_scanne in df['id'].tolist() else 0
        id_choisi = st.selectbox("Sélectionner l'ID du matériel", df['id'].tolist(), index=index_defaut)
        nom_materiel_choisi = df[df['id'] == id_choisi]['nom'].values[0]
        st.caption(f"Sélection : {nom_materiel_choisi}")
    with col2:
        nouveau_statut = st.selectbox("Nouveau statut", ["En Service", "Disponible", "Alerte Étalonnage", "En Réparation"])
    with col3:
        collaborateur = st.text_input("Votre Nom / Prénom", value="" if id_scanne else "Dépôt")
    with col4:
        destination = st.text_input("Ville du chantier actuel", value="" if id_scanne else "Dépôt")
        
    villes_coordonnees = {"Angers": (47.4784, -0.5632), "Cholet": (47.0600, -0.8800), "Saumur": (47.2600, -0.0800), "Dépôt": (47.47, -0.56)}

    if st.button("Valider la prise de possession 📱"):
        lat, lon = villes_coordonnees.get(destination, (47.4784, -0.5632))
        conn = connexion_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE materiel SET statut = ?, detenteur = ?, ville = ?, lat = ?, lon = ? WHERE id = ?
        ''', (nouveau_statut, collaborateur, destination, lat, lon, id_choisi))
        conn.commit()
        conn.close()
        
        st.success(f"Possession validée pour le matériel : {nom_materiel_choisi} !")
        st.query_params.clear()
        st.rerun()

# --- ONGLET 3 : ÉTALONNAGES ---
with onglet3:
    st.subheader("Suivi de la maintenance réglementaire")
    date_du_jour = datetime.now().date()
    for idx, row in df.iterrows():
        date_etalon = datetime.strptime(row['prochain_etalonnage'], "%Y-%m-%d").date()
        jours_restants = (date_etalon - date_du_jour).days
        col_m1, col_m2 = st.columns([3, 1])
        with col_m1: st.write(f"**{row['nom']}** (Étalonnage : {row['prochain_etalonnage']})")
        with col_m2:
            if jours_restants < 0: st.error(f"❌ PÉRIMÉ ({-jours_restants} j)")
            elif jours_restants < 90: st.warning(f"⚠️ À planifier ({jours_restants} j)")
            else: st.success("✅ Conforme")

# --- ONGLET 4 : GÉNÉRATEUR DE QR CODES ---
with onglet4:
    st.subheader("Générer les QR Codes à coller sur votre matériel")
    st.write("Imprimez ces codes. Lorsqu'un technicien le flashera, l'application s'ouvrira directement sur cet appareil.")
    
    adresse_appli = "http://localhost:8501" 
    
    for idx, row in df.iterrows():
        col_q1, col_q2 = st.columns([1, 3])
        with col_q1:
            lien_qr = f"{adresse_appli}/?mat_id={row['id']}"
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(lien_qr)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), width=150)
        with col_q2:
            st.write(f"### ID {row['id']} : {row['nom']}")
            st.caption(f"Lien encodé : `{lien_qr}`")
            st.write("👉 *Faites un clic droit sur l'image pour l'enregistrer et l'imprimer.*")
        st.write("---")

# --- ONGLET 5 : AJOUTER DU MATÉRIEL ---
with onglet5:
    st.subheader("Entrée d'un nouvel équipement")
    with st.form("ajout_materiel_form"):
        nom_neuf = st.text_input("Nom de l'appareil")
        date_etalon_neuf = st.date_input("Date du prochain étalonnage")
        submit = st.form_submit_button("Ajouter au parc") # <-- Correction ici
        if submit and nom_neuf:
            conn = connexion_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO materiel (nom, statut, detenteur, ville, lat, lon, prochain_etalonnage) VALUES (?, ?, ?, ?, ?, ?, ?)', (nom_neuf, "Disponible", "Dépôt", "Dépôt", 47.47, -0.56, str(date_etalon_neuf)))
            conn.commit()
            conn.close()
            st.success("Appareil ajouté !")
            st.rerun()
