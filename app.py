import streamlit as st
import pandas as pd
import sqlalchemy
from datetime import datetime # Correction pour l'erreur datetime

st.set_page_config(page_title="SOC Industrie", layout="wide")

# --- DÉFINITIONS GLOBALES ---
CATALOGUE_MAGASIN = [...] 
CATALOGUE_OUTILLAGE = [...]
CATALOGUE_TOTAL = CATALOGUE_MAGASIN + CATALOGUE_OUTILLAGE

# --- CONNEXION ---
@st.cache_resource
def init_connection():
    return sqlalchemy.create_engine(st.secrets["DB_URL"])
engine = init_connection()

# --- DÉBUT DES ONGLETS ---
tab0, tab1, tab2, tab3, tab4 = st.tabs([...])

try:
    engine = init_connection()
    with engine.connect() as conn:
        pass
except Exception as e:
    st.error(f"Erreur de connexion à la base de données : {e}")
    st.stop()

# 3. RECUPERATION DES DONNEES REELLES (SUPABASE)
def charger_materiel():
    query = """
        SELECT id AS "ID", nom AS "Nom", categorie AS "Catégorie", statut AS "Statut", 
               detenteur AS "Détenteur", date_controle AS "Date Contrôle", 
               intervalle_mois AS "Intervalle (mois)", prochain_controle AS "Prochain Contrôle",
               photo_base64 AS "Photo", 
               marque AS "Marque", reference AS "Référence", num_serie AS "N° de Série"
        FROM materiel;
    """
    return pd.read_sql(query, engine)

def charger_demandes():
    query = "SELECT date_demande AS \"Date\", collaborateur AS \"Collaborateur\", type_demande AS \"Type\", designation AS \"Désignation\", code_imputation AS \"Code Imputation\", details AS \"Détails / Dates\", statut AS \"Statut\" FROM demandes_collaborateurs;"
    return pd.read_sql(query, engine)

df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

if 'panier' not in st.session_state:
    st.session_state.panier = []

PHOTOS_SECOURS = {
    "Soudage": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=300&q=80",
    "Outillage Électroportatif": "https://images.unsplash.com/photo-1534224039826-c7a0dea0e66a?w=300&q=80",
    "Mesure": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=300&q=80",
    "Manutention": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=300&q=80"
}

CATALOGUE = [
    {"id": "EPI-01", "type": "🦺 EPI", "nom": "Gants de soudure Haute Protection", "marque": "Singer Safety", "ref": "TIG-500", "tailles": ["M (8)", "L (9)", "XL (10)", "XXL (11)"], "photo": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=150&q=80", "desc": "Cuir de chèvre supérieur, coutures Kevlar. Idéal pour soudure TIG/MIG."},
    {"id": "EPI-02", "type": "🦺 EPI", "nom": "Chaussures de Sécurité S3 Basse", "marque": "Caterpillar", "ref": "CAT-LITE", "tailles": ["41", "42", "43", "44", "45"], "photo": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=150&q=80", "desc": "Coque composite sans métal, semelle anti-perforation, imperméable."},
    {"id": "CON-01", "type": "🪵 Consommable", "nom": "Électrodes de Soudage Inox Ø2.5", "marque": "Gys", "ref": "E308L-16", "tailles": ["Étui de 50 pièces", "Blister de 10 pièces"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150&q=80", "desc": "Électrodes enrobées rutiles pour le soudage des aciers inoxydables."},
    {"id": "CON-02", "type": "🪵 Consommable", "nom": "Disque à tronçonner Acier/Inox Ø125", "marque": "Norton Abrasifs", "ref": "NOR-125-1", "tailles": ["Lot de 5 disques", "Boîte de 25 disques"], "photo": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=150&q=80", "desc": "Épaisseur 1mm pour une coupe ultra-rapide et précise sans bavure."}
]
CATALOGUE_OUTILLAGE = [
    {"id": "OUT-01", "type": "🛠️ Outillage", "nom": "Perceuse à percussion Bosch", "marque": "Bosch", "ref": "GBH 2-28", "tailles": ["Nue"], "photo": "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=150", "desc": "Puissante, pour béton et métal."},
    {"id": "OUT-02", "type": "🛠️ Outillage", "nom": "Meuleuse d'angle Ø125", "marque": "Makita", "ref": "GA5030", "tailles": ["Nue"], "photo": "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=150", "desc": "Compacte et maniable."},
]

tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "👑 ESPACE OLIVIER : Centralisation & Logistique",
    "🛒 CATALOGUE MAGASIN (EPI / Consommables)",
    "🛠️ CATALOGUE VISUEL & REGISTRE MATÉRIEL", 
    "📅 Sorties & Mouvements Terrain", 
    "📍 Carte des Chantiers"
])

# ==========================================
# ONGLET 0 & 1 : LOGISTIQUE ET MAGASIN
# ==========================================
with tab0:
    st.header("👑 Tableau de Bord Logistique d'Olivier")
    if not df_demandes_reel.empty:
        st.dataframe(df_demandes_reel, use_container_width=True, hide_index=True)
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            demande_a_traiter = st.selectbox("Sélectionner une ligne à archiver / traiter :", df_demandes_reel["Collaborateur"] + " - " + df_demandes_reel["Désignation"], key="sel_olivier")
        with col_v2:
            action_decision = st.radio("Action :", ["Laisser en attente", "Valider / Matériel Prêt", "Supprimer / Archiver la ligne"], horizontal=True, key="rad_olivier")
        if st.button("Confirmer l'action sur la demande", key="btn_olivier"):
            collab_sel = demande_a_traiter.split(" - ")[0]
            desig_sel = demande_a_traiter.split(" - ")[1]
            with engine.begin() as conn_tx:
                if action_decision == "Supprimer / Archiver la ligne":
                    conn_tx.execute(sqlalchemy.text("DELETE FROM demandes_collaborateurs WHERE collaborateur = :c AND designation = :d;"), {"c": collab_sel, "d": desig_sel})
                elif action_decision != "Laisser en attente":
                    conn_tx.execute(sqlalchemy.text("UPDATE demandes_collaborateurs SET statut = :s WHERE collaborateur = :c AND designation = :d;"), {"s": action_decision, "c": collab_sel, "d": desig_sel})
            st.rerun()
    else: st.success("✅ Aucune commande ou réservation en attente.")

    st.markdown("---")
    st.subheader("🚨 Alertes Étalonnages (< 90 jours)")
    aujourdhui = datetime.now().date()
    lignes_alertes = []
    for idx, row in df_materiel_reel.iterrows():
        date_prox = row["Prochain Contrôle"]
        if isinstance(date_prox, str): date_prox = datetime.strptime(date_prox, "%Y-%m-%d").date()
        elif isinstance(date_prox, datetime): date_prox = date_prox.date()
        if (date_prox - aujourdhui).days <= 90:
            lignes_alertes.append({"Urgence": "🔴 RETARD" if (date_prox - aujourdhui).days < 0 else "🟡 Échéance proche", "ID": row["ID"], "Matériel": row["Nom"], "Détenteur": row["Détenteur"], "Prochain Contrôle": date_prox})
    if lignes_alertes: st.dataframe(pd.DataFrame(lignes_alertes), use_container_width=True, hide_index=True)
    else: st.success("✅ Aucun étalonnage critique à prévoir.")

with tab1:
    st.header("🛒 Catalogue Magasin & Outillage SOC Industrie")
    col_cat, col_panier = st.columns([3, 2])
    
    with col_cat:
        # Ajout de "🛠️ Outillage" dans les options de filtre
        filtre_type = st.radio("Filtrer par type :", ["Tous", "🦺 EPI", "🪵 Consommable", "🛠️ Outillage"], horizontal=True)
        
        # On utilise CATALOGUE_TOTAL
        for prod in CATALOGUE_TOTAL:
            if filtre_type != "Tous" and prod["type"] != filtre_type: 
                continue
            with st.container(border=True):
                c_img, c_txt, c_form = st.columns([1, 2, 1.5])
                with c_img: st.image(prod["photo"], width=100)
                with c_txt:
                    st.markdown(f"### {prod['nom']}")
                    st.caption(f"**Marque :** {prod['marque']} | **Ref :** {prod['ref']}\n\n{prod['desc']}")
                with c_form:
                    t_choisie = st.selectbox("Option / Taille", prod["tailles"], key=f"t_{prod['id']}")
                    q_choisie = st.number_input("Quantité", min_value=1, value=1, key=f"q_{prod['id']}")
                    if st.button("➕ Ajouter", key=f"b_{prod['id']}", use_container_width=True):
                        st.session_state.panier.append({"type": prod["type"], "designation": f"{prod['nom']} ({prod['marque']})", "taille": t_choisie, "qte": q_choisie})
                        st.rerun()
    with col_panier:
        st.subheader("🛒 Mon Panier")
        if not st.session_state.panier: st.info("Panier vide.")
        else:
            st.dataframe(pd.DataFrame(st.session_state.panier), use_container_width=True, hide_index=True)
            if st.button("🗑️ Vider", use_container_width=True):
                st.session_state.panier = []
                st.rerun()
            st.markdown("---")
            with st.form("form_panier"):
                nom_c = st.text_input("Votre Nom")
                code_i = st.text_input("Code Imputation Obligatoire")
                if st.form_submit_button("🚀 Envoyer la commande", use_container_width=True):
                    if nom_c.strip() and code_i.strip():
                        with engine.begin() as conn_tx:
                            for art in st.session_state.panier:
                                conn_tx.execute(sqlalchemy.text("INSERT INTO demandes_collaborateurs (date_demande, collaborateur, type_demande, designation, code_imputation, details, statut) VALUES (:dt, :col, :ty, :des, :cod, :det, 'En attente');"),
                                                {"dt": datetime.now().strftime("%d/%m/%Y"), "col": nom_c.strip(), "ty": art["type"], "des": art["designation"], "cod": code_i.upper().strip(), "det": f"Option: {art['taille']} | Qté: {art['qte']}"})
                        st.session_state.panier = []
                        st.success("Commande transmise à Olivier !")
                        st.rerun()
                    else: st.error("Champs obligatoires manquants.")

# ==========================================
# ONGLET 2 : CATALOGUE VISUEL & REGISTRE
# ==========================================
with tab2:
    st.header("🛠️ Catalogue Commun du Parc Matériel")
    recherche = st.text_input("🔍 Rechercher un matériel (ex: Meuleuse, TIG, Bosch, N° Série...)", "").strip().lower()

    st.subheader("📦 Fiches Équipements & Disponibilités")
    df_filtre = df_materiel_reel.copy()
    if recherche:
        df_filtre = df_filtre[
            df_filtre["Nom"].str.lower().str.contains(recherche) | 
            df_filtre["ID"].str.lower().str.contains(recherche) |
            df_filtre["Marque"].fillna("").str.lower().str.contains(recherche) |
            df_filtre["Référence"].fillna("").str.lower().str.contains(recherche) |
            df_filtre["N° de Série"].fillna("").str.lower().str.contains(recherche)
        ]

    if df_filtre.empty:
        st.info("Aucun matériel trouvé.")
    else:
        cols_grid = st.columns(3)
        for idx, row in df_filtre.iterrows():
            col_case = cols_grid[idx % 3]
            with col_case:
                with st.container(border=True):
                    if row["Photo"] is not None and str(row["Photo"]).strip() != "":
                        try:
                            bytes_image = base64.b64decode(row["Photo"])
                            st.image(bytes_image, use_container_width=True)
                        except Exception:
                            st.image(PHOTOS_SECOURS.get(row["Catégorie"], PHOTOS_SECOURS["Outillage Électroportatif"]), use_container_width=True)
                    else:
                        st.image(PHOTOS_SECOURS.get(row["Catégorie"], PHOTOS_SECOURS["Outillage Électroportatif"]), use_container_width=True)
                    
                    st.markdown(f"### {row['Nom']}")
                    st.markdown(f"**Code Unique :** `{row['ID']}`")
                    
                    m_aff = row["Marque"] if pd.notna(row["Marque"]) and row["Marque"] else "Non renseignée"
                    r_aff = row["Référence"] if pd.notna(row["Référence"]) and row["Référence"] else "Non renseignée"
                    s_aff = row["N° de Série"] if pd.notna(row["N° de Série"]) and row["N° de Série"] else "Non renseigné"
                    
                    st.markdown(f"**🔧 Constructeur :** {m_aff} | **Ref :** `{r_aff}`")
                    st.markdown(f"**🔢 N° Série :** `{s_aff}`")
                    
                    statut = row["Statut"]
                    if statut == "Disponible": st.success(f"📍 {statut} (Stock Atelier)")
                    elif statut == "En Chantier": st.warning(f"🏗️ {statut} chez **{row['Détenteur']}**")
                    else: st.info(f"🔄 {statut} — {row['Détenteur']}")
                        
                    st.caption(f"📅 Prochain contrôle obligatoire : {row['Prochain Contrôle']}")
                    
                    texte_qr = f"SOC Industrie\nID: {row['ID']}\nNom: {row['Nom']}\nMarque: {m_aff}\nSérie: {s_aff}\nStatut: {statut}"
                    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(texte_qr)}"
                    with st.expander("📱 Afficher le QR Code de l'appareil"):
                        st.image(qr_api_url, caption="À coller sur l'appareil", width=130)

                    with st.expander("📅 Faire une demande de réservation"):
                        with st.form(key=f"reserve_{row['ID']}"):
                            nom_d = st.text_input("Votre Prénom/Nom", key=f"u_{row['ID']}")
                            code_imp = st.text_input("Code Imputation", key=f"i_{row['ID']}")
                            if st.form_submit_button("Valider"):
                                if nom_d.strip() and code_imp.strip():
                                    with engine.begin() as conn_tx:
                                        conn_tx.execute(sqlalchemy.text("INSERT INTO demandes_collaborateurs (date_demande, collaborateur, type_demande, designation, code_imputation, details, statut) VALUES (:dt, :col, '⚙️ Réservation', :des, :cod, :det, 'En attente');"),
                                                        {"dt": datetime.now().strftime("%d/%m/%Y"), "col": nom_d.strip(), "des": f"Réservation {row['Nom']} [{row['ID']}]", "cod": code_imp.upper().strip(), "det": f"Marque: {m_aff} | SN: {s_aff}"})
                                    st.success("Demande envoyée !")
                                    st.rerun()


# ========================================================
    # ⚙️ PANNEAU UNIQUE : CRÉER / MODIFIER / SUPPRIMER
    # ========================================================
    st.markdown("---")
    st.subheader("⚙️ Administration Unique du Parc Matériel")
    
    action_choisie = st.radio(
        "Quelle action souhaitez-vous réaliser ?",
        ["➕ Enregistrer un nouveau matériel", "✏️ Modifier un matériel existant", "🗑️ Supprimer un matériel du parc"],
        horizontal=True
    )
    
    # Rétablissement des catégories originales
    # (Sans la catégorie "🛠️ Outillage" ajoutée tout à l'heure)
    CATEGORIES_ORIGINALES = ["Outillage Électroportatif", "Manutention", "Soudage", "Mesure"]
    
    # ... (le reste du code doit utiliser CATEGORIES_ORIGINALES dans le st.selectbox)
    
    # Initialisation des variables par défaut
    val_id = ""
    val_nom = ""
    val_cat = "Outillage Électroportatif"
    val_marque = ""
    val_ref = ""
    val_serie = ""
    val_intervalle = 12
    val_date = aujourdhui
    desactiver_id = False
    
    # Logique d'affichage si Modification ou Suppression
    if action_choisie in ["✏️ Modifier un matériel existant", "🗑️ Supprimer un matériel du parc"]:
        if df_materiel_reel.empty:
            st.warning("Aucun matériel enregistré dans la base de données.")
            st.stop()
        else:
            liste_choix = df_materiel_reel["ID"] + " - " + df_materiel_reel["Nom"]
            mat_selectionne = st.selectbox("Sélectionnez l'équipement cible :", liste_choix, key="select_unique_admin")
            id_cible = mat_selectionne.split(" - ")[0]
            row_actuelle = df_materiel_reel[df_materiel_reel["ID"] == id_cible].iloc[0]
            
            # On injecte les données de la base dans les champs du formulaire
            val_id = str(row_actuelle["ID"])
            val_nom = str(row_actuelle["Nom"])
            val_cat = row_actuelle["Catégorie"]
            val_marque = str(row_actuelle["Marque"]) if pd.notna(row_actuelle["Marque"]) else ""
            val_ref = str(row_actuelle["Référence"]) if pd.notna(row_actuelle["Référence"]) else ""
            val_serie = str(row_actuelle["N° de Série"]) if pd.notna(row_actuelle["N° de Série"]) else ""
            val_intervalle = int(row_actuelle["Intervalle (mois)"])
            desactiver_id = True # On empêche de modifier l'ID unique clé

    # Affichage du formulaire unifié
    if action_choisie == "🗑️ Supprimer un matériel du parc":
        # Formulaire simplifié pour la suppression
        with st.form("form_suppression_unique"):
            st.error(f"⚠️ Vous êtes sur le point de supprimer définitivement la fiche : **{val_id} — {val_nom}** ({val_marque})")
            confirmer = st.checkbox("Je confirme vouloir détruire ce matériel de la base de données")
            if st.form_submit_button("💥 CONFIRMER LA SUPPRESSION DÉFINITIVE", use_container_width=True):
                if confirmer:
                    with engine.begin() as conn_tx:
                        conn_tx.execute(sqlalchemy.text("DELETE FROM materiel WHERE id = :id;"), {"id": val_id})
                    st.warning(f"Le matériel [{val_id}] a été retiré.")
                    st.rerun()
                else:
                    st.error("Veuillez cocher la case de confirmation.")
    else:
        # Formulaire commun pour Création et Modification
        with st.form("form_gestion_unique"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                new_id = st.text_input("Identifiant Unique SOC (ex: MAT-010)", value=val_id, disabled=desactiver_id)
                new_nom = st.text_input("Nom de l'équipement", value=val_nom)
                new_cat = st.selectbox("Catégorie", ["Outillage Électroportatif", "Manutention", "Soudage", "Mesure"], index=["Outillage Électroportatif", "Manutention", "Soudage", "Mesure"].index(val_cat))
                new_marque = st.text_input("Marque / Fabricant", value=val_marque)
            with col_f2:
                new_ref = st.text_input("Référence Modèle", value=val_ref)
                new_serie = st.text_input("Numéro de Série usine", value=val_serie)
                if action_choisie == "➕ Enregistrer un nouveau matériel":
                    new_date = st.date_input("Date du dernier contrôle", val_date)
                new_intervalle = st.number_input("Intervalle de contrôle (en mois)", min_value=1, value=val_intervalle)
            
            st.markdown("**📸 Photo de l'appareil (Laisser vide en modification pour garder l'ancienne photo) :**")
            photo_capturee = st.camera_input("Prendre la photo du matériel", key="camera_unique")

            # Bouton de validation dynamique
            texte_bouton = "🚀 Créer et ajouter au parc" if action_choisie == "➕ Enregistrer un nouveau matériel" else "💾 Enregistrer les modifications"
            
            if st.form_submit_button(texte_bouton, use_container_width=True):
                if new_id.strip() and new_nom.strip():
                    image_b64_str = ""
                    if photo_capturee is not None:
                        bytes_data = photo_capturee.getvalue()
                        image_b64_str = base64.b64encode(bytes_data).decode('utf-8')
                    
                    with engine.begin() as conn_tx:
                        if action_choisie == "➕ Enregistrer un nouveau matériel":
                            # Action d'insertion
                            prochain_calcul = new_date + timedelta(days=int(new_intervalle) * 30)
                            conn_tx.execute(
                                sqlalchemy.text("""
                                    INSERT INTO materiel (id, nom, categorie, statut, detenteur, date_controle, intervalle_mois, prochain_controle, photo_base64, marque, reference, num_serie)
                                    VALUES (:id, :nom, :cat, 'Disponible', 'Atelier / Agence', :dt, :inv, :prox, :img, :marque, :ref, :serie);
                                """),
                                {
                                    "id": new_id.strip(), "nom": new_nom.strip(), "cat": new_cat, 
                                    "dt": new_date, "inv": int(new_intervalle), "prox": prochain_calcul, 
                                    "img": image_b64_str, "marque": new_marque.strip(), "ref": new_ref.strip(), "serie": new_serie.strip()
                                }
                            )
                            st.success(f"🎉 Nouveau matériel {new_nom} enregistré avec succès !")
                        else:
                            # Action de mise à jour
                            conn_tx.execute(
                                sqlalchemy.text("""
                                    UPDATE materiel 
                                    SET nom = :nom, categorie = :cat, marque = :marque, reference = :ref, num_serie = :serie, intervalle_mois = :inv
                                    WHERE id = :id;
                                """),
                                {"nom": new_nom.strip(), "cat": new_cat, "marque": new_marque.strip(), "ref": new_ref.strip(), "serie": new_serie.strip(), "inv": int(new_intervalle), "id": val_id}
                            )
                            if photo_capturee is not None:
                                conn_tx.execute(
                                    sqlalchemy.text("UPDATE materiel SET photo_base64 = :img WHERE id = :id;"),
                                    {"img": image_b64_str, "id": val_id}
                                )
                            st.success(f"⚡ Fiche {new_nom} mise à jour avec succès !")
                    st.rerun()
                else:
                    st.error("L'ID et le Nom sont requis.")

# ==========================================
# ONGLETS CHANTIERS & DIRECT
# ==========================================
with tab3:
    st.header("📅 Sorties Opérationnelles Directes")
    st.info("Espace de transit de matériel lourd d'artisan à artisan.")

with tab4:
    st.header("📍 Cartographie des Chantiers")
    map_data = pd.DataFrame(np.random.randn(3, 2) / [50, 50] + [47.33, -0.40], columns=['lat', 'lon'])
    st.map(map_data, zoom=10)

st.sidebar.image("https://img.icons8.com/clouds/100/000000/crane.png", width=60)
st.sidebar.title("Navigation")
st.sidebar.info("Application Interne v3.3 — SOC Industrie. Panneau d'administration centralisé.")
