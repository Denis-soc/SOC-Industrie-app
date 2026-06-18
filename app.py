import streamlit as st
import pandas as pd
from supabase import create_client
import uuid # Mettez-le ici avec les autres imports

# 1. CONFIGURATION
st.set_page_config(page_title="SOC Industrie – Gestion", page_icon="🏗️", layout="wide")

# 2. CONNEXION SUPABASE
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 3. CHARGEMENT DONNÉES
def charger_materiel():
    response = supabase.table("materiel").select("*").execute()
    return pd.DataFrame(response.data)

def charger_demandes():
    response = supabase.table("demandes_collaborateurs").select("*").execute()
    return pd.DataFrame(response.data)

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
# 5. CONTENU DES ONGLES
with tab1:
    st.header("📋 Catalogue du Matériel")
    
    # 1. Chargement et Nettoyage immédiat
    response = supabase.table("materiel").select("*").execute()
    df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
    
    if not df.empty:
        # Remplacer tous les NULL par du texte vide pour stabiliser le DataFrame
        df = df.fillna("")
        
        # 2. Filtrage pour ne garder que les articles valides (Nom non vide)
        df = df[df["Nom du Matériel"] != "Sans nom"]
        
        # Sélecteur
        cat_choisie = st.selectbox("Choisir le catalogue :", ["Tous"] + sorted(list(set(df["categorie"]))))
        df_filtre = df if cat_choisie == "Tous" else df[df["categorie"] == cat_choisie]
        
        # 3. Grille propre
        cols = st.columns(6)
        for i, (idx, row) in enumerate(df_filtre.reset_index().iterrows()):
            with cols[i % 6]:
                st.markdown(f"**{row['Nom du Matériel']}**")
                
                # Image seulement si URL valide
                url = str(row.get("photo_url", ""))
                if url.startswith("http"):
                    st.image(url, use_container_width=True)
                else:
                    # On affiche une zone vide de taille fixe pour garder l'alignement
                    st.write("") 
                
                st.caption(f"Ref: {row.get('reference', 'N/A')}")
                if st.button("Détails", key=f"btn_{idx}"):
                    st.info(f"N° Interne: {row.get('num_interne', '')}")
    else:
        st.write("Aucun matériel enregistré.")
with tab2:
    st.header("📋 Suivi des Contrôles & Étalonnages")
    
    try:
        response = supabase.table("materiel").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if not df.empty:
            df = df.fillna(0) # Remplace les cases vides par 0
            
            # Filtre : Matériel avec une périodicité définie
            df_suivi = df[df['periodicite_controle'].astype(int) > 0]
            
            st.write("Voici la liste du matériel nécessitant un suivi régulier :")
            
            # Affichage sous forme de tableau
            st.dataframe(
                df_suivi[['num_interne', 'Nom du Matériel', 'reference', 'periodicite_controle']],
                use_container_width=True
            )
            
            st.info("💡 Les alertes de contrôle automatique seront bientôt ajoutées ici.")
        else:
            st.info("Aucun matériel dans la base.")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
with tab5:
    st.header("⚙️ Administration du Matériel")
    
    # 1. Récupération des données
    try:
        response = supabase.table("materiel").select("*").execute()
        df_admin = pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur base : {e}")
        df_admin = pd.DataFrame()

    mode = st.radio("Action", ["Ajouter", "Modifier", "Supprimer"], horizontal=True)

    # 2. Fonction de formulaire robuste
    def afficher_form_complet(item=None):
        # Conversion sécurisée : on gère la ligne de DataFrame comme un dict
        item_dict = item.to_dict() if hasattr(item, 'to_dict') else (item if isinstance(item, dict) else {})
        
        with st.form("form_gestion"):
            col1, col2 = st.columns(2)
            with col1:
                # 'disabled' permet de verrouiller le N° interne en mode modification
                num = st.text_input("N° Interne", value=item_dict.get("num_interne", ""), disabled=(item is not None))
                nom = st.text_input("Nom du matériel", value=item_dict.get("Nom du Matériel", ""))
                cat = st.selectbox("Catégorie", ["EPI", "Outillage", "Consommables", "Soudage", "Mesure"], 
                                   index=0)
                taille = st.text_input("Taille (si EPI)", value=item_dict.get("taille", ""))
            with col2:
                ref = st.text_input("Référence", value=item_dict.get("reference", ""))
                ns = st.text_input("N° de série", value=item_dict.get("num_serie", ""))
                fourn = st.text_input("Fournisseur", value=item_dict.get("fournisseur", ""))
                perio = st.number_input("Périodicité contrôle (mois)", value=int(item_dict.get("periodicite_controle", 0) or 0))
                photo = st.file_uploader("Photo", type=['png', 'jpg', 'jpeg'])
            
            submit = st.form_submit_button("Valider")
            return submit, num, nom, cat, taille, ref, ns, fourn, perio, photo

    # 3. Logique d'exécution
    if mode == "Ajouter":
        submit, num, nom, cat, taille, ref, ns, fourn, perio, photo = afficher_form_complet()
        if submit and num:
        data = {
            "num_interne": num,
            "Nom du Matériel": nom,
            "categorie": cat,
            "taille": taille,
            "reference": ref,
            "num_serie": ns,
            "fournisseur": fourn,
            "periodicite_controle": int(perio) # Force le format entier
        }
        try:
            supabase.table("materiel").insert(data).execute()
            st.success("Matériel ajouté !")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur Supabase : {e}")

    elif mode == "Modifier":
        if not df_admin.empty:
            sel = st.selectbox("Choisir le N° Interne", df_admin["num_interne"].tolist())
            item = df_admin[df_admin["num_interne"] == sel].iloc[0]
            
            submit, num, nom, cat, taille, ref, ns, fourn, perio, photo = afficher_form_complet(item=item)
            if submit:
                upd = {"Nom du Matériel": nom, "categorie": cat, "taille": taille, "reference": ref, "num_serie": ns, "fournisseur": fourn, "periodicite_controle": perio}
                supabase.table("materiel").update(upd).eq("num_interne", num).execute()
                st.success("Modifié !")
                st.rerun()

    elif mode == "Supprimer":
        if not df_admin.empty:
            choix = st.selectbox("Supprimer le N° Interne", df_admin["num_interne"].tolist())
            if st.button("Confirmer la suppression"):
                supabase.table("materiel").delete().eq("num_interne", choix).execute()
                st.rerun()
