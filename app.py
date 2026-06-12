import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, date, timedelta
import sqlite3
import qrcode
from io import BytesIO
import urllib.parse

# Configuration de la page
st.set_page_config(page_title="SOC Industrie - Gestion Matériel & Stocks", layout="wide")

URL_APPLICATION_EN_LIGNE = "https://soc-industrie-app-z5wnlx3n2pmnbcn5uvy.streamlit.app"
ADRESSE_SIEGE = "70 route de brissac - ZA la Jailletière - 49380 TERRANJOU"
COORD_SIEGE = (47.2662, -0.4355)
MAIL_OLIVIER = "owasse@soc.fr"
PHOTO_DEFAUT = "https://cdn-icons-png.flaticon.com/512/4054/4054615.png" # Icône par défaut si pas de photo

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def connexion_db():
    return sqlite3.connect('gestion_soc_v5.db')

def initialiser_db():
    conn = connexion_db()
    cursor = conn.cursor()
    
    # Table Matériel avec Photo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, modele TEXT, num_serie TEXT,
            statut TEXT DEFAULT 'A l''agence', photo_url TEXT,
            dernier_controle TEXT, intervalle_mois INTEGER, prochain_controle TEXT
        )
    ''')
    
    # Table Historique / Réservations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mouvements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materiel_id INTEGER, technicien TEXT, num_affaire TEXT,
            adresse_chantier TEXT, lat REAL, lon REAL, date_demande TEXT,
            date_debut TEXT, date_fin TEXT, statut_mouvement TEXT, 
            date_retrait_reel TEXT, date_retour_reel TEXT
        )
    ''')
    
    # Table Stocks avec Photo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, marque TEXT, reference TEXT, fournisseur TEXT,
            quantite INTEGER, seuil_mini INTEGER, seuil_maxi INTEGER,
            type_article TEXT DEFAULT 'Consommable', photo_url TEXT
        )
    ''')
    
    # Table Sorties de Stocks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sorties_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER, technicien TEXT, num_affaire TEXT,
            quantite_sortie INTEGER, date_sortie TEXT
        )
    ''')
    conn.commit()
    conn.close()

initialiser_db()

# --- ENVOI DE MAIL ---
def generer_lien_mail(sujet, corps):
    corps_encode = urllib.parse.quote(corps)
    sujet_encode = urllib.parse.quote(sujet)
    return f"mailto:{MAIL_OLIVIER}?subject={sujet_encode}&body={corps_encode}"

# --- CHARGEMENT DES DONNÉES ---
conn = connexion_db()
df_mat = pd.read_sql_query("SELECT * FROM materiel", conn)
df_mouvements_tous = pd.read_sql_query("""
    SELECT m.*, mat.nom, mat.modele, mat.num_serie, mat.photo_url 
    FROM mouvements m 
    JOIN materiel mat ON m.materiel_id = mat.id
""", conn) if not df_mat.empty else pd.DataFrame()
df_stock_total = pd.read_sql_query("SELECT * FROM stocks", conn)
conn.close()

# --- PARAMÈTRE DE RETRAIT SCAN QR CODE ---
id_scanne = None
try:
    if "mat_id" in st.query_parameters:
        id_scanne = int(st.query_parameters["mat_id"])
except:
    pass

st.title("🛠️ SOC Industrie : Logistique, Matériel & Visuels")

# --- INTERACTION QR CODE ---
if id_scanne and not df_mat.empty:
    mat_scanne = df_mat[df_mat['id'] == id_scanne]
    if not mat_scanne.empty:
        row_mat = mat_scanne.iloc[0]
        st.warning(f"📱 **QR Code Flashé** : **{row_mat['nom']}** ({row_mat['modele']})")
        
        # Affichage visuel de la machine scannée
        p_url = row_mat['photo_url'] if row_mat['photo_url'] else PHOTO_DEFAUT
        st.image(p_url, width=150)
        
        conn = connexion_db()
        res_attente = pd.read_sql_query("SELECT * FROM mouvements WHERE materiel_id=? AND statut_mouvement='Réservé' ORDER BY date_debut ASC LIMIT 1", conn)
        conn.close()
        
        if row_mat['statut'] == "A l'agence" and not res_attente.empty:
            res = res_attente.iloc[0]
            st.info(f"👉 Réservation pour : **{res['technicien']}** (Affaire : {res['num_affaire']})")
            if st.button("✅ Valider mon Retrait de l'Agence"):
                conn = connexion_db()
                conn.execute("UPDATE materiel SET statut='En Chantier' WHERE id=?", (id_scanne,))
                conn.execute("UPDATE mouvements SET statut_mouvement='Sorti (En Cours)', date_retrait_reel=? WHERE id=?", (date.today().strftime('%Y-%m-%d'), res['id']))
                conn.commit()
                conn.close()
                st.success("Sortie validée ! Bon chantier.")
                st.rerun()
                
        elif row_mat['statut'] == "En Chantier":
            if st.button("🏢 Valider le Retour définitif à l'Agence"):
                conn = connexion_db()
                conn.execute("UPDATE materiel SET statut='A l''agence' WHERE id=?", (id_scanne,))
                conn.execute("UPDATE mouvements SET statut_mouvement='Retourné', date_retour_reel=? WHERE materiel_id=? AND statut_mouvement='Sorti (En Cours)'", (date.today().strftime('%Y-%m-%d'), id_scanne))
                conn.commit()
                conn.close()
                st.success("Matériel de retour au dépôt !")
                st.rerun()

# --- ONGLETS PRINCIPAUX ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🗺️ Planification & Carte", "📅 Planifier une Réservation", 
    "📦 Stocks Consommables", "🦺 Suivi des EPI", "📱 QR Codes", "➕ Administration"
])

# --- TAB 1 : MAP & PLANNING ---
with tab1:
    st.subheader("Suivi Géographique Actuel")
    m = folium.Map(location=[47.3, -0.4], zoom_start=9)
    folium.Marker(COORD_SIEGE, popup="<b>SIÈGE SOC</b>", icon=folium.Icon(color="red", icon="home")).add_to(m)
    st_folium(m, width=1200, height=300)
    
    st.write("### 📋 Statut Visuel du Parc Machine")
    if not df_mat.empty:
        # Affichage sous forme de "Cartes" visuelles
        cols_m = st.columns(4)
        for idx, row in df_mat.iterrows():
            with cols_m[idx % 4]:
                url_i = row['photo_url'] if row['photo_url'] else PHOTO_DEFAUT
                st.image(url_i, width=120)
                st.markdown(f"**{row['nom']}** ({row['modele']})")
                st.caption(f"S/N: {row['num_serie']} | Statut: `{row['statut']}`")
                st.write("---")
    else:
        st.info("Aucune machine enregistrée.")

# --- TAB 2 : CRÉER UNE RÉSERVATION ---
with tab2:
    st.subheader("🗓️ Planifier une Réservation")
    if df_mat.empty: st.info("Aucune machine disponible.")
    else:
        with st.form("form_res"):
            mat_id = st.selectbox("Équipement", df_mat['id'].tolist(), format_func=lambda x: f"{df_mat[df_mat['id']==x]['nom'].values[0]}")
            tech = st.text_input("Technicien")
            n_affaire = st.text_input("N° d'Affaire")
            adresse = st.text_input("Adresse chantier", value=ADRESSE_SIEGE)
            d_deb = st.date_input("Début", date.today())
            d_fi = st.date_input("Fin", date.today() + timedelta(days=5))
            
            if st.form_submit_button("Enregistrer la réservation"):
                conn = connexion_db()
                conn.execute("INSERT INTO mouvements (materiel_id, technicien, num_affaire, adresse_chantier, lat, lon, date_demande, date_debut, date_fin, statut_mouvement) VALUES (?,?,?,?,?,?,?,?,?,'Réservé')", (mat_id, tech, n_affaire, adresse, COORD_SIEGE[0], COORD_SIEGE[1], date.today().strftime('%Y-%m-%d'), str(d_deb), str(d_fi)))
                conn.commit()
                conn.close()
                st.success("Réservé !")
                st.rerun()

# --- TAB 3 : STOCKS CONSOMMABLES ---
with tab3:
    st.subheader("📦 Stock Consommables Atelier")
    df_conso = df_stock_total[df_stock_total['type_article'] == 'Consommable'] if not df_stock_total.empty else pd.DataFrame()
    if not df_conso.empty:
        # Affichage en grille avec Photos !
        c_index = st.columns(4)
        for idx, row in df_conso.iterrows():
            with c_index[idx % 4]:
                img_url = row['photo_url'] if row['photo_url'] else PHOTO_DEFAUT
                st.image(img_url, width=100)
                st.markdown(f"**{row['nom']}**")
                st.caption(f"Réf: {row['reference']} | Qté : **{row['quantite']}**")
        
        st.write("---")
        with st.form("form_sort_c"):
            art_id = st.selectbox("Article prélevé", df_conso['id'].tolist(), format_func=lambda x: df_conso[df_conso['id']==x]['nom'].values[0])
            t_nom = st.text_input("Nom Tech")
            a_nom = st.text_input("N° d'affaire")
            q_s = st.number_input("Quantité", min_value=1, value=1)
            if st.form_submit_button("Déclarer la sortie"):
                conn = connexion_db()
                conn.execute("UPDATE stocks SET quantite = quantite - ? WHERE id = ?", (q_s, art_id))
                conn.commit()
                conn.close()
                st.success("Stock mis à jour !")
                st.rerun()

# --- TAB 4 : EPI ---
with tab4:
    st.subheader("🦺 Équipements de Sécurité (EPI)")
    df_epi = df_stock_total[df_stock_total['type_article'] == 'EPI'] if not df_stock_total.empty else pd.DataFrame()
    if not df_epi.empty:
        c_epi = st.columns(4)
        for idx, row in df_epi.iterrows():
            with c_epi[idx % 4]:
                img_url = row['photo_url'] if row['photo_url'] else PHOTO_DEFAUT
                st.image(img_url, width=100)
                st.markdown(f"**{row['nom']}**")
                st.caption(f"Marque: {row['marque']} | En stock: {row['quantite']}")
        
        st.write("---")
        with st.form("f_epi"):
            epi_id = st.selectbox("EPI demandé", df_epi['id'].tolist(), format_func=lambda x: df_epi[df_epi['id']==x]['nom'].values[0])
            sal = st.text_input("Salarié demandeur")
            motif = st.text_input("Affaire / Motif")
            if st.form_submit_button("Générer le Mail pour Olivier"):
                n_epi = df_epi[df_epi['id']==epi_id]['nom'].values[0]
                s_mail = f"[EPI] Demande de {sal}"
                c_mail = f"Bonjour Olivier,\n\n{sal} demande l'EPI suivant : {n_epi}.\nMotif: {motif}."
                st.markdown(f'<a href="{generer_lien_mail(s_mail, c_mail)}" target="_blank" style="padding:10px; background-color:#FF4B4B; color:white; border-radius:5px; text-decoration:none; font-weight:bold;">📢 Envoyer à owasse@soc.fr</a>', unsafe_allow_html=True)

# --- TAB 5 : QR CODES ---
with tab5:
    st.subheader("📱 Vos étiquettes QR Codes")
    if not df_mat.empty:
        for idx, row in df_mat.iterrows():
            lien_qr = f"{URL_APPLICATION_EN_LIGNE}/?mat_id={row['id']}"
            qr = qrcode.QRCode(version=1, box_size=3, border=1)
            qr.add_data(lien_qr)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.write(f"**ID {row['id']} - {row['nom']}**")
            st.image(buf.getvalue())
            st.write("---")

# --- TAB 6 : ADMINISTRATION (AJOUT AVEC PHOTOS) ---
with tab6:
    st.subheader("⚙️ Panneau d'Administration")
    colA, colB = st.columns(2)
    with colA:
        st.write("### ➕ Ajouter une Machine")
        with st.form("f_add_m"):
            n = st.text_input("Nom de la machine")
            m = st.text_input("Marque / Modèle")
            s = st.text_input("N° de Série")
            p = st.text_input("Lien URL de la Photo (Optionnel)", value="")
            if st.form_submit_button("Enregistrer Machine"):
                conn = connexion_db()
                conn.execute("INSERT INTO materiel (nom, modele, num_serie, statut, photo_url) VALUES (?,?,?,'A l''agence',?)", (n, m, s, p))
                conn.commit()
                conn.close()
                st.success("Ajouté !")
                st.rerun()
                
    with colB:
        st.write("### ➕ Ajouter un Consommable / EPI")
        with st.form("f_add_s"):
            n_s = st.text_input("Désignation")
            t_s = st.selectbox("Type", ["Consommable", "EPI"])
            m_s = st.text_input("Marque")
            r_s = st.text_input("Référence")
            f_s = st.text_input("Fournisseur")
            p_s = st.text_input("Lien URL de la Photo (Optionnel)", value="")
            q_i = st.number_input("Stock initial", min_value=0, value=5)
            if st.form_submit_button("Enregistrer l'Article"):
                conn = connexion_db()
                conn.execute("INSERT INTO stocks (nom, marque, reference, fournisseur, quantite, seuil_mini, seuil_maxi, type_article, photo_url) VALUES (?,?,?,?,?,5,100,?,?)", (n_s, m_s, r_s, f_s, q_i, t_s, p_s))
                conn.commit()
                conn.close()
                st.success("Article enregistré !")
                st.rerun()
