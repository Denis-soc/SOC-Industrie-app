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

# --- INITIALISATION ET EVOLUTION DE LA BASE DE DONNÉES ---
def connexion_db():
    return sqlite3.connect('gestion_soc_v3.db')

def initialiser_db():
    conn = connexion_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materiel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, modele TEXT, num_serie TEXT,
            statut TEXT DEFAULT 'A l''agence', 
            dernier_controle TEXT, intervalle_mois INTEGER, prochain_controle TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mouvements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materiel_id INTEGER,
            technicien TEXT,
            num_affaire TEXT,
            adresse_chantier TEXT,
            lat REAL,
            lon REAL,
            date_demande TEXT,
            date_debut TEXT,
            date_fin TEXT,
            statut_mouvement TEXT, 
            date_retrait_reel TEXT,
            date_retour_reel TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT, quantite INTEGER, seuil_mini INTEGER, seuil_maxi INTEGER,
            type_article TEXT DEFAULT 'Consommable'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sorties_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            technicien TEXT,
            num_affaire TEXT,
            quantite_sortie INTEGER,
            date_sortie TEXT
        )
    ''')
    conn.commit()
    conn.close()

initialiser_db()

# --- SIMULATION ENVOI DE MAIL AUTOMATIQUE (LIEN DIRECT MAILTO) ---
def generer_lien_mail(sujet, corps):
    corps_encode = urllib.parse.quote(corps)
    sujet_encode = urllib.parse.quote(sujet)
    return f"mailto:{MAIL_OLIVIER}?subject={sujet_encode}&body={corps_encode}"

# --- CHARGEMENT DES DONNÉES SÉCURISÉ ---
conn = connexion_db()
df_mat = pd.read_sql_query("SELECT * FROM materiel", conn)
df_mouvements_tous = pd.read_sql_query("""
    SELECT m.*, mat.nom, mat.modele, mat.num_serie 
    FROM mouvements m 
    JOIN materiel mat ON m.materiel_id = mat.id
""", conn) if not df_mat.empty else pd.DataFrame()
df_stock_total = pd.read_sql_query("SELECT * FROM stocks", conn)
conn.close()

# --- NETTOYAGE DE L'HISTORIQUE (GARDE LES 3 DERNIERS MOIS) ---
if not df_mouvements_tous.empty:
    try:
        conn = connexion_db()
        limite_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        conn.execute("DELETE FROM mouvements WHERE statut_mouvement='Retourné' AND date_retour_reel < ?", (limite_date,))
        conn.commit()
        conn.close()
    except:
        pass

# --- CAPTURE DES PARAMÈTRES SCAN QR CODE ---
id_scanne = None
try:
    if "mat_id" in st.query_parameters:
        id_scanne = int(st.query_parameters["mat_id"])
except:
    pass

st.title("🛠️ SOC Industrie : Logistique & Matériel Pro")

# --- INTERACTION QR CODE (VALIDATION TERRAIN SUR SMARTPHONE) ---
if id_scanne and not df_mat.empty:
    mat_scanne = df_mat[df_mat['id'] == id_scanne]
    if not mat_scanne.empty:
        row_mat = mat_scanne.iloc[0]
        st.warning(f"📱 **QR Code Flashé** : Appareil **{row_mat['nom']}** ({row_mat['modele']})")
        
        conn = connexion_db()
        res_attente = pd.read_sql_query("SELECT * FROM mouvements WHERE materiel_id=? AND statut_mouvement='Réservé' ORDER BY date_debut ASC LIMIT 1", conn)
        conn.close()
        
        if row_mat['statut'] == "A l'agence" and not res_attente.empty:
            res = res_attente.iloc[0]
            st.info(f"👉 Réservation trouvée pour le tech **{res['technicien']}** (Affaire : {res['num_affaire']})")
            if st.button("✅ Valider mon Retrait de l'Agence (Départ Chantier)"):
                conn = connexion_db()
                conn.execute("UPDATE materiel SET statut='En Chantier' WHERE id=?", (id_scanne,))
                conn.execute("UPDATE mouvements SET statut_mouvement='Sorti (En Cours)', date_retrait_reel=? WHERE id=?", (date.today().strftime('%Y-%m-%d'), res['id']))
                conn.commit()
                conn.close()
                st.success("Matériel validé sorti ! Bon chantier.")
                st.rerun()
                
        elif row_mat['statut'] == "En Chantier":
            conn = connexion_db()
            mvt_en_cours = pd.read_sql_query("SELECT * FROM mouvements WHERE materiel_id=? AND statut_mouvement='Sorti (En Cours)' LIMIT 1", conn)
            conn.close()
            
            if st.button("🏢 Valider le Retour définitif à l'Agence"):
                conn = connexion_db()
                conn.execute("UPDATE materiel SET statut='A l''agence' WHERE id=?", (id_scanne,))
                if not mvt_en_cours.empty:
                    conn.execute("UPDATE mouvements SET statut_mouvement='Retourné', date_retour_reel=? WHERE id=?", (date.today().strftime('%Y-%m-%d'), mvt_en_cours.iloc[0]['id']))
                conn.commit()
                conn.close()
                st.success("Matériel bien enregistré comme déposé au dépôt. Merci !")
                st.rerun()
        else:
            st.info("Appareil disponible à l'agence. Aucune réservation en attente à valider pour le moment.")

# --- ONGLETS PRINCIPAUX ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🗺️ Planification & Carte", 
    "📅 Planifier une Réservation", 
    "📦 Stocks Consommables",
    "🦺 Suivi des EPI",
    "📱 QR Codes",
    "➕ Administration"
])

# --- TAB 1 : MAP & PLANNING ---
with tab1:
    st.subheader("Suivi Géographique Actuel")
    m = folium.Map(location=[47.3, -0.4], zoom_start=9)
    folium.Marker(COORD_SIEGE, popup="<b>SIÈGE SOC INDUSTRIE</b>", icon=folium.Icon(color="red", icon="home")).add_to(m)
    
    if not df_mouvements_tous.empty:
        mvt_actifs = df_mouvements_tous[df_mouvements_tous['statut_mouvement'] == 'Sorti (En Cours)']
        for _, row in mvt_actifs.iterrows():
            folium.Marker([row['lat'], row['lon']], popup=f"<b>{row['nom']}</b><br>Tech: {row['technicien']}<br>Affaire: {row['num_affaire']}", icon=folium.Icon(color="blue", icon="wrench")).add_to(m)
    
    st_folium(m, width=1200, height=350)
    
    st.write("### 📜 File d'attente chronologique des mouvements (3 derniers mois)")
    if not df_mouvements_tous.empty:
        st.dataframe(df_mouvements_tous[["id", "nom", "num_serie", "technicien", "num_affaire", "date_debut", "date_fin", "statut_mouvement", "date_retrait_reel", "date_retour_reel"]], use_container_width=True)
    else:
        st.info("Aucun mouvement ni historique enregistré dans la base actuelle.")

# --- TAB 2 : CRÉER UNE RÉSERVATION ---
with tab2:
    st.subheader("🗓️ Réserver un matériel à la suite pour un futur projet")
    if df_mat.empty:
        st.info("Veuillez d'abord déclarer vos machines dans l'onglet '➕ Administration' pour pouvoir les réserver.")
    else:
        with st.form("form_reservation"):
            mat_id = st.selectbox("Choisir l'équipement", df_mat['id'].tolist(), format_func=lambda x: f"{df_mat[df_mat['id']==x]['nom'].values[0]} (S/N: {df_mat[df_mat['id']==x]['num_serie'].values[0]}) - [{df_mat[df_mat['id']==x]['statut'].values[0]}]")
            tech = st.text_input("Technicien Demandeur")
            n_affaire = st.text_input("N° d'Affaire / Projet")
            adresse = st.text_input("Adresse complète du chantier", value=ADRESSE_SIEGE)
            d_deb = st.date_input("Date de début prévue", date.today())
            d_fi = st.date_input("Date de fin prévue", date.today() + timedelta(days=5))
            
            if st.form_submit_button("📁 Enregistrer la demande de réservation"):
                # Simulation géocodage simple pour éviter le plantage
                lat, lon = COORD_SIEGE[0] + 0.02, COORD_SIEGE[1] + 0.03
                conn = connexion_db()
                conn.execute('''
                    INSERT INTO mouvements (materiel_id, technicien, num_affaire, adresse_chantier, lat, lon, date_demande, date_debut, date_fin, statut_mouvement)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Réservé')
                ''', (mat_id, tech, n_affaire, adresse, lat, lon, date.today().strftime('%Y-%m-%d'), str(d_deb), str(d_fi)))
                conn.commit()
                conn.close()
                
                sujet_mail = f"[LOGISTIQUE] Nouvelle demande de matériel - Affaire {n_affaire}"
                corps_mail = f"Bonjour Olivier,\n\nLe technicien {tech} vient de réserver un matériel pour l'affaire n°{n_affaire}.\nPériode du {d_deb} au {d_fi}.\n\nSystème Automatique SOC."
                lien_mailto = generer_lien_mail(sujet_mail, corps_mail)
                
                st.success("Demande ajoutée avec succès à la suite du planning !")
                st.markdown(f'<a href="{lien_mailto}" target="_blank" style="padding:10px; background-color:#FF4B4B; color:white; border-radius:5px; text-decoration:none; font-weight:bold;">📢 Cliquer ici pour notifier Olivier par Mail</a>', unsafe_allow_html=True)

# --- TAB 3 : STOCKS CONSOMMABLES ---
with tab3:
    st.subheader("📦 Liste du stock consommables d'atelier")
    df_conso = df_stock_total[df_stock_total['type_article'] == 'Consommable'] if not df_stock_total.empty else pd.DataFrame()
    if not df_conso.empty:
        st.dataframe(df_conso[["id", "nom", "quantite", "seuil_mini", "seuil_maxi"]], use_container_width=True)
        
        st.write("### 🔄 Déclarer une sortie de consommable sur un projet")
        with st.form("sortie_conso"):
            art_id = st.selectbox("Composant sorti", df_conso['id'].tolist(), format_func=lambda x: df_conso[df_conso['id']==x]['nom'].values[0])
            nom_tech = st.text_input("Nom du Technicien")
            aff_id = st.text_input("N° d'affaire affecté")
            qte_s = st.number_input("Quantité prélevée", min_value=1, value=1)
            
            if st.form_submit_button("Valider la sortie de stock"):
                conn = connexion_db()
                conn.execute("UPDATE stocks SET quantite = quantite - ? WHERE id = ?", (qte_s, art_id))
                conn.execute("INSERT INTO sorties_stocks (article_id, technicien, num_affaire, quantite_sortie, date_sortie) VALUES (?,?,?,?,?)", (art_id, nom_tech, aff_id, qte_s, date.today().strftime('%Y-%m-%d')))
                conn.commit()
                conn.close()
                st.success("Inventaire mis à jour !")
                st.rerun()
    else:
        st.info("Aucun consommable créé. Allez dans le dernier onglet pour ajouter des références.")

# --- TAB 4 : ÉQUIPEMENTS DE PROTECTION INDIVIDUELLE (EPI) ---
with tab4:
    st.subheader("🦺 Suivi et Demandes d'EPI")
    df_epi = df_stock_total[df_stock_total['type_article'] == 'EPI'] if not df_stock_total.empty else pd.DataFrame()
    if not df_epi.empty:
        st.dataframe(df_epi[["id", "nom", "quantite"]], use_container_width=True)
        
        st.write("### 📨 Faire une demande d'attribution d'EPI")
        with st.form("demande_epi"):
            epi_nom = st.selectbox("EPI requis", df_epi['nom'].tolist())
            demandeur = st.text_input("Nom du salarié")
            raison = st.text_input("N° d'affaire ou motif (ex: Renouvellement annuel)")
            
            if st.form_submit_button("Envoyer la demande d'EPI"):
                sujet_mail = f"[EPI] Nouvelle demande équipement de sécurité - {demandeur}"
                corps_mail = f"Bonjour Olivier,\n\nLe salarié {demandeur} fait une demande d'EPI pour l'article suivant : {epi_nom}.\nMotif / Projet : {raison}.\n\nMerci de valider l'affectation."
                lien_mailto = generer_lien_mail(sujet_mail, corps_mail)
                st.markdown(f'<a href="{lien_mailto}" target="_blank" style="padding:10px; background-color:#FF4B4B; color:white; border-radius:5px; text-decoration:none; font-weight:bold;">📢 Envoyer le mail de demande à Olivier</a>', unsafe_allow_html=True)
    else:
        st.info("Aucun article EPI enregistré. Utilisez l'onglet '➕ Administration' pour en créer.")

# --- TAB 5 : IMPRESSION DES CODES QR CODES ---
with tab5:
    st.subheader("📱 Générateur d'étiquettes QR Code pour les machines")
    if df_mat.empty:
        st.info("Aucun matériel enregistré.")
    else:
        c1, c2 = st.columns(2)
        for index, row in df_mat.iterrows():
            lien_qr = f"{URL_APPLICATION_EN_LIGNE}/?mat_id={row['id']}"
            qr = qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(lien_qr)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = BytesIO()
            img.save(buf, format="PNG")
            
            with c1 if index % 2 == 0 else c2:
                st.write(f"**ID {row['id']} - {row['nom']}** ({row['modele']})")
                st.image(buf.getvalue(), width=130)
                st.write("---")

# --- TAB 6 : ENREGISTREMENT ET ADMINISTRATION BASES ---
with tab6:
    st.subheader("⚙️ Panneau de configuration SOC")
    colA, colB = st.columns(2)
    with colA:
        st.write("### ➕ Ajouter une nouvelle machine")
        with st.form("add_mach"):
            n_m = st.text_input("Nom du matériel")
            m_m = st.text_input("Marque / Modèle")
            s_m = st.text_input("Numéro de Série (S/N)")
            if st.form_submit_button("Sauvegarder l'appareil"):
                conn = connexion_db()
                conn.execute("INSERT INTO materiel (nom, modele, num_serie, statut) VALUES (?,?,?,'A l''agence')", (n_m, m_m, s_m))
                conn.commit()
                conn.close()
                st.success("Appareil ajouté !")
                st.rerun()
                
    with colB:
        st.write("### ➕ Ajouter au catalogue (Stocks ou EPI)")
        with st.form("add_stock"):
            n_s = st.text_input("Désignation de l'article")
            t_s = st.selectbox("Catégorie de l'article", ["Consommable", "EPI"])
            q_i = st.number_input("Quantité de départ", min_value=0, value=10)
            if st.form_submit_button("Ajouter l'article"):
                conn = connexion_db()
                conn.execute("INSERT INTO stocks (nom, quantite, seuil_mini, seuil_maxi, type_article) VALUES (?,?,5,100,?)", (n_s, q_i, t_s))
                conn.commit()
                conn.close()
                st.success("Référence créée avec succès !")
                st.rerun()
