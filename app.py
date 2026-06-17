# --- ONGLET 0 : TABLEAU DE BORD ---
with tab0:
    st.header("👑 Tableau de Bord Logistique")
    
    # 1. Gestion des demandes
    st.subheader("📋 Demandes en attente")
    if not df_demandes_reel.empty:
        st.dataframe(df_demandes_reel, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Aucune demande en attente.")
    
    st.markdown("---")
    
    # 2. Alertes étalonnage
    st.subheader("🚨 Alertes Étalonnages (< 90 jours)")
    aujourdhui = datetime.now().date()
    lignes_alertes = []
    
    for idx, row in df_materiel_reel.iterrows():
        # Conversion sécurisée de la date
        date_prox = row["Prochain Contrôle"]
        if isinstance(date_prox, str): 
            date_prox = datetime.strptime(date_prox, "%Y-%m-%d").date()
        elif isinstance(date_prox, datetime): 
            date_prox = date_prox.date()
            
        if (date_prox - aujourdhui).days <= 90:
            lignes_alertes.append({
                "ID": row["ID"], 
                "Matériel": row["Nom"], 
                "Détenteur": row["Détenteur"], 
                "Prochain Contrôle": date_prox
            })
            
    if lignes_alertes:
        st.dataframe(pd.DataFrame(lignes_alertes), use_container_width=True, hide_index=True)
    else:
        st.success("✅ Aucun étalonnage critique à prévoir.")
