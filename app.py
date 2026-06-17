import streamlit as st
import sqlalchemy
import pandas as pd

# 1. CONFIGURATION
st.set_page_config(page_title="SOC Industrie", layout="wide")
db_url = "postgresql://postgres.spxrxmzeaybndgpmoslo:LesGaulois2026@aws-0-eu-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
engine = sqlalchemy.create_engine(db_url)

# 2. LOGIQUE MÉTIER (Facile à modifier)
def executer_sql(query, params={}):
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text(query), params)

def get_data():
    return pd.read_sql("SELECT * FROM materiel", engine)

# 3. INTERFACE (Facile à faire évoluer)
tab_cat, tab_admin = st.tabs(["🛒 Catalogue", "⚙️ Administration"])

with tab_cat:
    st.dataframe(get_data())

with tab_admin:
    action = st.radio("Action :", ["Créer", "Modifier", "Supprimer"], horizontal=True)
    
    # Formulaire de saisie dynamique
    with st.form("admin_form"):
        id_mat = st.text_input("ID Matériel")
        nom = st.text_input("Nom")
        marque = st.text_input("Marque")
        
        submitted = st.form_submit_button("Valider")
        
        if submitted:
            if action == "Créer":
                executer_sql("INSERT INTO materiel (id, nom, marque) VALUES (:id, :nom, :marque)", 
                             {"id": id_mat, "nom": nom, "marque": marque})
            elif action == "Modifier":
                executer_sql("UPDATE materiel SET nom=:nom, marque=:marque WHERE id=:id", 
                             {"id": id_mat, "nom": nom, "marque": marque})
            elif action == "Supprimer":
                executer_sql("DELETE FROM materiel WHERE id=:id", {"id": id_mat})
            
            st.success(f"Action '{action}' effectuée avec succès !")
            st.rerun()
