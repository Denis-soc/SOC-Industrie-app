import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, date, timedelta
import sqlite3
import qrcode
from io import BytesIO
from geopy.geocoders import Nominatim
from streamlit.web.server.server import Server

# Configuration de la page
st.set_page_config(page_title="SOC Industrie - Gestion Pro", layout="wide")

ADRESSE_SIEGE = "70 route de brissac - ZA la Jailletière - 49380 TERRANJOU"
COORD_SIEGE = (47.2662, -0.4355)

# --- DÉTECTION AUTOMATIQUE DE L'URL DE L'APPLI ---
def obtenir_url_application():
    # Détecte si on est en ligne ou en local pour adapter le QR Code
    query_params = st.query_parameters
    # URL par défaut (sera surchargée proprement par les requêtes du navigateur)
    return "https://soc-industrie-app.streamlit.app" 

# --- GESTION BASE DE DONNÉES ---
def connexion_db():
    return sqlite3.connect('gestion_soc.db')

def initialiser_db():
    conn = connexion_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, modele TEXT, num_serie TEXT,
            statut TEXT, detenteur TEXT, adresse TEXT, 
            lat REAL, lon REAL, date_debut TEXT, date_fin TEXT, 
            dernier_controle TEXT, intervalle_mois INTEGER, prochain_controle TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, quantite INTEGER, seuil_mini INTEGER, seuil_maxi INTEGER
        )
    ''')
    conn.commit()
    conn.close()

initialiser_db()

# --- FONCTIONS REQUÊTES ---
def geocoder_adresse(adresse):
    try:
        geolocator = Nominatim(user_agent="soc_industrie_pro")
        location = geolocator.geocode(adresse)
        if location: return location.latitude, location.longitude
        return COORD_SIEGE
    except:
        return COORD_SIEGE

def charger_materiel():
    conn = connexion_db()
    df = pd.read_sql_query("SELECT * FROM materiel", conn)
    conn.close()
    return df

df_mat = charger_materiel()

# Récupération d'un éventuel scan QR Code (?mat_id=X dans l'URL)
id_scanne = st.query_parameters.get("mat_id", None)

st.title("🛠️ SOC Industrie : Suivi Expert du Matériel")

# --- SI UN QR CODE EST SCANNÉ ---
if id_scanne:
    id_scanne = int(id_scanne)
    materiel_selectionne = df_mat[df_mat['id'] == id_scanne]
    
    if not materiel_selectionne.empty:
        mat = materiel_selectionne.iloc[0]
        st.warning(f"📢 **QR Code Scanné** : Vous agissez sur l'appareil **{mat['nom']}** (S/N: {mat['num_serie']})")
        
        with st.expander("👉 Ouvrir la fiche d'affectation rapide", expanded=True):
            with st.form("form_flash"):
                st.write(f"**Modèle :** {mat['modele']} | **Contrôle requis avant le :** {mat['prochain_controle']}")
                nouveau_gars = st.text_input("Technicien qui prend le matériel", value=mat['detenteur'])
                chantier = st.text_input("Adresse du chantier affecté", value=mat['adresse'])
                d_fin = st.date_input("Date de fin prévue", date.today() + timedelta(days=7))
                
                if st.form_submit_button("Valider la prise de possession sur le terrain"):
                    lat, lon = geocoder_adresse(chantier)
                    conn = connexion_db()
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE materiel SET detenteur=?, adresse=?, lat=?, lon=?, date_debut=?, date_fin=?, statut='En Service'
                        WHERE id=?
                    ''', (nouveau_gars, chantier, lat, lon, str(date.today()), str(d_fin), id_scanne))
                    conn.commit()
                    conn.close()
                    st.success("Fiche mise à jour ! Bon chantier.")
                    st.query_parameters.clear() # Reset le scan
                    st.rerun()

# --- ONGLETS PRINCIPAUX ---
onglet1, onglet2, onglet3, onglet4 = st.tabs([
    "🗺️ Carte & Statuts", 
    "📅 Mouvements & Affectations", 
    "📱 Générer QR Codes",
    "➕ Ajouter du Matériel"
])

# --- ONGLET 1 : CARTE ---
with onglet1:
    st.subheader("Position du parc matériel")
    m = folium.Map(location=[47.3, -0.4], zoom_start=9)
    for _, row in df_mat.iterrows():
        color = "green" if row['adresse'] == ADRESSE_SIEGE else "blue"
        popup = f"<b>{row['nom']}</b> ({row['modele']})<br>S/N: {row['num_serie']}<br>Affecktation: {row['detenteur']}"
        folium.Marker([row['lat'], row['lon']], popup=popup, tooltip=row['nom'], icon=folium.Icon(color=color)).add_to(m)
    st_folium(m, width=1200, height=450)

# --- ONGLET 2 : MOUVEMENTS ---
with onglet2:
    st.subheader("Historique et modification manuelle")
    st.dataframe(df_mat[["id", "nom", "modele", "num_serie", "detenteur", "adresse", "prochain_controle", "statut"]], use_container_width=True)

# --- ONGLET 3 : GÉNÉRATION QR CODES ---
with onglet3:
    st.subheader("Impression des QR Codes Industriels")
    base_url = obtenir_url_application()
    
    col1, col2 = st.columns(2)
    for index, row in df_mat.iterrows():
        # Construction du lien absolu obligatoire pour les smartphones
        lien_qr = f"{base_url}/?mat_id={row['id']}"
        
        # Génération visuelle du QR
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(lien_qr)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = BytesIO()
        img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        with col1 if index % 2 == 0 else col2:
            st.write(f"**{row['nom']}** - {row['modele']} (S/N: {row['num_serie']})")
            st.image(byte_im, width=150)
            st.caption(f"Lien encodé : `{lien_qr}`")
            st.download_button(label="💾 Télécharger l'étiquette", data=byte_im, file_name=f"QR_{row['nom']}.png", mime="image/png")
            st.write("---")

# --- ONGLET 4 : AJOUT MATÉRIEL ULTRA-PRÉCIS ---
with onglet4:
    st.subheader("Enregistrer un nouvel équipement dans le système")
    with st.form("form_ajout_mat"):
        c1, c2 = st.columns(2)
        with c1:
            nom_n = st.text_input("Nom de l'appareil (ex: Caméra Thermique)")
            modele_n = st.text_input("Modèle / Marque (ex: FLIR E8)")
            num_serie_n = st.text_input("Numéro de Série (S/N)")
        with c2:
            dernier_ctrl = st.date_input("Date du dernier contrôle", date.today())
            intervalle = st.number_input("Intervalle entre 2 contrôles (en mois)", min_value=1, value=12)
            affectation_initiale = st.text_input("Assigné à (par défaut : Entreprise)", value="Entreprise")
            
        if st.form_submit_button("Créer l'équipement et générer son profil"):
            # Calcul de la prochaine date de contrôle réglementaire
            prochain_ctrl = dernier_ctrl + timedelta(days=int(intervalle * 30.5))
            lat, lon = COORD_SIEGE
            
            conn = connexion_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO materiel (nom, modele, num_serie, statut, detenteur, adresse, lat, lon, date_debut, date_fin, dernier_controle, intervalle_mois, prochain_controle)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nom_n, modele_n, num_serie_n, "Disponible", affectation_initiale, ADRESSE_SIEGE, lat, lon, "-", "-", str(dernier_ctrl), intervalle, str(prochain_ctrl)))
            conn.commit()
            conn.close()
            st.success(f"✔️ {nom_n} enregistré avec succès ! Prochain contrôle le {prochain_ctrl}")
            st.rerun()
