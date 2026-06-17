import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, date, timedelta
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

# --- CONNEXION GLOBALE SUPABASE ---
conn = st.connection("postgresql", type="sql")

# --- ENCODAGE DES IMAGES ---
def convertir_image_en_base64(fichier_image):
    if fichier_image is not None:
        try:
            bytes_data = fichier_image.read()
            base64_encoded = base64.b64encode(bytes_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_encoded}"
        except Exception:
            return None
    return None

# Affichage sécurisé des images
def afficher_image_securisee(image_source, width=120):
    if isinstance(image_source, str) and (image_source.startswith("http") or image_source.startswith("data:image")):
        try:
            st.image(image_source, width=width)
        except Exception:
            st.image(PHOTO_DEFAUT, width=width)
    else:
        st.image(PHOTO_DEFAUT, width=width)

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def initialiser_db():
    with conn.session as session:
        session.execute("""
            CREATE TABLE IF NOT EXISTS materiel (
                id SERIAL PRIMARY KEY,
                nom TEXT, modele TEXT, num_serie TEXT,
                statut TEXT DEFAULT 'A l''agence', photo_data TEXT,
                dernier_controle TEXT, intervalle_mois INTEGER, prochain_controle TEXT
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS mouvements (
                id SERIAL PRIMARY KEY,
                materiel_id INTEGER, technicien TEXT, num_affaire TEXT,
                adresse_chantier TEXT, lat REAL, lon REAL, date_demande TEXT,
                date_debut TEXT, date_fin TEXT, statut_mouvement TEXT, 
                date_retrait_reel TEXT, date_retour_reel TEXT
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id SERIAL PRIMARY KEY,
                nom TEXT, marque TEXT, reference TEXT, fournisseur TEXT,
                quantite INTEGER DEFAULT 0, seuil_mini INTEGER DEFAULT 5, seuil_maxi INTEGER DEFAULT 50,
                type_article TEXT DEFAULT 'Consommable', photo_data TEXT
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS variantes_stock (
                id SERIAL PRIMARY KEY,
                article_id INTEGER,
                caracteristique TEXT,
                quantite INTEGER DEFAULT 0,
                FOREIGN KEY(article_id) REFERENCES stocks(id) ON DELETE CASCADE
            )
        """)
        session.execute("""
            CREATE TABLE IF NOT EXISTS sorties_stocks (
                id SERIAL PRIMARY KEY,
                article_id INTEGER, variante_id INTEGER, technicien TEXT, num_affaire TEXT,
                quantite_sortie INTEGER, caracteristique TEXT, date_sortie TEXT
            )
        """)
        session.commit()

initialiser_db()

# Recalculer le total général dans la table stocks par sécurité
def recalculer_total_stock(article_id):
    with conn.session as session:
        res = session.execute("SELECT SUM(quantite) FROM variantes_stock WHERE article_id = :article_id", {"article_id": article_id}).fetchone()
        total = res[0] if res and res[0] is not None else 0
        session.execute("UPDATE stocks SET quantite = :total WHERE id = :article_id", {"total": total, "article_id": article_id})
        session.commit()

# --- ENVOI DE MAIL ---
def generer_lien_mail(sujet, corps):
    corps_encode = urllib.parse.quote(corps)
    sujet_encode = urllib.parse.quote(sujet)
    return f"mailto:{MAIL_OLIVIER}?subject={sujet_encode}&body={corps_encode}"

# --- CHARGEMENT DES DONNÉES ---
df_mat = conn.query("SELECT * FROM materiel ORDER BY id ASC;", ttl=0)
df_stock_total = conn.query("SELECT * FROM stocks ORDER BY id ASC;", ttl=0)
df_variantes_toutes = conn.query("SELECT * FROM variantes_stock ORDER BY id ASC;", ttl=0)

# --- LECTURE SÉCURISÉE DES PARAMÈTRES ---
id_scanne = None
try:
    parametres = st.query_parameters
    if "mat_id" in parametres:
        id_scanne = int(parametres["mat_id"])
except Exception:
    pass

st.title("🛠️ SOC Industrie : Logistique, Matériel & Visuels")

# --- INTERACTION QR CODE ---
if id_scanne and not df_mat.empty:
    mat_scanne = df_mat[df_mat['id'] == id_scanne]
    if not mat_scanne.empty:
        row_mat = mat_scanne.iloc[0]
        st.warning(f"📱 **QR Code Flashé** : **{row_mat['nom']}** ({row_mat['modele']})")
        afficher_image_securisee(row_mat['photo_data'], width=200)
        
        res_attente = conn.query("SELECT * FROM mouvements WHERE %s = :mat_id AND statut_mouvement='Réservé' ORDER BY date_debut ASC LIMIT 1;" % "materiel_id", params={"mat_id": id_scanne}, ttl=0)
        
        if row_mat['statut'] == "A l'agence" and not res_attente.empty:
            res = res_attente.iloc[0]
            st.info(f"👉 Réservation pour : **{res['technicien']}** (Affaire : {res['num_affaire']})")
            if st.button("✅ Valider mon Retrait de l'Agence"):
                with conn.session as session:
                    session.execute("UPDATE materiel SET statut='En Chantier' WHERE id = :id_scanne", {"id_scanne": id_scanne})
                    session.execute("UPDATE mouvements SET statut_mouvement='Sorti (En Cours)', date_retrait_reel = :date WHERE id = :res_id", {"date": date.today().strftime('%Y-%m-%d'), "res_id": int(res['id'])})
                    session.commit()
                st.success("Sortie validée ! Bon chantier.")
                st.rerun()
                
        elif row_mat['statut'] == "En Chantier":
            if st.button("🏢 Valider le Retour définitif à l'Agence"):
                with conn.session as session:
                    session.execute("UPDATE materiel SET statut='A l''agence' WHERE id = :id_scanne", {"id_scanne": id_scanne})
                    session.execute("UPDATE mouvements SET statut_mouvement='Retourné', date_retour_reel = :date WHERE materiel_id = :id_scanne AND statut_mouvement='Sorti (En Cours)'", {"date": date.today().strftime('%Y-%m-%d'), "id_scanne": id_scanne})
                    session.commit()
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
        for idx, row in df_mat.reset_index(drop=True).iterrows():
            with cols_m[idx % 4]:
                afficher_image_securisee(row['photo_data'], width=140)
                st.markdown(f"**{row['nom']}** ({row['modele']})")
                st.caption(f"S/N: {row['num_serie']} | Statut: `{row['statut']}`")
                st.write("---")
    else:
        st.info("Aucune machine enregistrée.")

# --- TAB 2 : PLANIFIER UNE RÉSERVATION ---
with tab2:
    st.subheader("🗓️ Enregistrer un nouveau mouvement")
    if df_mat.empty: 
        st.info("Aucune machine disponible.")
    else:
        with st.form("form_res"):
            mat_id = st.selectbox("Sélectionner le matériel concerné", df_mat['id'].tolist(), format_func=lambda x: f"ID {x} : {df_mat[df_mat['id']==x]['nom'].values[0]} (S/N: {df_mat[df_mat['id']==x]['num_serie'].values[0]})")
            tech = st.text_input("Technicien / Détenteur du matériel")
            n_affaire = st.text_input("N° d'Affaire")
            adresse = st.text_area("Lieu du chantier (Adresse précise pour la carte)", value=ADRESSE_SIEGE)
            d_deb = st.date_input("Date de début de réservation", date.today())
            d_fi = st.date_input("Date de fin prévue", date.today() + timedelta(days=7))
            
            if st.form_submit_button("🔥 Valider l'affectation et le mouvement"):
                with conn.session as session:
                    session.execute("""
                        INSERT INTO mouvements (materiel_id, technicien, num_affaire, adresse_chantier, lat, lon, date_demande, date_debut, date_fin, statut_mouvement) 
                        VALUES (:mat_id, :tech, :n_affaire, :adresse, :lat, :lon, :date_demande, :date_debut, :date_fin, 'Réservé')
                    """, {
                        "mat_id": mat_id, "tech": tech, "n_affaire": n_affaire, "adresse": adresse,
                        "lat": COORD_SIEGE[0], "lon": COORD_SIEGE[1], "date_demande": date.today().strftime('%Y-%m-%d'),
                        "date_debut": str(d_deb), "date_fin": str(d_fi)
                    })
                    session.commit()
                st.success("Mouvement enregistré avec succès ! La carte et le tableau sont à jour.")
                st.rerun()

# --- TAB 3 : STOCKS CONSOMMABLES ---
with tab3:
    st.subheader("📦 Stock Consommables Atelier")
    df_conso = df_stock_total[df_stock_total['type_article'] == 'Consommable'] if not df_stock_total.empty else pd.DataFrame()
    
    if not df_conso.empty:
        c_index = st.columns(4)
        for idx, row in df_conso.reset_index(drop=True).iterrows():
            with c_index[idx % 4]:
                afficher_image_securisee(row['photo_data'], width=120)
                st.markdown(f"**{row['nom']}**")
                
                # Récupération et affichage des variantes pour cet article
                vars_art = df_variantes_toutes[df_variantes_toutes['article_id'] == row['id']]
                
                qte_actuelle = int(row['quantite'])
                seuil_critique = int(row['seuil_mini']) if row['seuil_mini'] is not None else 5
                
                if qte_actuelle <= 0:
                    st.error(f"🚨 RUPTURE DE STOCK GÉNÉRALE : **{qte_actuelle}**")
                elif qte_actuelle <= seuil_critique:
                    st.warning(f"⚠️ Stock Total Critique : **{qte_actuelle}** (Seuil: {seuil_critique})")
                else:
                    st.success(f"✅ Stock Total OK : **{qte_actuelle}**")
                
                # Petit affichage propre des déclinaisons sous le statut
                if not vars_art.empty:
                    texte_variantes = " / ".join([f"`{r['caracteristique']}`: **{r['quantite']}**" for _, r in vars_art.iterrows()])
                    st.markdown(f"📊 **Détail :** {texte_variantes}")
                else:
                    st.caption("ℹ️ Aucune taille/dimension configurée.")
                    
                st.caption(f"Marque: {row['marque']} | Réf: {row['reference']}")
                st.write("---")
        
        st.write("### 🛠️ Déclarer un retrait de consommable")
        with st.form("form_sort_c"):
            art_id = st.selectbox("Article prélevé", df_conso['id'].tolist(), format_func=lambda x: f"{df_conso[df_conso['id']==x]['nom'].values[0]} (En stock global : {df_conso[df_conso['id']==x]['quantite'].values[0]})")
            
            # Sélectionner dynamiquement la variante disponible pour cet article
            df_v_dispos = df_variantes_toutes[df_variantes_toutes['article_id'] == art_id]
            if not df_v_dispos.empty:
                var_id = st.selectbox("Dimension / Caractéristique disponible", df_v_dispos['id'].tolist(), format_func=lambda x: f"{df_v_dispos[df_v_dispos['id']==x]['caracteristique'].values[0]} (Dispo: {df_v_dispos[df_v_dispos['id']==x]['quantite'].values[0]})")
            else:
                var_id = None
                st.error("⚠️ Cet article n'a pas de caractéristiques/tailles enregistrées en base. Créez-en une en Administration.")
                
            t_nom = st.text_input("Nom du Technicien")
            a_nom = st.text_input("N° d'affaire")
            q_s = st.number_input("Quantité retirée", min_value=1, value=1)
            
            if st.form_submit_button("Déclarer la sortie") and var_id:
                with conn.session as session:
                    # 1. Prélèvement sur la variante
                    session.execute("UPDATE variantes_stock SET quantite = quantite - :q_s WHERE id = :var_id", {"q_s": q_s, "var_id": var_id})
                    
                    # Récupération du nom de la caractéristique pour l'historique
                    carac_nom = df_v_dispos[df_v_dispos['id'] == var_id]['caracteristique'].values[0]
                    
                    # 2. Enregistrement dans l'historique
                    session.execute("""
                        INSERT INTO sorties_stocks (article_id, variante_id, technicien, num_affaire, quantite_sortie, caracteristique, date_sortie) 
                        VALUES (:art_id, :var_id, :t_nom, :a_nom, :q_s, :carac_nom, :date)
                    """, {"art_id": art_id, "var_id": var_id, "t_nom": t_nom, "a_nom": a_nom, "q_s": q_s, "carac_nom": carac_nom, "date": datetime.now().strftime('%Y-%m-%d %H:%M')})
                    session.commit()
                
                # 3. Recalcul automatique du total
                recalculer_total_stock(art_id)
                
                st.success("Prélèvement enregistré !")
                st.session_state["derniere_sortie_id"] = art_id
                st.rerun()

    # --- ALERTE MAIL AUTOMATIQUE SI SEUIL MINI ATTEINT ---
    if "derniere_sortie_id" in st.session_state:
        id_verif = st.session_state["derniere_sortie_id"]
        art_verif = conn.query("SELECT * FROM stocks WHERE id = :id_verif;", params={"id_verif": id_verif}, ttl=0)
        if not art_verif.empty:
            row_v = art_verif.iloc[0]
            if int(row_v['quantite']) <= int(row_v['seuil_mini']):
                st.error(f"🛑 Attention ! Le stock global de **{row_v['nom']}** est descendu à **{row_v['quantite']}** (Seuil mini : {row_v['seuil_mini']}).")
                sujet_alerte = f"[ALERTE REAPPRO] Stock critique : {row_v['nom']}"
                corps_alerte = f"Bonjour Olivier,\n\nLe consommable suivant a atteint son seuil d'alerte à l'atelier :\n• Article : {row_v['nom']}\n• Référence : {row_v['reference']}\n• Stock restant : {row_v['quantite']} (Seuil d'alerte : {row_v['seuil_mini']})\n\nMerci de prévoir un réapprovisionnement."
                st.markdown(f'<a href="{generer_lien_mail(sujet_alerte, corps_alerte)}" target="_blank" style="display:inline-block; padding:12px; background-color:#FF4B4B; color:white; border-radius:5px; text-decoration:none; font-weight:bold;">📧 Envoyer l\'alerte réappro à Olivier</a>', unsafe_allow_html=True)

    # --- AFFICHAGE HISTORIQUE DES SORTIES ---
    st.write("---")
    st.write("### 📜 Historique complet des sorties (Consommables & EPI)")
    df_historique = conn.query("""
        SELECT s.date_sortie as "Date", st.type_article as "Type", st.nom as "Désignation", 
               s.caracteristique as "Taille / Dim", s.quantite_sortie as "Quantité", 
               s.technicien as "Technicien", s.num_affaire as "N° Affaire"
        FROM sorties_stocks s
        JOIN stocks st ON s.article_id = st.id
        ORDER BY s.id DESC
    """, ttl=0)
    
    if not df_historique.empty:
        st.dataframe(df_historique, use_container_width=True)
    else:
        st.info("Aucun historique de sortie enregistré pour le moment.")

# --- TAB 4 : EPI ---
with tab4:
    st.subheader("🦺 Équipements de Sécurité (EPI)")
    df_epi = df_stock_total[df_stock_total['type_article'] == 'EPI'] if not df_stock_total.empty else pd.DataFrame()
    
    if not df_epi.empty:
        c_epi = st.columns(4)
        for idx, row in df_epi.reset_index(drop=True).iterrows():
            with c_epi[idx % 4]:
                afficher_image_securisee(row['photo_data'], width=120)
                st.markdown(f"**{row['nom']}**")
                
                # Récupération et affichage des variantes pour cet EPI
                vars_epi = df_variantes_toutes[df_variantes_toutes['article_id'] == row['id']]
                
                qte_actuelle_epi = int(row['quantite'])
                seuil_critique_epi = int(row['seuil_mini']) if row['seuil_mini'] is not None else 5
                
                if qte_actuelle_epi <= 0:
                    st.error(f"🚨 RUPTURE GÉNÉRALE : **{qte_actuelle_epi}**")
                elif qte_actuelle_epi <= seuil_critique_epi:
                    st.warning(f"⚠️ Stock Total Faible : **{qte_actuelle_epi}** (Mini: {seuil_critique_epi})")
                else:
                    st.success(f"✅ En stock Total : **{qte_actuelle_epi}**")
                
                if not vars_epi.empty:
                    texte_vars_epi = " / ".join([f"`{r['caracteristique']}`: **{r['quantite']}**" for _, r in vars_epi.iterrows()])
                    st.markdown(f"📏 **Tailles :** {texte_vars_epi}")
                else:
                    st.caption("ℹ️ Aucune taille configurée.")
                    
                st.caption(f"Marque: {row['marque']} | Réf: {row['reference']}")
                st.write("---")
        
        st.markdown("### 📢 Formulaire de demande de dotation (Mail Olivier)")
        with st.form("f_epi"):
            col_epi1, col_epi2 = st.columns(2)
            with col_epi1:
                epi_id = st.selectbox("EPI demandé", df_epi['id'].tolist(), format_func=lambda x: df_epi[df_epi['id']==x]['nom'].values[0])
                
                df_v_epi = df_variantes_toutes[df_variantes_toutes['article_id'] == epi_id]
                if not df_v_epi.empty:
                    var_epi_id = st.selectbox("Taille / Pointure disponible à l'atelier", df_v_epi['id'].tolist(), format_func=lambda x: f"Taille {df_v_epi[df_v_epi['id']==x]['caracteristique'].values[0]} (Restant: {df_v_epi[df_v_epi['id']==x]['quantite'].values[0]})")
                else:
                    var_epi_id = None
                    st.error("⚠️ Aucune taille configurée en base pour cet EPI.")
                    
                sal = st.text_input("Salarié demandeur / Technicien")
                motif = st.text_input("Affaire de destination / Motif")
            with col_epi2:
                qte_demandee = st.number_input("Quantité souhaitée", min_value=1, value=1, step=1)
                valider_sortie_epi_direct = st.checkbox("Déduire directement du stock disponible à l'atelier")
            
            if st.form_submit_button("📩 Préparer le Mail pour Olivier") and var_epi_id:
                n_epi = df_epi[df_epi['id']==epi_id]['nom'].values[0]
                ref_epi = df_epi[df_epi['id']==epi_id]['reference'].values[0]
                taille_selectionnee = df_v_epi[df_v_epi['id']==var_epi_id]['caracteristique'].values[0]
                
                if valider_sortie_epi_direct:
                    with conn.session as session:
                        session.execute("UPDATE variantes_stock SET quantite = quantite - :qte WHERE id = :var_id", {"qte": qte_demandee, "var_id": var_epi_id})
                        session.execute("""
                            INSERT INTO sorties_stocks (article_id, variante_id, technicien, num_affaire, quantite_sortie, caracteristique, date_sortie) 
                            VALUES (:epi_id, :var_id, :sal, :motif, :qte, :taille, :date)
                        """, {"epi_id": epi_id, "var_id": var_epi_id, "sal": sal, "motif": motif, "qte": qte_demandee, "taille": taille_selectionnee, "date": datetime.now().strftime('%Y-%m-%d %H:%M')})
                        session.commit()
                    recalculer_total_stock(epi_id)
                
                s_mail = f"[EPI] Demande de matériel - {sal}"
                c_mail = (
                    f"Bonjour Olivier,\n\n"
                    f"Une nouvelle demande d'Équipement de Protection Individuelle vient d'être complétée :\n\n"
                    f"• Salarié : {sal}\n"
                    f"• Équipement : {n_epi} (Réf : {ref_epi})\n"
                    f"• Quantité demandée : {qte_demandee}\n"
                    f"• Taille / Pointure choisie : {taille_selectionnee}\n"
                    f"• Motif / N° Affaire : {motif}\n\n"
                    f"Merci d'avance.\nCordialement."
                )
                st.markdown(f'<a href="{generer_lien_mail(s_mail, c_mail)}" target="_blank" style="display: inline-block; padding: 12px 24px; background-color: #2e7d32; color: white; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">🚀 Cliquer ici pour Envoyer le mail à owasse@soc.fr</a>', unsafe_allow_html=True)
                if valider_sortie_epi_direct:
                    st.rerun()

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

# --- TAB 6 : ADMINISTRATION ---
with tab6:
    st.subheader("⚙️ Panneau d'Administration")
    subtab_creer, subtab_variantes, subtab_modifier = st.tabs([
        "➕ Créer des Articles / Machines", "📏 Gérer les Tailles & Dimensions", "✏️ Modifier ou Supprimer un Article"
    ])
    
    with subtab_creer:
        st.write("### ➕ Ajouter une Machine")
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
                with conn.session as session:
                    session.execute("INSERT INTO materiel (nom, modele, num_serie, statut, photo_data) VALUES (:nom, :modele, :num_serie, 'A l''agence', :photo)", 
                                    {"nom": n, "modele": m, "num_serie": s, "photo": p_base64})
                    session.commit()
                st.success("Machine ajoutée au parc !")
                st.rerun()
                    
        st.write("---")
        st.write("### ➕ Ajouter un Nouveau Modèle d'Article (Consommable / EPI)")
        st.info("💡 Étape 1 : Créez la fiche de l'article ici. Étape 2 : Allez dans l'onglet 'Gérer les Tailles' pour lui attribuer ses stocks spécifiques.")
        with st.form("f_add_s"):
            c3, c4 = st.columns(2)
            with c3:
                n_s = st.text_input("Désignation")
                t_s = st.selectbox("Type", ["Consommable", "EPI"])
                m_s = st.text_input("Marque")
                r_s = st.text_input("Référence")
                f_s = st.text_input("Fournisseur")
                s_mini = st.number_input("Seuil Minimal d'alerte global", min_value=0, value=5)
            with c4:
                fichier_photo_s = st.file_uploader("📸 Capture écran ou Photo (JPG/PNG) - Article", type=["jpg", "jpeg", "png"], key="add_s_photo")
                
            if st.form_submit_button("Enregistrer l'Article"):
                p_base64_s = convertir_image_en_base64(fichier_photo_s)
                with conn.session as session:
                    session.execute("""
                        INSERT INTO stocks (nom, marque, reference, fournisseur, quantite, seuil_mini, seuil_maxi, type_article, photo_data) 
                        VALUES (:nom, :marque, :ref, :fourn, 0, :seuil, 100, :type_art, :photo)
                    """, {"nom": n_s, "marque": m_s, "ref": r_s, "fourn": f_s, "seuil": s_mini, "type_art": t_s, "photo": p_base64_s})
                    session.commit()
                st.success("Modèle d'article créé ! Pensez à lui ajouter ses tailles/dimensions dans le second onglet.")
                st.rerun()

    with subtab_variantes:
        st.write("### 📏 Gestion des Variantes (Tailles, Pointures, Dimensions)")
        if df_stock_total.empty:
            st.info("Créez d'abord un article pour lui attribuer des déclinaisons.")
        else:
            art_sel_id = st.selectbox(
                "Sélectionner l'article à configurer ou réapprovisionner",
                options=df_stock_total['id'].tolist(),
                format_func=lambda x: f"[{df_stock_total[df_stock_total['id']==x]['type_article'].values[0]}] {df_stock_total[df_stock_total['id']==x]['nom'].values[0]}"
            )
            
            df_existantes = df_variantes_toutes[df_variantes_toutes['article_id'] == art_sel_id]
            if not df_existantes.empty:
                st.write("**Variantes existantes pour cet article :**")
                st.dataframe(df_existantes[['id', 'caracteristique', 'quantite']], use_container_width=True, hide_index=True)
            
            st.write("#### ➕ Ajouter ou Modifier le stock d'une variante")
            with st.form("form_gestion_variante"):
                carac_input = st.text_input("Taille ou Dimension (ex: M, XL, 8x70, 10x100)", placeholder="Ex: XL")
                qte_input = st.number_input("Quantité en stock pour cette variante", min_value=0, value=10)
                
                if st.form_submit_button("💾 Enregistrer la variante"):
                    carac_input = carac_input.strip()
                    if carac_input == "":
                        st.error("La taille/dimension ne peut pas être vide.")
                    else:
                        with conn.session as session:
                            existe = session.execute("SELECT id FROM variantes_stock WHERE article_id = :art_id AND caracteristique = :carac", {"art_id": art_sel_id, "carac": carac_input}).fetchone()
                            
                            if existe:
                                session.execute("UPDATE variantes_stock SET quantite = :qte WHERE id = :id_var", {"qte": qte_input, "id_var": existe[0]})
                                st.success(f"Mise à jour de la taille `{carac_input}` enregistrée.")
                            else:
                                session.execute("INSERT INTO variantes_stock (article_id, caracteristique, quantite) VALUES (:art_id, :carac, :qte)", {"art_id": art_sel_id, "carac": carac_input, "qte": qte_input})
                                st.success(f"Nouvelle variante `{carac_input}` ajoutée avec succès.")
                            session.commit()
                        
                        recalculer_total_stock(art_sel_id)
                        st.rerun()

    with subtab_modifier:
        st.write("### ✏️ Éditer la Fiche Générale d'un Article")
        if df_stock_total.empty:
            st.info("Aucun article en stock à modifier.")
        else:
            id_article_choisi = st.selectbox(
                "Sélectionner l'article à modifier ou à supprimer",
                options=df_stock_total['id'].tolist(),
                key="sb_edit_art",
                format_func=lambda x: f"[{df_stock_total[df_stock_total['id']==x]['type_article'].values[0]}] {df_stock_total[df_stock_total['id']==x]['nom'].values[0]}"
            )
            
            art_actuel = df_stock_total[df_stock_total['id'] == id_article_choisi].iloc[0]
            
            with st.form("form_modification_article"):
                col_mod1, col_mod2 = st.columns(2)
                with col_mod1:
                    edit_nom = st.text_input("Désignation de l'article", value=art_actuel['nom'])
                    edit_type = st.selectbox("Catégorie", ["Consommable", "EPI"], index=0 if art_actuel['type_article'] == "Consommable" else 1)
                    edit_marque = st.text_input("Marque", value=art_actuel['marque'])
                    edit_ref = st.text_input("Référence", value=art_actuel['reference'])
                with col_mod2:
                    edit_fourn = st.text_input("Fournisseur", value=art_actuel['fournisseur'])
                    st.info(f"📈 Stock total actuel (calculé) : **{art_actuel['quantite']}** unités.")
                    edit_seuil = st.number_input("Modifier le Seuil Minimal Global", min_value=0, value=int(art_actuel['seuil_mini'] if art_actuel['seuil_mini'] is not None else 5))
                    fichier_photo_edit = st.file_uploader("Remplacer la photo", type=["jpg", "jpeg", "png"], key="edit_photo")
                
                btn_col1, btn_col2 = st.columns([1, 4])
                with btn_col1:
                    sauvegarder_changement = st.form_submit_button("💾 Enregistrer les infos")
                with btn_col2:
                    supprimer_definitivement = st.form_submit_button("🗑️ Supprimer l'article et ses tailles")

            if sauvegarder_changement:
                nouveau_b64 = convertir_image_en_base64(fichier_photo_edit) if fichier_photo_edit is not None else art_actuel['photo_data']
                with conn.session as session:
                    session.execute("""
                        UPDATE stocks SET nom = :nom, type_article = :type_art, marque = :marque, reference = :ref, fournisseur = :fourn, seuil_mini = :seuil, photo_data = :photo 
                        WHERE id = :id_art
                    """, {"nom": edit_nom, "type_art": edit_type, "marque": edit_marque, "ref": edit_ref, "fourn": edit_fourn, "seuil": edit_seuil, "photo": nouveau_b64, "id_art": id_article_choisi})
                    session.commit()
                st.success("Fiche article mise à jour avec succès !")
                st.rerun()
                
            if supprimer_definitivement:
                with conn.session as session:
                    session.execute("DELETE FROM stocks WHERE id = :id_art", {"id_art": id_article_choisi})
                    session.execute("DELETE FROM variantes_stock WHERE article_id = :id_art", {"id_art": id_article_choisi})
                    session.commit()
                st.warning("Article et toutes ses déclinaisons supprimés.")
                st.rerun()
