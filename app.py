import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, date, timedelta
import sqlite3
import qrcode
from io import BytesIO
from geopy.geocoders import Nominatim

# Configuration de la page
st.set_page_config(page_title="SOC Industrie - Gestion Pro", layout="wide")

# --- PARAMÈTRE DE L'URL DE TON APPLICATION ---
# REMPLACE ICI par ton adresse finale exacte (ex: https://soc-industrie-app.streamlit.app)
URL_APPLICATION_EN_LIGNE = "https://soc-industrie-app.streamlit.app"

ADRESSE_SIEGE = "70 route de brissac - ZA la Jailletière - 49380 TERRANJOU"
COORD_SIEGE = (47.2662, -0.4355)

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

def charger_stocks():
    conn = connexion_db()
    df = pd.read_sql_query("SELECT * FROM stocks", conn)
    conn.close()
    return df

df_mat = charger_materiel()
df_stock = charger_stocks()

# --- GESTION DES SCANS QR CODE (CORRIGÉE) ---
id_scanne = None
if "mat_id" in st.query_parameters:
    id_scanne = st.query_parameters["mat_id"]

st.title("🛠️ SOC Industrie : Suivi Expert du Matériel")

# Si un QR code est flashé
if id_scanne:
    try:
        id_scanne_int = int(id_scanne)
        materiel_selectionne = df_mat[df_mat['id'] == id_scanne_int]
        
        if not materiel_selectionne.empty:
            mat = materiel_selectionne.iloc[0]
            st.warning(f"📢 **QR Code Scanné** : Appareil **{mat['nom']}** (S/N: {mat['num_serie']})")
            
            with st.expander("👉 Ouvrir la fiche d'affectation rapide", expanded=True):
                with st.form("form_flash"):
                    st.write(f"**Modèle :** {mat['modele']} | **Contrôle requis avant le :** {mat['prochain_controle']}")
                    nouveau_gars = st.text_input("Technicien qui prend le matériel", value=mat['detenteur'])
                    chantier = st.text_input("Adresse du chantier affecté", value=mat['adresse'])
                    d_fin = st.date_input("Date de fin prévue", date.today() + timedelta(days=7))
                    
                    if st.form_submit_button("Valider la prise de possession"):
                        lat, lon = geocoder_adresse(chantier)
                        conn = connexion_db()
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE materiel SET detenteur=?, adresse=?, lat=?, lon=?, date_debut=?, date_fin=?, statut='En Service'
                            WHERE id=?
                        ''', (nouveau_gars, chantier, lat, lon, str(date.today()), str(d_fin), id_scanne_int))
                        conn.commit()
                        conn.close()
                        st.success("Fiche mise à jour ! Bon chantier.")
                        # Nettoyer l'URL
                        st.query_parameters.clear()
                        st.rerun()
    except Exception as e:
        st.error(f"Erreur lors de la lecture du QR Code : {e}")

# --- ONGLETS PRINCIPAUX ---
onglet1, onglet2, onglet3, onglet4, onglet5 = st.tabs([
    "🗺️ Carte & Statuts", 
    "📅 Mouvements & Affectations", 
    "📦 Gestion des Consommables",
    "📱 Générer QR Codes",
    "➕ Ajouter du Matériel"
])

# --- ONGLET 1 : CARTE ---
with onglet1:
    st.subheader("Position du parc matériel")
    m = folium.Map(location=[47.3, -0.4], zoom_start=9)
    for _, row in df_mat.iterrows():
        color = "green" if row['adresse'] == ADRESSE_SIEGE else "blue"
        popup = f"<b>{row['nom']}</b> ({row['modele']})<br>S/N: {row['num_serie']}<br>Affectation: {row['detenteur']}"
        folium.Marker([row['lat'], row['lon']], popup=popup, tooltip=row['nom'], icon=folium.Icon(color=color)).add_to(m)
    st_folium(m, width=1200, height=450)

# --- ONGLET 2 : MOUVEMENTS ---
with onglet2:
    st.subheader("Historique et modification manuelle")
    st.dataframe(df_mat[["id", "nom", "modele", "num_serie", "detenteur", "adresse", "prochain_controle", "statut"]], use_container_width=True)

# --- ONGLET 3 : GESTION DES CONSOMMABLES ---
with onglet3:
    st.subheader("État des stocks consommables")
    if not df_stock.empty:
        cols = st.columns(len(df_stock))
        for i, (_, item) in enumerate(df_stock.iterrows()):
            if item['quantite'] <= item['seuil_mini']: color = "red"
            elif item['quantite'] >= item['seuil_maxi']: color = "green"
            else: color = "orange"
            
            with cols[i]:
                st.metric(label=item['nom'], value=item['quantite'], delta=f"Mini: {item['seuil_mini']}")
                st.markdown(f"<div style='height:10px; background-color:{color}; border-radius:5px;'></div>", unsafe_allow_html=True)

    st.write("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("### 🔄 Sortie / Réappro")
        if not df_stock.empty:
            item_id = st.selectbox("Choisir le composant", df_stock['id'].tolist(), format_func=lambda x: df_stock[df_stock['id']==x]['nom'].values[0])
            mouvement_qte = st.number_input("Quantité (+ pour réappro, - pour sortie)", value=0, key="qte_mvmt")
            if st.button("Mettre à jour le stock"):
                conn = connexion_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE stocks SET quantite = quantite + ? WHERE id = ?", (mouvement_qte, item_id))
                conn.commit()
                conn.close()
                st.rerun()
    with col_b:
        st.write("### ✨ Créer un nouveau composant")
        with st.form("nouveau_stock"):
            n_nom = st.text_input("Nom du consommable")
            n_qte = st.number_input("Quantité initiale", 0)
            n_mini = st.number_input("Seuil Alerte (Mini)", 0)
            n_maxi = st.number_input("Seuil Optimal (Maxi)", 0)
            if st.form_submit_button("Ajouter au stock"):
                conn = connexion_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO stocks (nom, quantite, seuil_mini, seuil_maxi) VALUES (?,?,?,?)", (n_nom, n_qte, n_mini, n_maxi))
                conn.commit()
                conn.close()
                st.rerun()

# --- ONGLET 4 : GÉNÉRATION QR CODES ---
with onglet4:
    st.subheader("Impression des QR Codes Industriels")
    
    if df_mat.empty:
        st.info("Ajoutez du matériel dans l'onglet suivant pour générer des QR Codes.")
    else:
        col1, col2 = st.columns(2)
        for index, row in df_mat.iterrows():
            # Création du lien parfait pour le smartphone
            lien_qr = f"{URL_APPLICATION_EN_LIGNE}/?mat_id={row['id']}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(lien_qr)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            with col1 if index % 2 == 0 else col2:
                st.write(f"**ID {row['id']} : {row['nom']}** - {row['modele']} (S/N: {row['num_serie']})")
                st.image(byte_im, width=150)
                st.caption(f"Lien : `{lien_qr}`")
                st.download_button(label="💾 Télécharger l'étiquette", data=byte_im, file_name=f"QR_{row['nom']}.png", mime="image/png", key=f"dl_{row['id']}")
                st.write("---")

# --- ONGLET 5 : AJOUT MATÉRIEL PRÉCIS ---
with onglet5:
    st.subheader("Enregistrer un nouvel équipement")
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
            st.success(f"✔️ {nom_n} enregistré ! Prochain contrôle : {prochain_ctrl}")
            st.rerun()
