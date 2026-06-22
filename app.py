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

# 3. CHARGEMENT DONNÉES SÉCURISÉ
def charger_materiel():
    try:
        response = supabase.table("materiel").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
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
    "📦 Matériels Commun",
    "📅 Réservation matériel",
    "📍 Carte de localisation du matériel",
    "⚙️ Administration Matériel"
])

# 5. CONTENU DES ONGLETS
with tab1:
    st.header("🛒 Catalogue du Matériel")
    
    if 'panier' not in st.session_state:
        st.session_state.panier = {}

    if not df_materiel_reel.empty:
        # Sécurité si la colonne 'categorie' n'existe pas exactement sous ce nom
        col_cat = "categorie" if "categorie" in df_materiel_reel.columns else df_materiel_reel.columns[0]
        
        cat_choisie = st.selectbox("Catégorie :", ["Tous"] + sorted(list(set(df_materiel_reel[col_cat].dropna()))))
        df_filtre = df_materiel_reel if cat_choisie == "Tous" else df_materiel_reel[df_materiel_reel[col_cat] == cat_choisie]

        cols = st.columns(4) 
        for i, (idx, row) in enumerate(df_filtre.reset_index().iterrows()):
            # Fallbacks si les clés exactes n'existent pas
            nom_mat = row.get('Nom du Matériel', row.get('nom', 'Matériel sans nom'))
            num_int = row.get('num_interne', f"REF-{idx}")
            
            with cols[i % 4]:
                st.markdown(f"**{nom_mat}**")
                
                url = str(row.get("photo_url", ""))
                if url.startswith("http"):
                    st.image(url, width=150) 
                
                qte = st.number_input(f"Qté {num_int}", 0, 10, key=f"qte_{num_int}")
                taille = st.selectbox("Taille", ["", "S", "M", "L", "XL"], key=f"t_{num_int}")
                
                if st.button("Ajouter au panier", key=f"add_{num_int}"):
                    st.session_state.panier[num_int] = {"nom": nom_mat, "qte": qte, "taille": taille}
                    st.success("Ajouté !")

    # --- PARTIE PANIER ---
    st.divider()
    st.subheader("📦 Votre Panier")
    if st.session_state.panier:
        df_panier = pd.DataFrame.from_dict(st.session_state.panier, orient='index')
        st.table(df_panier)
        
        num_affaire = st.text_input("Entrez votre numéro d'affaire :")
        
        if num_affaire and st.button("Envoyer la commande à Olivier"):
            corps = f"Commande pour l'affaire {num_affaire} :\n\n" + df_panier.to_string()
            subject = f"Commande Matériel - Affaire {num_affaire}"
            mailto = f"mailto:owasse@soc.fr?subject={subject}&body={corps.replace(chr(10), '%0D%0A')}"
            st.markdown(f'<a href="{mailto}" style="padding: 10px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">Cliquer ici pour envoyer le mail</a>', unsafe_allow_html=True)
    else:
        st.info("Le panier est vide.")

with tab2:
    st.header("📋 Suivi des Contrôles & Étalonnages")
    
    if not df_materiel_reel.empty:
        df_suivi_df = df_materiel_reel.fillna(0)
        if 'periodicite_controle' in df_suivi_df.columns:
            try:
                df_suivi = df_suivi_df[df_suivi_df['periodicite_controle'].astype(int) > 0]
                st.write("Voici la liste du matériel nécessitant un suivi régulier :")
                
                colonnes_visibles = [c for c in ['num_interne', 'Nom du Matériel', 'reference', 'periodicite_controle'] if c in df_suivi.columns]
                st.dataframe(df_suivi[colonnes_visibles], use_container_width=True)
            except Exception as e:
                st.error(f"Erreur de tri des périodicités : {e}")
        else:
            st.warning("La colonne 'periodicite_controle' est introuvable.")
    else:
        st.info("Aucun matériel dans la base.")

with tab5:
    st.header("⚙️ Administration du Matériel")
    
    mode = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

    def afficher_form_complet(item=None):
        item_dict = item.to_dict() if hasattr(item, 'to_dict') else (item if isinstance(item, dict) else {})
        
        with st.form("form_gestion"):
            col1, col2 = st.columns(2)
            with col1:
                num = st.text_input("N° Interne", value=item_dict.get("num_interne", ""), disabled=(item is not None))
                nom = st.text_input("Nom du matériel", value=item_dict.get("Nom du Matériel", ""))
                cat = st.selectbox("Catégorie", ["EPI", "Outillage", "Consommables", "Soudage", "Mesure"], index=0)
                taille = st.text_input("Taille (si EPI)", value=item_dict.get("taille", ""))
            with col2:
                ref = st.text_input("Référence", value=item_dict.get("reference", ""))
                ns = st.text_input("N° de série", value=item_dict.get("num_serie", ""))
                fourn = st.text_input("Fournisseur", value=item_dict.get("fournisseur", ""))
                perio = st.number_input("Périodicité contrôle (mois)", value=int(item_dict.get("periodicite_controle", 0) or 0))
                url_photo = st.text_input("URL de la photo (lien http)", value=item_dict.get("photo_url", ""))
            
            submit = st.form_submit_button("Valider")
            return submit, num, nom, cat, taille, ref, ns, fourn, perio, url_photo

    # Compatibilité st.rerun selon la version locale de Streamlit
    def rafraichir_page():
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

    if mode == "Ajouter":
        submit, num, nom, cat, taille, ref, ns, fourn, perio, url_photo = afficher_form_complet()
        if submit:
            if not num:
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
                    "photo_url": url_photo
                }
                try:
                    supabase.table("materiel").insert(data).execute()
                    st.success("Matériel ajouté !")
                    rafraichir_page()
                except Exception as e:
                    st.error(f"Erreur Supabase : {e}")

    elif mode == "Modifier" and not df_materiel_reel.empty:
        if "num_interne" in df_materiel_reel.columns:
            sel = st.selectbox("Choisir le N° Interne", df_materiel_reel["num_interne"].tolist())
            item = df_materiel_reel[df_materiel_reel["num_interne"] == sel].iloc[0]
            
            submit, num, nom, cat, taille, ref, ns, fourn, perio, url_photo = afficher_form_complet(item=item)
            if submit:
                upd = {
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
                    supabase.table("materiel").update(upd).eq("num_interne", num).execute()
                    st.success("Modifié !")
                    rafraichir_page()
                except Exception as e:
                    st.error(f"Erreur lors de la modification : {e}")

    elif mode == "Supprimer" and not df_materiel_reel.empty:
        if "num_interne" in df_materiel_reel.columns:
            choix = st.selectbox("Supprimer le N° Interne", df_materiel_reel["num_interne"].tolist())
            if st.button("Confirmer la suppression"):
                try:
                    supabase.table("materiel").delete().eq("num_interne", choix).execute()
                    st.success(f"N° {choix} supprimé.")
                    rafraichir_page()
                except Exception as e:
                    st.error(f"Erreur lors de la suppression : {e}")
