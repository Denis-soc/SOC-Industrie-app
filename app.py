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
            if 'affectation_actuelle' not in df_commun.columns:
                df_commun['affectation_actuelle'] = None

            # --- PARTIE 1 : TABLEAU DE BORD ---
            st.subheader("📋 État actuel du parc")
            
            visual_status = []
            localisation_label = []
            
            for idx, row in df_commun.iterrows():
                au_depot = row['est_a_l_agence']
                if au_depot is True or au_depot == "True" or au_depot == "":
                    visual_status.append("🟢 Disponible")
                    localisation_label.append("📍 Dépôt (Terranjou)")
                else:
                    visual_status.append("🔴 En chantier")
                    qui = row['affectation_actuelle']
                    
                    # SÉCURITÉ : Si Supabase renvoie un tableau/liste, on extrait le premier élément texte
                    if isinstance(qui, list) and len(qui) > 0:
                        qui = qui[0]
                    elif isinstance(qui, str) and qui.startswith('{') and qui.endswith('}'):
                        qui = qui.strip('{}').replace('"', '')
                        
                    visual_status_str = f"👷 Sorti chez : {qui}" if qui else "🔴 Hors Agence"
                    localisation_label.append(visual_status_str)
            
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
                item_courant = df_commun[df_commun['num_interne'] == num_int_isole].iloc[0]
                
                etat_initial = item_courant['est_a_l_agence']
                bool_initial = True if (etat_initial is True or etat_initial == "True" or etat_initial == "") else False
                
                with st.form("form_mixte_reservation"):
                    st.markdown("##### 📥 Option A : Retour au dépôt")
                    a_l_agence = st.checkbox("Le matériel est de nouveau disponible à l'agence (Terranjou)", value=bool_initial)
                    
                    st.markdown("---")
                    st.markdown("##### 🚧 Option B : Planifier une nouvelle réservation (Chantier)")
                    
                    col_form1, col_form2 = st.columns(2)
                    with col_form1:
                        nom_demandeur = st.text_input("Nom du demandeur :", value="")
                        nom_chantier = st.text_input("Chantier / Affectation :", value="")
                    with col_form2:
                        date_debut = st.date_input("Date de début :", value=datetime.now().date())
                        date_fin = st.date_input("Date de fin :", value=datetime.now().date())
                    
                    btn_valider = st.form_submit_button("💾 Enregistrer le statut", use_container_width=True)
                    
                    if btn_valider:
                        try:
                            est_un_chantier = bool(nom_demandeur.strip() or nom_chantier.strip())
                            
                            if est_un_chantier:
                                if not nom_demandeur.strip() or not nom_chantier.strip():
                                    st.error("❌ Pour réserver sur un chantier, vous devez renseigner le nom du demandeur ET le chantier.")
                                elif date_fin < date_debut:
                                    st.error("❌ La date de fin ne peut pas être antérieure à la date de début.")
                                else:
                                    libelle_affectation = f"{nom_demandeur.strip()} ({nom_chantier.strip()})"
                                    
                                    # MISE À JOUR : On envoie une liste [libelle...] pour satisfaire le type text[] de Supabase
                                    supabase.table("materiel").update({
                                        "est_a_l_agence": False,
                                        "affectation_actuelle": [libelle_affectation]
                                    }).eq("num_interne", num_int_isole).execute()
                                    
                                    # Enregistrement dans l'historique
                                    supabase.table("reservations").insert({
                                        "num_interne": num_int_isole,
                                        "technicien": nom_demandeur.strip(),
                                        "num_affaire": nom_chantier.strip(),
                                        "date_debut": str(date_debut),
                                        "date_fin": str(date_fin),
                                        "statut": "Active"
                                    }).execute()
                                    
                                    st.success(f"🎉 Réservation validée pour {libelle_affectation} !")
                                    st.rerun()
                            else:
                                # Retour classique à l'agence (on passe le tableau à None/NULL)
                                supabase.table("materiel").update({
                                    "est_a_l_agence": True,
                                    "affectation_actuelle": None
                                }).eq("num_interne", num_int_isole).execute()
                                
                                st.success(f"📥 Le matériel {num_int_isole} est bien de retour à l'agence.")
                                st.rerun()
                                    
                        except Exception as e:
                            st.error(f"Erreur lors de la validation : {e}")
    else:
        st.info("Aucun matériel disponible.")       
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
            
            # À remplacer dans le bloc "Ajouter" de votre Tab 5 :

            # À remplacer sous le bouton "Valider l'ajout" (dans la condition if submit:)

        if submit:
            if not num.strip():
                st.warning("Le N° Interne est obligatoire.")
            else:
                # Fonction pour transformer les textes vides en None (NULL)
                def sans_vide(val):
                    if val is None:
                        return None
                    return val.strip() if str(val).strip() != "" else None
        
                # DÉFINITION EXPLICITE DE LA VARIABLE 'data'
                data = {
                    "num_interne": num.strip(), 
                    "Nom du Matériel": sans_vide(nom), 
                    "categorie": cat, 
                    "taille": sans_vide(taille), 
                    "reference": sans_vide(ref), 
                    "num_serie": sans_vide(ns), 
                    "fournisseur": sans_vide(fourn), 
                    "periodicite_controle": int(perio), 
                    "photo_url": sans_vide(url_photo),
                    "date_achat": str(date_achat) if date_achat else None,
                    "date_prochain_controle": str(date_prochain) if date_prochain else None,
                    "est_a_l_agence": True,
                    "affectation_actuelle": None
                }
                
                try:
                    # Envoi de la variable 'data' bien définie à Supabase
                    supabase.table("materiel").insert(data).execute()
                    st.success("🎉 Matériel ajouté avec succès !")
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
