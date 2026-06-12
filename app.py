import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, date, timedelta
import sqlite3
import qrcode
from io import BytesIO
import urllib.parse
import base64

# Configuration de la page
st.set_page_config(page_title="SOC Industrie - Gestion Matériel & Stocks", layout="wide")

URL_APPLICATION_EN_LIGNE = "https://soc-industrie-app-z5wnlx3n2pmnbcn5uvy.streamlit.app"
ADRESSE_SIEGE = "70 route de brissac - ZA la Jailletière - 49380 TERRANJOU"
COORD_SIEGE = (47.2662, -0.4355)
MAIL_OLIVIER = "owasse@soc.fr"
PHOTO_DEFAUT = "https://cdn-icons-png.flaticon.com/512/4054/4054615.png"

# --- ENCODAGE / DÉCODAGE DES IMAGES EN BASE64 ---
def convertir_image_en_base64(fichier_image):
    if fichier_image is not None:
        bytes_data = fichier_image.read()
        base64_encoded = base64.b64encode(bytes_data).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_encoded}"
    return None

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def connexion_db():
    return sqlite3.connect('gestion_soc_v6.db')

def initialiser_db():
    conn = connexion_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, modele TEXT, num_serie TEXT,
            statut TEXT DEFAULT 'A l''agence', photo_data TEXT,
            dernier_controle TEXT, intervalle_mois INTEGER, prochain_controle TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mouvements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materiel_id INTEGER, technicien TEXT, num_affaire TEXT,
            adresse_chantier TEXT, lat REAL, lon REAL, date_demande TEXT,
            date_debut TEXT, date_fin TEXT, statut_mouvement TEXT, 
            date_retrait_reel TEXT, date_retour_reel TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, marque TEXT, reference TEXT, fournisseur TEXT,
            quantite INTEGER, seuil_mini INTEGER, seuil_maxi INTEGER,
            type_article TEXT DEFAULT 'Consommable', photo_data TEXT
        )
    ''')
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
    SELECT m.*, mat.nom, mat.modele, mat.num_serie, mat.photo_data 
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
        p_data = row_mat['photo_data'] if row_mat['photo_data'] else PHOTO_DEFAUT
        st.image(p_data, width=200)
        
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
        cols_m = st.columns(4)
        for idx, row in df_mat.iterrows():
            with cols_m[idx % 4]:
                img_data = row['photo_data'] if row['photo_data'] else PHOTO_DEFAUT
                st.image(img_data, width=140)
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
        c_index = st.columns(4)
        for idx, row in df_conso.iterrows():
            with c_index[idx % 4]:
                img_data = row['photo_data'] if row['photo_data'] else PHOTO_DEFAUT
                st.image(img_data, width=120)
                st.markdown(f"**{row['nom']}**")
                st.caption(f"Marque: {row['marque']} | Réf: {row['reference']}\n\nQté en stock : **{row['quantite']}**")
        
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
                img_data = row['photo_data'] if row['photo_data'] else PHOTO_DEFAUT
                st.image(img_data, width=120)
                st.markdown(f"**{row['nom']}**")
                st.caption(f"Marque: {row['marque']} | Réf: {row['reference']}\n\nEn stock: **{row['quantite']}**")
        
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

# --- TAB 6 : ADMINISTRATION (AJOUT, MODIFICATION AVEC GLISSER-DÉPOSER) ---
with tab6:
    st.subheader("⚙️ Panneau d'Administration")
    
    subtab_creer, subtab_modifier = st.tabs(["➕ Créer des Articles / Machines", "✏️ Modifier ou Supprimer un Article existant"])
    
    with subtab_creer:
        st.write("### ➕ Ajouter une Machine")
        # Utilisation de colonnes différentes pour ne pas bloquer l'upload dans un mini-formulaire étroit
        with st.form("f_add_m"):
            c1, c2 = st.columns(2)
            with c1:
                n = st.text_input("Nom de la machine")
                m = st.text_input("Marque / Modèle")
                s = st.text_input("N° de Série")
            with c2:
                fichier_photo_m = st.file_uploader("📸 Capture écran ou Photo (JPG/PNG) - Machine", type=["jpg", "jpeg", "png"], key="add_m_photo")
            
            if st.form_submit_button("Enregistrer Machine"):
                p_base64 = convertir_image_en_base64(fichier_photo_m)
                conn = connexion_db()
                conn.execute("INSERT INTO materiel (nom, modele, num_serie, statut, photo_data) VALUES (?,?,?,'A l''agence',?)", (n, m, s, p_base64))
                conn.commit()
                conn.close()
                st.success("Machine ajoutée au parc avec sa photo !")
                st.rerun()
                    
        st.write("---")
        st.write("### ➕ Ajouter un Consommable / EPI")
        with st.form("f_add_s"):
            c3, c4 = st.columns(2)
            with c3:
                n_s = st.text_input("Désignation")
                t_s = st.selectbox("Type", ["Consommable", "EPI"])
                m_s = st.text_input("Marque")
                r_s = st.text_input("Référence")
                f_s = st.text_input("Fournisseur")
                q_i = st.number_input("Stock initial", min_value=0, value=5)
            with c4:
                fichier_photo_s = st.file_uploader("📸 Capture écran ou Photo (JPG/PNG) - Article", type=["jpg", "jpeg", "png"], key="add_s_photo")
                
            if st.form_submit_button("Enregistrer l'Article"):
                p_base64_s = convertir_image_en_base64(fichier_photo_s)
                conn = connexion_db()
                conn.execute("INSERT INTO stocks (nom, marque, reference, fournisseur, quantite, seuil_mini, seuil_maxi, type_article, photo_data) VALUES (?,?,?,?,?,5,100,?,?)", (n_s, m_s, r_s, f_s, q_i, t_s, p_base64_s))
                conn.commit()
                conn.close()
                st.success("Article enregistré au catalogue !")
                st.rerun()

    with subtab_modifier:
        st.write("### ✏️ Éditer un Consommable ou un EPI")
        if df_stock_total.empty:
            st.info("Aucun article en stock à modifier pour le moment.")
        else:
            id_article_choisi = st.selectbox(
                "Sélectionner l'article à modifier ou à supprimer",
                options=df_stock_total['id'].tolist(),
                format_func=lambda x: f"[{df_stock_total[df_stock_total['id']==x]['type_article'].values[0]}] {df_stock_total[df_stock_total['id']==x]['nom'].values[0]} (Réf: {df_stock_total[df_stock_total['id']==x]['reference'].values[0]})"
            )
            
            art_actuel = df_stock_total[df_stock_total['id'] == id_article_choisi].iloc[0]
            
            with st.form("form_modification_article"):
                col_mod1, col_mod2 = st.columns(2)
                
                with col_mod1:
                    edit_nom = st.text_input("Désignation de l'article", value=art_actuel['nom'])
                    edit_type = st.selectbox("Catégorie / Type", ["Consommable", "EPI"], index=0 if art_actuel['type_article'] == "Consommable" else 1)
                    edit_marque = st.text_input("Marque", value=art_actuel['marque'])
                    edit_ref = st.text_input("Référence Fabricant", value=art_actuel['reference'])
                
                with col_mod2:
                    edit_fourn = st.text_input("Fournisseur", value=art_actuel['fournisseur'])
                    edit_qte = st.number_input("Quantité exacte actuellement en Stock", min_value=0, value=int(art_actuel['quantite']))
                    
                    st.caption("📷 Remplacer la photo existante (laisser vide pour la conserver) :")
                    fichier_photo_edit = st.file_uploader("Glisser une nouvelle capture d'écran", type=["jpg", "jpeg", "png"], key="edit_photo")
                
                btn_col1, btn_col2 = st.columns([1, 4])
                with btn_col1:
                    sauvegarder_changement = st.form_submit_button("💾 Enregistrer")
                with btn_col2:
                    supprimer_definitivement = st.form_submit_button("🗑️ Supprimer cet article")

            if sauvegarder_changement:
                # Si l'utilisateur a mis une nouvelle image, on la convertit, sinon on garde l'ancienne
                if fichier_photo_edit is not None:
                    nouveau_b64 = convertir_image_en_base64(fichier_photo_edit)
                else:
                    nouveau_b64 = art_actuel['photo_data']
                    
                conn = connexion_db()
                conn.execute('''
                    UPDATE stocks SET 
                    nom=?, type_article=?, marque=?, reference=?, fournisseur=?, quantite=?, photo_data=?
                    WHERE id=?
                ''', (edit_nom, edit_type, edit_marque, edit_ref, edit_fourn, edit_qte, nouveau_b64, id_article_choisi))
                conn.commit()
                conn.close()
                st.success(f"✔️ L'article '{edit_nom}' a été mis à jour !")
                st.rerun()
                
            if supprimer_definitivement:
                conn = connexion_db()
                conn.execute("DELETE FROM stocks WHERE id=?", (id_article_choisi,))
                conn.commit()
                conn.close()
                st.warning(f"L'article a été retiré du catalogue.")
                st.rerun()
