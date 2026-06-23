with tab0:
    st.header("📦 Gestion des Stocks - Olivier")
    
    # 1. Initialisation de l'état du panier
    if 'panier_stock' not in st.session_state or not isinstance(st.session_state.panier_stock, list):
        st.session_state.panier_stock = []
    
    # 2. Récupération des données Supabase
    try:
        # On utilise une requête simple pour éviter les erreurs de colonnes inexistantes
        data_stock = supabase.table("materiel").select("*").execute()
        df_stock = pd.DataFrame(data_stock.data)
        
        data_hist = supabase.table("historique_mouvements").select("*").execute()
        df_hist = pd.DataFrame(data_hist.data)
    except Exception as e:
        st.error(f"Erreur de connexion base de données : {e}")
        st.stop()
    
    # --- A. TABLEAU ÉTAT DU STOCK ---
    if not df_stock.empty:
        st.subheader("État du stock détaillé")
        # On s'assure que la colonne quantité est numérique
        df_stock['quantité'] = pd.to_numeric(df_stock['quantité'], errors='coerce').fillna(0)
        
        # Affichage sélectif des colonnes
        cols_a_afficher = ['photo_url', 'num_interne', 'Nom du Matériel', 'quantité']
        # On vérifie si la colonne taille existe avant de l'afficher
        if 'taille' in df_stock.columns:
            cols_a_afficher.insert(3, 'taille')
            
        df_display = df_stock[cols_a_afficher].copy()
        
        st.data_editor(
            df_display, 
            column_config={"photo_url": st.column_config.ImageColumn("Photo")}, 
            use_container_width=True, 
            disabled=True
        )

        # --- B. FORMULAIRE D'AJOUT ---
        with st.expander("➕ Ajouter un mouvement au stock", expanded=True):
            with st.form("panier_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    ref = st.selectbox("Réf. Interne", sorted(df_stock['num_interne'].unique()))
                    type_mvt = st.radio("Type", ["Entrée", "Sortie"], horizontal=True)
                    qte = st.number_input("Quantité", min_value=1, step=1)
                with col_b:
                    taille = st.selectbox("Taille", options=st.session_state.liste_tailles)
                    collab = st.text_input("Collaborateur")
                    chantier = st.text_input("Code Chantier")
                
                if st.form_submit_button("Ajouter à la liste"):
                    st.session_state.panier_stock.append({
                        "ref": ref, "type": type_mvt, "qte": int(qte), 
                        "taille": taille, "nom": collab, "chantier": chantier
                    })
                    st.rerun()

        # --- C. PANIER ---
        if st.session_state.panier_stock:
            st.subheader("🛒 Panier en attente")
            st.dataframe(pd.DataFrame(st.session_state.panier_stock), use_container_width=True)
            
            cols = st.columns([1, 1, 4])
            if cols[0].button("🗑️ Vider le panier"):
                st.session_state.panier_stock = []
                st.rerun()
            
            idx_a_supprimer = cols[1].selectbox("Ligne", range(len(st.session_state.panier_stock)), format_func=lambda x: f"Ligne {x+1}")
            if cols[1].button("Retirer cette ligne"):
                st.session_state.panier_stock.pop(idx_a_supprimer)
                st.rerun()

            if st.button("✅ Valider tout le panier"):
                for item in st.session_state.panier_stock:
                    # Traitement de la mise à jour du stock
                    mask = (df_stock['num_interne'] == item['ref'])
                    ligne = df_stock[mask]
                    
                    if not ligne.empty:
                        stock_act = int(ligne.iloc[0]['quantité'])
                        new_stock = stock_act + item['qte'] if item['type'] == "Entrée" else max(0, stock_act - item['qte'])
                        
                        supabase.table("materiel").update({"quantité": new_stock}).eq("num_interne", item['ref']).execute()
                        
                        # Insertion Historique
                        supabase.table("historique_mouvements").insert({
                            "date": str(date.today()), 
                            "num_interne": item['ref'], 
                            "type_mvt": item['type'], 
                            "quantite": int(item['qte']), 
                            "code_chantier": str(item.get('chantier', '')), 
                            "collaborateur": str(item.get('nom', '')),
                            "taille": str(item.get('taille', ''))
                        }).execute()
                
                st.session_state.panier_stock = []
                st.success("Mise à jour réussie !")
                st.rerun()

    # --- D. HISTORIQUE & PDF ---
    st.subheader("📜 Historique des mouvements")
    if not df_hist.empty:
        st.dataframe(df_hist.sort_values(by="date", ascending=False), use_container_width=True)
    
    col_pdf, col_del = st.columns(2)
    
    if col_pdf.button("📄 Exporter Historique en PDF"):
        from fpdf import FPDF
        pdf = FPDF(orientation='L')
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Historique des mouvements", ln=True, align='C')
        pdf.set_font("Arial", size=9)
        # Headers
        for h in ["Date", "Réf", "Mvt", "Qté", "Taille", "Collab", "Chantier"]:
            pdf.cell(35, 10, h, border=1)
        pdf.ln()
        # Data
        for _, row in df_hist.sort_values(by="date", ascending=False).iterrows():
            for k in ['date', 'num_interne', 'type_mvt', 'quantite', 'taille', 'collaborateur', 'code_chantier']:
                pdf.cell(35, 8, str(row.get(k, '')), border=1)
            pdf.ln()
        st.download_button("📥 Télécharger PDF", pdf.output(dest='S').encode('latin-1'), "historique.pdf", "application/pdf")

    if col_del.button("🗑️ Vider l'historique"):
        supabase.table("historique_mouvements").delete().neq("id", -1).execute()
        st.rerun()
