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
def charger_materiel():
    try:
        response = supabase.table("materiel").select("*").execute()
        if response.data:
            # On remplace immédiatement les valeurs nulles/NaN par du texte vide ou 0
            df = pd.DataFrame(response.data)
            df = df.astype(object).fillna("")
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
                    taille = st.selectbox("Taille", ["", "S", "M", "L", "XL"], key=f"t_{num_int}")
                    
                    if st.button("Ajouter au panier", key=f"add_{num_int}"):
                        st.session_state.panier[num_int] = {"nom": nom_mat, "qte": qte, "taille": taille}
                        st.success("Ajouté !")
        else:
            st.info("Aucun matériel dans cette catégorie.")

  # --- PARTIE PANIER ---
    st.divider()
    st.subheader("📦 Votre Panier")
    
    if st.session_state.panier:
        df_panier = pd.DataFrame.from_dict(st.session_state.panier, orient='index')
        st.table(df_panier)
        
        # On crée deux colonnes pour saisir proprement le Nom et le N° d'affaire
        col_demandeur, col_affaire = st.columns(2)
        with col_demandeur:
            nom_demandeur = st.text_input("Nom du demandeur :", key="nom_demandeur_panier")
        with col_affaire:
            num_affaire = st.text_input("Entrez votre numéro d'affaire :", key="num_affaire_panier")
        
        # Le bouton de téléchargement ne s'active que si les deux champs sont remplis
        if nom_demandeur and num_affaire:
            
            # Fonction interne pour générer le PDF avec Nom, Affaire et DATE automatique
            def generer_pdf(df, affaire, demandeur):
                import io
                from datetime import datetime
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib import colors
                
                # Récupération et formatage de la date du jour (ex: 22/06/2026)
                date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
                
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                story = []
                
                styles = getSampleStyleSheet()
                
                # Styles personnalisés
                style_titre = ParagraphStyle(
                    'TitreEntreprise',
                    parent=styles['Heading1'],
                    fontSize=20,
                    leading=24,
                    textColor=colors.HexColor("#1A365D"),
                    spaceAfter=10
                )
                
                # En-tête du document PDF
                story.append(Paragraph("<b>SOC Industrie – Gestion Interne</b>", style_titre))
                story.append(Paragraph(f"<b>Bon de Commande Matériel / EPI</b>", styles['Heading2']))
                story.append(Spacer(1, 15))
                
                # Ajout des informations : Date, Demandeur, Affaire
                story.append(Paragraph(f"<b>Date de la demande :</b> {date_aujourdhui}", styles['Normal']))
                story.append(Paragraph(f"<b>Demandeur :</b> {demandeur}", styles['Normal']))
                story.append(Paragraph(f"<b>N° d'Affaire :</b> {affaire}", styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Préparation du tableau des données du panier
                donnees_table = [["N° Interne", "Désignation", "Quantité", "Taille"]]
                for num_int, row in df.iterrows():
                    donnees_table.append([
                        str(num_int),
                        str(row.get('nom', '')),
                        str(row.get('qte', '1')),
                        str(row.get('taille', '-'))
                    ])
                
                # Style du tableau
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

            # Génération du PDF
            pdf_data = generer_pdf(df_panier, num_affaire, nom_demandeur)
            
            # Bouton de téléchargement
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
    if not df_materiel_reel.empty:
        if 'periodicite_controle' in df_materiel_reel.columns:
            try:
                # On convertit en numérique proprement pour filtrer
                df_materiel_reel['periodicite_controle_num'] = pd.to_numeric(df_materiel_reel['periodicite_controle'], errors='coerce').fillna(0)
                df_suivi = df_materiel_reel[df_materiel_reel['periodicite_controle_num'] > 0]
                
                if not df_suivi.empty:
                    st.write("Voici la liste du matériel nécessitant un suivi régulier :")
                    colonnes_visibles = [c for c in ['num_interne', 'Nom du Matériel', 'reference', 'periodicite_controle'] if c in df_suivi.columns]
                    st.dataframe(df_suivi[colonnes_visibles], use_container_width=True)
                else:
                    st.info("Aucun matériel ne nécessite de contrôle périodique actuellement.")
            except Exception as e:
                st.error(f"Erreur de tri des périodicités : {e}")
        else:
            st.warning("La colonne 'periodicite_controle' est introuvable.")
    else:
        st.info("Aucun matériel dans la base.")

with tab5:
    st.header("⚙️ Administration du Matériel")
    
    mode = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

    if mode == "Ajouter":
        with st.form("form_ajouter"):
            col1, col2 = st.columns(2)
            with col1:
                num = st.text_input("N° Interne")
                nom = st.text_input("Nom du matériel")
                cat = st.selectbox("Catégorie", ["EPI", "Outillage", "Consommables", "Soudage", "Mesure"])
                taille = st.text_input("Taille (si EPI)")
            with col2:
                ref = st.text_input("Référence")
                ns = st.text_input("N° de série")
                fourn = st.text_input("Fournisseur")
                perio = st.number_input("Périodicité contrôle (mois)", value=0)
                url_photo = st.text_input("URL de la photo (lien http)")
            
            submit = st.form_submit_button("Valider l'ajout")
            
            if submit:
                if not num:
                    st.warning("Le N° Interne est obligatoire.")
                else:
                    data = {"num_interne": num, "Nom du Matériel": nom, "categorie": cat, "taille": taille, "reference": ref, "num_serie": ns, "fournisseur": fourn, "periodicite_controle": int(perio), "photo_url": url_photo}
                    try:
                        supabase.table("materiel").insert(data).execute()
                        st.success("Matériel ajouté !")
                        rafraichir_page()
                    except Exception as e:
                        st.error(f"Erreur Supabase : {e}")

    elif mode == "Modifier" and not df_materiel_reel.empty:
        if "num_interne" in df_materiel_reel.columns:
            liste_numeros = [n for n in df_materiel_reel["num_interne"].tolist() if n != ""]
            sel = st.selectbox("Choisir le matériel à modifier (par son N° Interne actuel)", liste_numeros)
            
            if sel:
                item = df_materiel_reel[df_materiel_reel["num_interne"] == sel].iloc[0]
                
                with st.form("form_modifier"):
                    col1, col2 = st.columns(2)
                    with col1:
                        # On stocke l'ancien numéro dans une variable cachée ou sous forme de texte informatif
                        st.info(f"Ancien N° Interne : {sel}")
                        
                        # Le champ est maintenant modifiable !
                        nouveau_num = st.text_input("Nouveau N° Interne", value=str(item.get("num_interne", "")))
                        
                        nom = st.text_input("Nom du matériel", value=str(item.get("Nom du Matériel", "")))
                        
                        cat_index = 0
                        categories_liste = ["EPI", "Outillage", "Consommables", "Soudage", "Mesure"]
                        if item.get("categorie") in categories_liste:
                            cat_index = categories_liste.index(item.get("categorie"))
                        cat = st.selectbox("Catégorie", categories_liste, index=cat_index)
                        
                        taille = st.text_input("Taille (si EPI)", value=str(item.get("taille", "")))
                    with col2:
                        ref = st.text_input("Référence", value=str(item.get("reference", "")))
                        ns = st.text_input("N° de série", value=str(item.get("num_serie", "")))
                        fourn = st.text_input("Fournisseur", value=str(item.get("fournisseur", "")))
                        
                        try:
                            val_perio = int(item.get("periodicite_controle", 0))
                        except:
                            val_perio = 0
                        perio = st.number_input("Périodicité contrôle (mois)", value=val_perio)
                        url_photo = st.text_input("URL de la photo (lien http)", value=str(item.get("photo_url", "")))
                    
                    submit = st.form_submit_button("Enregistrer les modifications")
                    
                    if submit:
                        if not nouveau_num.strip():
                            st.error("Le N° Interne ne peut pas être vide.")
                        else:
                            # On prépare les données incluant le potentiel NOUVEAU numéro interne
                            upd = {
                                "num_interne": nouveau_num,
                                "Nom du Matériel": nom, 
                                "categorie": cat, 
                                "taille": taille, 
                                "reference": ref, 
                                "num_serie": ns, 
                                "fournisseur": fourn, 
                                "periodicite_controle": int(perio), 
                                "photo_url": url_photo
                            }
                            try:
                                # CRUCIAL : On cherche l'ancienne ligne grâce à 'sel' (l'ancien numéro)
                                # et on lui applique le dictionnaire 'upd' (qui contient le nouveau numéro)
                                supabase.table("materiel").update(upd).eq("num_interne", sel).execute()
                                st.success("Modifié avec succès !")
                                rafraichir_page()
                            except Exception as e:
                                st.error(f"Erreur lors de la modification : {e}")

    elif mode == "Supprimer" and not df_materiel_reel.empty:
        if "num_interne" in df_materiel_reel.columns:
            liste_numeros = [n for n in df_materiel_reel["num_interne"].tolist() if n != ""]
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
