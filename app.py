import streamlit as st
import pandas as pd
from supabase import create_client
import uuid

# 1. CONFIGURATION
st.set_page_config(page_title="SOC Industrie – Gestion", page_icon="🏗️", layout="wide")

# 2. CONNEXION SUPABASE
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Impossible de se connecter à Supabase. Vérifiez vos secrets. Erreur : {e}")
    st.stop()

# 3. CHARGEMENT DONNÉES SÉCURISÉ & NETTOYÉ
# # 3. CHARGEMENT DONNÉES SÉCURISÉ & NETTOYÉ
# # 3. CHARGEMENT DONNÉES SÉCURISÉ & NETTOYÉ
def charger_materiel():
    try:
        response = supabase.table("materiel").select("*").execute()
        if response.data:
            # On crée d'abord le DataFrame
            df = pd.DataFrame(response.data)
            
            # --- SÉCURISATION DES COLONNES DE DATES ---
            if 'date_achat' not in df.columns:
                df['date_achat'] = None
            if 'date_prochain_controle' not in df.columns:
                df['date_prochain_controle'] = None
                
            # --- SÉCURISATION DES COLONNES DE RÉSERVATION ---
            if 'est_a_l_agence' not in df.columns:
                df['est_a_l_agence'] = True
            if 'affectation_actuelle' not in df.columns:
                df['affectation_actuelle'] = ""
                
            # On remplace immédiatement les valeurs nulles/NaN par du texte vide
            df = df.astype(object).fillna("")
            
            # --- TRI PAR N° INTERNE CROISSANT ---
            if 'num_interne' in df.columns:
                df['num_interne_str'] = df['num_interne'].astype(str)
                df = df.sort_values(by='num_interne_str', ascending=True).drop(columns=['num_interne_str'])
            
            return df
            
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la table 'materiel' : {e}")
        return pd.DataFrame()
def charger_demandes():
    try:
        response = supabase.table("demandes_collaborateurs").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur lors du chargement de la table 'demandes_collaborateurs' : {e}")
        return pd.DataFrame()

# Initialisation des données
df_materiel_reel = charger_materiel()
df_demandes_reel = charger_demandes()

# 4. INTERFACE
st.title("🏗️ SOC Industrie – Gestion Interne")

# Définition des onglets
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Tableau de Bord Olivier",
    "🛒 Catalogues EPI/Consommables/Outillage",
    "📋 Suivi Contrôles & Étalonnages", # Correspond au Tab2 mentionné
    "📅 Réservation matériel",
    "📍 Carte de localisation du matériel",
    "⚙️ Administration Matériel"
])

# Compatibilité st.rerun selon la version de Streamlit
def rafraichir_page():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# 5. CONTENU DES ONGLETS
import streamlit as st
import pandas as pd
from datetime import date

with tab0:
    st.header("📦 Gestion des Stocks - Olivier")
    
    # 1. INITIALISATION SÉCURISÉE (On force une liste vide si rien n'existe)
    if 'panier_stock' not in st.session_state or not isinstance(st.session_state.panier_stock, list):
        st.session_state.panier_stock = []
    
    try:
        # Récupération des données
        response = supabase.table("materiel").select("*").execute()
        df_stock = pd.DataFrame(response.data)
        
        if not df_stock.empty:
            # Nettoyage affichage
            df_display = df_stock[['photo_url', 'num_interne', 'Nom du Matériel', 'quantité']].copy()
            df_display['quantité'] = pd.to_numeric(df_display['quantité'], errors='coerce').fillna(0)
            
            st.subheader("État du stock")
            st.data_editor(
                df_display,
                column_config={"photo_url": st.column_config.ImageColumn("Photo")},
                use_container_width=True, disabled=True
            )

            # 2. FORMULAIRE "Ajouter au Panier"
            with st.expander("➕ Ajouter un mouvement au panier_stock", expanded=True):
                with st.form("panier_stock_form", clear_on_submit=True):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        ref_select = st.selectbox("Réf. Interne", df_stock['num_interne'].unique())
                        type_mvt = st.radio("Type", ["Entrée", "Sortie"], horizontal=True)
                        qte_input = st.number_input("Quantité", min_value=1, step=1)
                    with col_b:
                        taille = st.text_input("Taille")
                        collaborateur = st.text_input("Collaborateur")
                        chantier = st.text_input("Code Chantier")
                    
                    if st.form_submit_button("Ajouter à la liste"):
                        # Ajout sécurisé dans la liste
                        st.session_state.panier_stock.append({
                            "ref": ref_select, 
                            "type": type_mvt, 
                            "qte": int(qte_input),
                            "taille": taille, 
                            "nom": collaborateur, 
                            "chantier": chantier
                        })
                        st.rerun()

            # 3. GESTION DU PANIER (Affichage et Validation)
            if st.session_state.panier_stock:
                st.subheader("🛒 panier_stock en attente")
                # Construction sécurisée du DataFrame
                df_panier = pd.DataFrame(st.session_state.panier_stock)
                st.dataframe(df_panier_stock, use_container_width=True)
                
                col_c, col_d = st.columns(2)
                if col_c.button("❌ Vider le panier_stock"):
                    st.session_state.panier_stock = []
                    st.rerun()
                
                if col_d.button("✅ Valider tout"):
                    for item in st.session_state.panier_stock:
                        # Mise à jour Stock
                        art = df_stock[df_stock['num_interne'] == item['ref']].iloc[0]
                        stock_act = int(art['quantité']) if pd.notnull(art['quantité']) else 0
                        new_stock = stock_act + item['qte'] if item['type'] == "Entrée" else max(0, stock_act - item['qte'])
                        
                        supabase.table("materiel").update({"quantité": new_stock}).eq("num_interne", item['ref']).execute()
                        
                        # Insertion Historique
                        supabase.table("historique_mouvements").insert({
                            "date": str(date.today()),
                            "num_interne": item['ref'],
                            "type_mvt": item['type'],
                            "quantite": int(item['qte']),
                            "code_chantier": item['chantier'],
                            "collaborateur": item['nom'],
                            "taille": item['taille']
                        }).execute()
                    
                    st.session_state.panier = []
                    st.success("Opérations validées !")
                    st.rerun()
        else:
            st.info("Aucune donnée matérielle trouvée.")
    except Exception as e:
        st.error(f"Erreur technique : {e}")
with tab1:
    st.header("🛒 Catalogue du Matériel")
    
    if 'panier' not in st.session_state:
        st.session_state.panier = {}

    if not df_materiel_reel.empty:
        col_cat = "categorie" if "categorie" in df_materiel_reel.columns else df_materiel_reel.columns[0]
        
        # Filtrer les catégories valides (non vides)
        categories_dispo = sorted(list(set(df_materiel_reel[col_cat].dropna())))
        categories_dispo = [c for c in categories_dispo if c != ""]
        
        cat_choisie = st.selectbox("Catégorie :", ["Tous"] + categories_dispo)
        df_filtre = df_materiel_reel if cat_choisie == "Tous" else df_materiel_reel[df_materiel_reel[col_cat] == cat_choisie]

        if not df_filtre.empty:
            cols = st.columns(4) 
            for i, (idx, row) in enumerate(df_filtre.reset_index().iterrows()):
                nom_mat = row.get('Nom du Matériel', 'Matériel sans nom')
                num_int = row.get('num_interne', f"REF-{idx}")
                
                # Éviter d'afficher les lignes de test complètement vides
                if not nom_mat and not num_int:
                    continue
                    
                with cols[i % 4]:
                    st.markdown(f"**{nom_mat if nom_mat else 'Sans Nom'}**")
                    
                    url = str(row.get("photo_url", ""))
                    if url and url.startswith("http"):
                        st.image(url, width=150) 
                    
                    qte = st.number_input(f"Qté {num_int}", 0, 10, key=f"qte_{num_int}")
                    liste_tailles = [
                        "", 
                        # Tailles Standards (EPI / Vêtements)
                        "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL", 
                        # Tailles Numériques (Pantalons / Chaussures)
                        "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52"
                    ]

                    taille = st.selectbox("Taille", liste_tailles, key=f"t_{num_int}")
                    
                    if st.button("Ajouter au panier", key=f"add_{num_int}"):
                        st.session_state.panier[num_int] = {"nom": nom_mat, "qte": qte, "taille": taille}
                        st.success("Ajouté !")
        else:
            st.info("Aucun matériel dans cette catégorie.")

  # --- PARTIE PANIER ---
    st.divider()
    st.subheader("📦 Votre Panier")
    
    if st.session_state.panier:
        # 1. Transformation du panier en DataFrame pour l'affichage
        df_panier = pd.DataFrame.from_dict(st.session_state.panier, orient='index')
        
        # On renomme proprement les colonnes pour l'affichage
        df_affichage = df_panier.rename(columns={
            "nom": "Désignation",
            "qte": "Quantité",
            "taille": "Taille"
        })
        st.table(df_affichage)
        
        # 2. ZONE DE MODIFICATION / SUPPRESSION D'UN ARTICLE
        with st.expander("✏️ Modifier ou retirer un article du panier"):
            liste_articles_panier = list(st.session_state.panier.keys())
            article_a_modifier = st.selectbox("Sélectionner un N° Interne :", liste_articles_panier)
            
            if article_a_modifier:
                col_mod_qte, col_mod_btn = st.columns([2, 1])
                with col_mod_qte:
                    nouvelle_qte = st.number_input(
                        f"Nouvelle quantité pour {article_a_modifier}", 
                        min_value=1, 
                        max_value=20, 
                        value=int(st.session_state.panier[article_a_modifier]["qte"])
                    )
                with col_mod_btn:
                    st.write("") # Juste pour aligner le bouton verticalement
                    st.write("")
                    if st.button("🔄 Mettre à jour la quantité", use_container_width=True):
                        st.session_state.panier[article_a_modifier]["qte"] = nouvelle_qte
                        st.success("Quantité mise à jour !")
                        st.rerun()
                
                # Bouton pour supprimer l'article sélectionné
                if st.button(f"❌ Retirer l'article {article_a_modifier} du panier", use_container_width=True):
                    del st.session_state.panier[article_a_modifier]
                    st.success("Article retiré !")
                    st.rerun()

        # 3. BOUTON POUR VIDER TOUT LE PANIER
        if st.button("🗑️ Vider entièrement le panier", type="secondary"):
            st.session_state.panier = {}
            st.success("Le panier a été vidé.")
            st.rerun()
            
        st.divider()
        
        # 4. FORMULAIRE ET GÉNÉRATION DU PDF
        # On crée deux colonnes pour saisir proprement le Nom et le N° d'affaire
        col_demandeur, col_affaire = st.columns(2)
        with col_demandeur:
            nom_demandeur = st.text_input("Nom du demandeur :", key="nom_demandeur_panier")
        with col_affaire:
            num_affaire = st.text_input("Entrez votre numéro d'affaire :", key="num_affaire_panier")
        
        # Le bouton de téléchargement ne s'active que si les deux champs sont remplis
        if nom_demandeur and num_affaire:
            
            def generer_pdf(df, affaire, demandeur):
                import io
                from datetime import datetime
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib import colors
                
                date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
                
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                story = []
                
                styles = getSampleStyleSheet()
                
                style_titre = ParagraphStyle(
                    'TitreEntreprise',
                    parent=styles['Heading1'],
                    fontSize=20,
                    leading=24,
                    textColor=colors.HexColor("#1A365D"),
                    spaceAfter=10
                )
                
                story.append(Paragraph("<b>SOC Industrie – Gestion Interne</b>", style_titre))
                story.append(Paragraph(f"<b>Bon de Commande Matériel / EPI</b>", styles['Heading2']))
                story.append(Spacer(1, 15))
                
                story.append(Paragraph(f"<b>Date de la demande :</b> {date_aujourdhui}", styles['Normal']))
                story.append(Paragraph(f"<b>Demandeur :</b> {demandeur}", styles['Normal']))
                story.append(Paragraph(f"<b>N° d'Affaire :</b> {affaire}", styles['Normal']))
                story.append(Spacer(1, 20))
                
                donnees_table = [["N° Interne", "Désignation", "Quantité", "Taille"]]
                for num_int, row in df.iterrows():
                    donnees_table.append([
                        str(num_int),
                        str(row.get('nom', '')),
                        str(row.get('qte', '1')),
                        str(row.get('taille', '-'))
                    ])
                
                t = Table(donnees_table, colWidths=[100, 250, 70, 70])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('ALIGN', (2,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 11),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
                    ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
                    ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                    ('FONTSIZE', (0,1), (-1,-1), 10),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                
                story.append(t)
                doc.build(story)
                buffer.seek(0)
                return buffer.getvalue()

            pdf_data = generer_pdf(df_panier, num_affaire, nom_demandeur)
            
            st.download_button(
                label="📥 Télécharger le Bon de Commande (PDF)",
                data=pdf_data,
                file_name=f"Commande_{nom_demandeur.replace(' ', '_')}_Affaire_{num_affaire}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("💡 Veuillez renseigner le nom du demandeur ET le numéro d'affaire pour pouvoir générer le PDF.")
            
    else:
        st.info("Le panier est vide.")
with tab2:
    st.header("📋 Suivi des Contrôles & Étalonnages")
    
    from datetime import datetime

    if not df_materiel_reel.empty:
        # On ne garde que l'Outillage et le Matériel Commun pour ce suivi
        df_suivi = df_materiel_reel[df_materiel_reel['categorie'].isin(["Outillage", "Matériel Commun"])].copy()
        
        if not df_suivi.empty:
            # Conversion propre des dates pour faire les calculs
            df_suivi['date_prochain_controle'] = pd.to_datetime(df_suivi['date_prochain_controle'], errors='coerce')
            
            statuts = []
            prochaines_dates = []
            date_du_jour = datetime.now()
            
            for idx, row in df_suivi.iterrows():
                dt_prochain = row['date_prochain_controle']
                
                if pd.isnull(dt_prochain):
                    statuts.append("🔴 À renseigner")
                    prochaines_dates.append("Non planifié")
                else:
                    prochaines_dates.append(dt_prochain.strftime("%d/%m/%Y"))
                    jours_restants = (dt_prochain - date_du_jour).days
                    
                    if jours_restants < 0:
                        statuts.append("🔴 EN RETARD")
                    elif jours_restants <= 30:
                        statuts.append("🟡 À PRÉVOIR (<30j)")
                    else:
                        statuts.append("🟢 À JOUR")
            
            df_suivi['Statut'] = statuts
            df_suivi['Prochain Contrôle'] = prochaines_dates
            
            # Formater la date d'achat pour l'affichage
            df_suivi['Date d\'achat'] = pd.to_datetime(df_suivi['date_achat'], errors='coerce').apply(
                lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "Non renseignée"
            )
            
            # Filtres rapides pour Olivier
            filtre_statut = st.multiselect(
                "Filtrer par état :", 
                ["🔴 EN RETARD", "🟡 À PRÉVOIR (<30j)", "🟢 À JOUR", "🔴 À renseigner"],
                default=["🔴 EN RETARD", "🟡 À PRÉVOIR (<30j)", "🟢 À JOUR", "🔴 À renseigner"]
            )
            
            df_suivi_filtre = df_suivi[df_suivi['Statut'].isin(filtre_statut)]
            
            # Sélection et affichage des colonnes finales dans le tableau
            colonnes_affichage = [
                'Statut', 'num_interne', 'Nom du Matériel', 'categorie', 
                'Date d\'achat', 'periodicite_controle', 'Prochain Contrôle'
            ]
            
            df_tab_final = df_suivi_filtre[colonnes_affichage].rename(columns={
                'num_interne': 'N° Interne',
                'periodicite_controle': 'Intervalle (mois)',
                'categorie': 'Catégorie'
            })
            
            st.dataframe(df_tab_final, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun outillage ou matériel commun enregistré pour le moment.")
    else:
        st.info("Aucun matériel trouvé dans la base de données.")
with tab3:
    st.header("📅 Réservation & Affectation du Matériel Commun")
    st.markdown("📍 **Zone d'affectation par défaut :** Agence SOC Industrie — *70 route de Brissac, 49380 TERRANJOU*")
    
    from datetime import datetime

    if not df_materiel_reel.empty:
        df_commun = df_materiel_reel[df_materiel_reel['categorie'] == "Matériel Commun"].copy()
        
        if df_commun.empty:
            st.info("Aucun matériel commun enregistré pour le moment.")
        else:
            if 'est_a_l_agence' not in df_commun.columns:
                df_commun['est_a_l_agence'] = True

            # --- PARTIE 1 : TABLEAU DE BORD ---
            st.subheader("📋 État actuel du parc")
            
            visual_status = []
            localisation_label = []
            
            try:
                res_planning = supabase.table("reservations").select("*").eq("statut", "Active").execute()
                dict_res = {r['num_interne']: r for r in res_planning.data} if res_planning.data else {}
            except:
                dict_res = {}
            
            for idx, row in df_commun.iterrows():
                num_int = row['num_interne']
                au_depot = row['est_a_l_agence']
                
                if au_depot is True or au_depot == "True" or num_int not in dict_res:
                    visual_status.append("🟢 Disponible")
                    localisation_label.append("📍 Dépôt (Terranjou)")
                else:
                    info_res = dict_res[num_int]
                    # Récupération et formatage rapide des dates (AAAA-MM-JJ)
                    d_debut = info_res.get('date_debut', '')
                    d_fin = info_res.get('date_fin', '')
                    
                    # Formatage optionnel en JJ/MM si les dates existent
                    try:
                        date_deb_fr = datetime.strptime(d_debut, "%Y-%m-%d").strftime("%d/%m")
                        date_fin_fr = datetime.strptime(d_fin, "%Y-%m-%d").strftime("%d/%m")
                        dates_str = f"({date_deb_fr} au {date_fin_fr})"
                    except:
                        dates_str = f"({d_debut} au {d_fin})" if d_debut else ""

                    visual_status.append("🔴 En chantier")
                    localisation_label.append(f"👷 {info_res.get('technicien', '')} — 🏗️ {info_res.get('num_affaire', '')} {dates_str}")
            
            df_commun['Statut'] = visual_status
            df_commun['Localisation / Affectation'] = localisation_label
            
            st.dataframe(
                df_commun[['num_interne', 'Nom du Matériel', 'Statut', 'Localisation / Affectation']].rename(columns={'num_interne': 'N° Interne'}),
                use_container_width=True, hide_index=True
            )
            
            st.divider()
            
            # --- PARTIE 2 : FORMULAIRE ---
            st.subheader("🔄 Enregistrer un mouvement (Retour ou Nouvelle Réservation)")
            
            df_commun['choix_label'] = df_commun['num_interne'].astype(str) + " - " + df_commun['Nom du Matériel'].astype(str)
            mat_cible = st.selectbox("Sélectionner le matériel commun :", df_commun['choix_label'].tolist())
            
            if mat_cible:
                num_int_isole = mat_cible.split(" - ")[0]
                
                with st.form("form_mixte_reservation_v3"):
                    st.markdown("##### 📥 Option A : Retour au dépôt")
                    case_retour = st.checkbox("Le matériel est revenu et est de nouveau disponible à l'agence (Terranjou)")
                    
                    st.markdown("---")
                    st.markdown("##### 🚧 Option B : Planifier une nouvelle réservation (Chantier)")
                    
                    col_form1, col_form2 = st.columns(2)
                    with col_form1:
                        nom_demandeur = st.text_input("Nom du demandeur :", placeholder="Ex: Denis")
                        nom_chantier = st.text_input("Nom du chantier :", placeholder="Ex: ALH")
                        adresse_chantier = st.text_input("📍 Adresse complète du chantier (pour la carte) :", placeholder="Ex: 4 la villette, 49540 La Fosse-de-Tigné")
                    with col_form2:
                        date_debut = st.date_input("Date de début :", value=datetime.now().date())
                        date_fin = st.date_input("Date de fin :", value=datetime.now().date())
                    
                    btn_valider = st.form_submit_button("💾 Enregistrer le statut", use_container_width=True)
                    
                    if btn_valider:
                        try:
                            if case_retour:
                                supabase.table("materiel").update({
                                    "est_a_l_agence": True,
                                    "affectation_actuelle": None
                                }).eq("num_interne", num_int_isole).execute()
                                
                                supabase.table("reservations").update({"statut": "Terminée"}).eq("num_interne", num_int_isole).eq("statut", "Active").execute()
                                
                                st.success(f"📥 Le matériel {num_int_isole} est de retour au dépôt.")
                                st.rerun()
                            
                            else:
                                if not nom_demandeur.strip() or not nom_chantier.strip() or not adresse_chantier.strip():
                                    st.error("❌ Merci de renseigner le Demandeur, le Nom du chantier ET l'Adresse complète.")
                                elif date_fin < date_debut:
                                    st.error("❌ La date de fin ne peut pas être antérieure à la date de début.")
                                else:
                                    libelle_affichage = f"{nom_demandeur.strip()} ({nom_chantier.strip()})"
                                    
                                    supabase.table("materiel").update({
                                        "est_a_l_agence": False,
                                        "affectation_actuelle": [libelle_affichage]
                                    }).eq("num_interne", num_int_isole).execute()
                                    
                                    supabase.table("reservations").update({"statut": "Terminée"}).eq("num_interne", num_int_isole).eq("statut", "Active").execute()
                                    
                                    supabase.table("reservations").insert({
                                        "num_interne": num_int_isole,
                                        "technicien": nom_demandeur.strip(),
                                        "num_affaire": nom_chantier.strip(),
                                        "adresse_chantier": adresse_chantier.strip(),
                                        "date_debut": str(date_debut),
                                        "date_fin": str(date_fin),
                                        "statut": "Active"
                                    }).execute()
                                    
                                    st.success(f"🎉 Affectation validée avec succès pour le chantier {nom_chantier.strip()} !")
                                    st.rerun()
                                    
                        except Exception as e:
                            st.error(f"Erreur lors de l'enregistrement : {e}")
    else:
        st.info("Aucun matériel disponible.") 
import streamlit as st
import pandas as pd
import pydeck as pdk
from geopy.geocoders import Nominatim

with tab4:
    st.header("📍 Carte interactive de localisation")
    
    # 1. Récupération des données depuis Supabase
    try:
        res_actifs = supabase.table("reservations").select("*").eq("statut", "Active").execute()
        df_res = pd.DataFrame(res_actifs.data)
        data_mat = supabase.table("materiel").select("*").execute()
        df_mat = pd.DataFrame(data_mat.data)
    except Exception as e:
        st.error(f"Erreur de récupération des données : {e}")
        st.stop()
    
    geolocator = Nominatim(user_agent="soc_industrie_app_v3")
    
    # 2. Préparation dictionnaire pour grouper par coordonnées
    points_dict = {}

    # A. Ajout du Dépôt
    df_depot = df_mat[df_mat['est_a_l_agence'].astype(str).str.lower().isin(['true', '1'])]
    liste_mat_depot = [f"{row['num_interne']} ({row['Nom du Matériel']})" for _, row in df_depot.iterrows()]
    
    # Coordonnées Agence (arrondies pour correspondre aux chantiers)
    lat_ag, lon_ag = 47.3486, -0.4651
    points_dict[(round(lat_ag, 4), round(lon_ag, 4))] = {
        'lat': lat_ag, 'lon': lon_ag, 
        'label': '📍 Agence SOC Industrie', 
        'matériel': liste_mat_depot
    }

    # B. Ajout des Chantiers avec agrégation
    if not df_res.empty:
        for _, row in df_res.iterrows():
            try:
                location = geolocator.geocode(row['adresse_chantier'])
                if location:
                    coords = (round(location.latitude, 4), round(location.longitude, 4))
                    if coords in points_dict:
                        # Si le point existe déjà (ex: plusieurs matériels sur le même chantier), on ajoute à la liste
                        if row['num_interne'] not in points_dict[coords]['matériel']:
                            points_dict[coords]['matériel'].append(str(row['num_interne']))
                    else:
                        # Sinon on crée le point
                        points_dict[coords] = {
                            'lat': location.latitude, 'lon': location.longitude, 
                            'label': f"🏗️ {row['num_affaire']}", 
                            'matériel': [str(row['num_interne'])]
                        }
            except:
                continue

    # 3. Conversion du dictionnaire en liste finale pour Pydeck
    points_data = []
    for p in points_dict.values():
        p['matériel_str'] = " | ".join(p['matériel']) if isinstance(p['matériel'], list) else p['matériel']
        points_data.append(p)

    # 4. Affichage Pydeck
    if points_data:
        df_points = pd.DataFrame(points_data)
        
        view_state = pdk.ViewState(latitude=47.3486, longitude=-0.4651, zoom=10)
        
        st.pydeck_chart(pdk.Deck(
            initial_view_state=view_state,
            layers=[pdk.Layer(
                "ScatterplotLayer",
                df_points,
                get_position=["lon", "lat"],
                get_color=[200, 30, 0, 160],
                get_radius=300,
                pickable=True
            )],
            tooltip={"text": "{label}\nMatériel : {matériel_str}"}
        ))
    else:
        st.info("Aucune donnée de localisation disponible.")
with tab5:
    st.header("⚙️ Administration du Matériel")
    
    mode = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

    # Liste unique et harmonisée de vos 4 catégories
    categories_officielles = ["EPI", "Outillage", "Consommables", "Matériel Commun"]

    if mode == "Ajouter":
        with st.form("form_ajouter"):
            col1, col2 = st.columns(2)
            with col1:
                num = st.text_input("N° Interne")
                nom = st.text_input("Nom du matériel")
                cat = st.selectbox("Catégorie", categories_officielles, key="add_cat")
                
                # Condition : Si EPI, on demande la taille
                if cat == "EPI":
                    taille = st.text_input("Taille")
                else:
                    taille = ""
                    
                # Condition : Si Outillage ou Matériel Commun, on demande les dates et l'intervalle
                if cat in ["Outillage", "Matériel Commun"]:
                    date_achat = st.date_input("Date d'achat", value=None, key="add_achat")
                    perio = st.number_input("Intervalle / Périodicité contrôle (mois)", min_value=0, value=0, key="add_perio")
                    date_prochain = st.date_input("Date du prochain contrôle", value=None, key="add_prochain")
                else:
                    date_achat = None
                    perio = 0
                    date_prochain = None

            with col2:
                ref = st.text_input("Référence")
                ns = st.text_input("N° de série")
                fourn = st.text_input("Fournisseur")
                url_photo = st.text_input("URL de la photo (lien http)")
                
                # Si ce n'est pas un outillage/matériel commun, on cache la périodicité ici
                if cat not in ["Outillage", "Matériel Commun"]:
                    perio = st.number_input("Périodicité contrôle (mois)", min_value=0, value=0, key="add_perio_autre")
            
            submit = st.form_submit_button("Valider l'ajout")
            
            if submit:
                if not num.strip():
                    st.warning("Le N° Interne est obligatoire.")
                else:
                    data = {
                        "num_interne": num, 
                        "Nom du Matériel": nom, 
                        "categorie": cat, 
                        "taille": taille, 
                        "reference": ref, 
                        "num_serie": ns, 
                        "fournisseur": fourn, 
                        "periodicite_controle": int(perio), 
                        "photo_url": url_photo,
                        "date_achat": str(date_achat) if date_achat else None,
                        "date_prochain_controle": str(date_prochain) if date_prochain else None,
                        # --- VALEURS PAR DÉFAUT POUR LA RÉSERVATION ---
                        "est_a_l_agence": True,
                        "affectation_actuelle": ""
                    }
                    try:
                        supabase.table("materiel").insert(data).execute()
                        st.success("Matériel ajouté !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur Supabase : {e}")

    elif mode == "Modifier" and not df_materiel_reel.empty:
        if "num_interne" in df_materiel_reel.columns:
            liste_numeros = [n for n in df_materiel_reel["num_interne"].tolist() if str(n).strip() != ""]
            sel = st.selectbox("Choisir le matériel à modifier (par son N° Interne actuel)", liste_numeros)
            
            if sel:
                item = df_materiel_reel[df_materiel_reel["num_interne"] == sel].iloc[0]
                
                with st.form("form_modifier"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"Ancien N° Interne : {sel}")
                        nouveau_num = st.text_input("Nouveau N° Interne", value=str(item.get("num_interne", "")))
                        nom = st.text_input("Nom du matériel", value=str(item.get("Nom du Matériel", "")))
                        
                        cat_index = 0
                        item_cat = item.get("categorie")
                        if item_cat in categories_officielles:
                            cat_index = categories_officielles.index(item_cat)
                        
                        cat = st.selectbox("Catégorie", categories_officielles, index=cat_index, key="mod_cat")
                        
                        if cat == "EPI":
                            taille = st.text_input("Taille", value=str(item.get("taille", "")))
                        else:
                            taille = ""
                            
                        try:
                            val_perio = int(item.get("periodicite_controle", 0))
                        except:
                            val_perio = 0
                            
                        if cat in ["Outillage", "Matériel Commun"]:
                            val_achat = pd.to_datetime(item.get("date_achat")).date() if item.get("date_achat") else None
                            val_prochain = pd.to_datetime(item.get("date_prochain_controle")).date() if item.get("date_prochain_controle") else None
                            
                            date_achat = st.date_input("Date d'achat", value=val_achat, key="mod_achat")
                            perio = st.number_input("Intervalle / Périodicité contrôle (mois)", min_value=0, value=val_perio, key="mod_perio")
                            date_prochain = st.date_input("Date du prochain contrôle", value=val_prochain, key="mod_prochain")
                        else:
                            date_achat = None
                            date_prochain = None

                    with col2:
                        ref = st.text_input("Référence", value=str(item.get("reference", "")))
                        ns = st.text_input("N° de série", value=str(item.get("num_serie", "")))
                        fourn = st.text_input("Fournisseur", value=str(item.get("fournisseur", "")))
                        url_photo = st.text_input("URL de la photo (lien http)", value=str(item.get("photo_url", "")))
                        
                        if cat not in ["Outillage", "Matériel Commun"]:
                            perio = st.number_input("Périodicité contrôle (mois)", min_value=0, value=val_perio, key="mod_perio_autre")
                    
                    submit = st.form_submit_button("Enregistrer les modifications")
                    
                    if submit:
                        if not nouveau_num.strip():
                            st.error("Le N° Interne ne peut pas être vide.")
                        else:
                            upd = {
                                "num_interne": nouveau_num,
                                "Nom du Matériel": nom, 
                                "categorie": cat, 
                                "taille": taille, 
                                "reference": ref, 
                                "num_serie": ns, 
                                "fournisseur": fourn, 
                                "periodicite_controle": int(perio), 
                                "photo_url": url_photo,
                                "date_achat": str(date_achat) if date_achat else None,
                                "date_prochain_controle": str(date_prochain) if date_prochain else None
                            }
                            try:
                                supabase.table("materiel").update(upd).eq("num_interne", sel).execute()
                                st.success("Modifié avec succès !")
                                rafraichir_page()
                            except Exception as e:
                                st.error(f"Erreur lors de la modification : {e}")
    elif mode == "Supprimer" and not df_materiel_reel.empty:
        if "num_interne" in df_materiel_reel.columns:
            liste_numeros = [n for n in df_materiel_reel["num_interne"].tolist() if str(n).strip() != ""]
            choix = st.selectbox("Sélectionner le N° Interne à supprimer", liste_numeros)
            
            if choix:
                item_suppr = df_materiel_reel[df_materiel_reel["num_interne"] == choix].iloc[0]
                st.warning(f"Attention, vous allez supprimer définitivement : {item_suppr.get('Nom du Matériel', 'Matériel inconnu')}")
                
                if st.button("Confirmer la suppression définitive"):
                    try:
                        supabase.table("materiel").delete().eq("num_interne", choix).execute()
                        st.success(f"N° {choix} supprimé.")
                        rafraichir_page()
                    except Exception as e:
                        st.error(f"Erreur lors de la suppression : {e}")
