# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import io
import json
from PIL import Image
import os

# Import des modules
from config import APP_NAME, APP_VERSION, THRESHOLDS, ALERT_LEVELS
from database import Database
from auth import AuthManager
from ai_engine import AIEngine
from utils import (
    generate_report_pdf, create_excel_export, create_dashboard_charts,
    display_metrics, get_download_link, format_timestamp, get_status_color,
    get_severity_icon, truncate_text, safe_json_parse, create_sentiment_chart
)

# Configuration de la page
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation des composants
db = Database()
auth = AuthManager()
ai_engine = AIEngine()

# ============ SIDEBAR ============
def render_sidebar():
    """Rendu de la barre latérale"""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1a5276/ffffff?text=Amani+AI", use_column_width=True)
        
        if auth.is_authenticated():
            user = auth.get_current_user()
            st.markdown(f"### 👤 {user.get('full_name', user.get('username'))}")
            st.markdown(f"*Rôle: {user.get('role', 'observer')}*")
            
            # Navigation
            st.markdown("---")
            
            # Menu principal
            menu_items = {
                "🏠 Dashboard": "dashboard",
                "📝 Analyse": "analysis",
                "🗺️ Cartographie": "maps",
                "📊 Rapports": "reports",
                "🔔 Alertes": "alerts"
            }
            
            # Admin menu
            if auth.has_permission("manage_users"):
                menu_items["⚙️ Administration"] = "admin"
            
            # Sélection de la page
            page = st.radio("Navigation", list(menu_items.keys()))
            st.session_state['page'] = menu_items[page]
            
            st.markdown("---")
            
            # Déconnexion
            if st.button("🚪 Déconnexion", use_container_width=True):
                auth.logout()
        else:
            # Page de connexion/inscription
            st.markdown("### 🔐 Authentification")
            
            tab1, tab2 = st.tabs(["Connexion", "Inscription"])
            
            with tab1:
                login_form()
            
            with tab2:
                register_form()

def login_form():
    """Formulaire de connexion"""
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
        
        if submitted:
            if auth.login(username, password):
                st.success("Connexion réussie!")
                st.rerun()
            else:
                st.error("Identifiants incorrects")

def register_form():
    """Formulaire d'inscription"""
    with st.form("register_form"):
        username = st.text_input("Nom d'utilisateur")
        email = st.text_input("Email")
        full_name = st.text_input("Nom complet")
        password = st.text_input("Mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password")
        role = st.selectbox("Rôle", ["observer", "analyst", "moderator"])
        
        submitted = st.form_submit_button("S'inscrire")
        
        if submitted:
            if password != confirm_password:
                st.error("Les mots de passe ne correspondent pas")
            elif not username or not email:
                st.error("Les champs sont obligatoires")
            elif len(password) < 6:
                st.error("Le mot de passe doit contenir au moins 6 caractères")
            else:
                if auth.register_user(username, email, password, full_name, role):
                    st.success("Inscription réussie! Vous pouvez maintenant vous connecter.")
                else:
                    st.error("Utilisateur déjà existant")

# ============ PAGES ============

def render_dashboard():
    """Page Dashboard"""
    st.title("🏠 Tableau de Bord")
    
    if not auth.is_authenticated():
        st.warning("Veuillez vous connecter pour accéder au tableau de bord")
        return
    
    # Statistiques
    stats = db.get_statistics()
    
    # Métriques
    display_metrics(
        stats.get('total_users', 0),
        stats.get('total_analyses', 0),
        stats.get('active_alerts', 0),
        stats.get('average_score', 0)
    )
    
    st.markdown("---")
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        create_dashboard_charts(stats)
    
    with col2:
        # Analyses récentes
        st.subheader("📋 Analyses récentes")
        recent_analyses = db.get_all_analyses(limit=5)
        
        if recent_analyses:
            df = pd.DataFrame(recent_analyses)
            df_display = df[['created_at', 'content_type', 'score', 'status']].copy()
            df_display['created_at'] = df_display['created_at'].apply(format_timestamp)
            
            # Formatage des scores
            df_display['score'] = df_display['score'].apply(lambda x: f"{x:.1f}%" if x else "N/A")
            
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("Aucune analyse récente")
    
    # Alertes récentes
    st.subheader("🔔 Alertes récentes")
    recent_alerts = db.get_alerts(limit=5)
    
    if recent_alerts:
        for alert in recent_alerts:
            severity = alert['severity']
            icon = get_severity_icon(severity)
            status_color = get_status_color(alert['status'])
            
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.markdown(f"{icon} **{severity.upper()}**")
            with col2:
                st.markdown(truncate_text(alert['message']))
            with col3:
                st.markdown(f"*{format_timestamp(alert['created_at'])}*")
            
            if alert['status'] == 'new':
                if st.button(f"Résoudre", key=f"resolve_{alert['id']}"):
                    user = auth.get_current_user()
                    db.resolve_alert(alert['id'], user['id'])
                    st.success("Alerte résolue")
                    st.rerun()
            
            st.divider()
    else:
        st.info("Aucune alerte récente")

def render_analysis():
    """Page d'analyse"""
    st.title("📝 Analyse de contenu")
    
    if not auth.is_authenticated():
        st.warning("Veuillez vous connecter pour analyser du contenu")
        return
    
    user = auth.get_current_user()
    
    # Onglets d'analyse
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Texte", "🖼️ Image", "🎵 Audio", "🎬 Vidéo"])
    
    with tab1:
        render_text_analysis(user)
    
    with tab2:
        render_image_analysis(user)
    
    with tab3:
        render_audio_analysis(user)
    
    with tab4:
        render_video_analysis(user)

def render_text_analysis(user):
    """Analyse de texte"""
    st.markdown("### Analyse de texte")
    
    text = st.text_area(
        "Entrez le texte à analyser",
        height=200,
        placeholder="Collez votre texte ici..."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("Langue", ["fr", "en", "ar", "sw", "ln"])
    with col2:
        analyze_button = st.button("🔍 Analyser", use_container_width=True)
    
    if analyze_button and text:
        if len(text) < 10:
            st.warning("Le texte est trop court pour une analyse pertinente (minimum 10 caractères)")
            return
        
        with st.spinner("Analyse en cours..."):
            # Création de l'analyse dans la BDD
            analysis_id = db.create_analysis(user['id'], "text", text[:500])
            
            # Analyse IA
            result = ai_engine.analyze_text(text, language)
            
            # Mise à jour de la BDD
            db.update_analysis_result(analysis_id, result, result.get('credibility_score', 50))
            
            # Affichage des résultats
            display_analysis_results(result, "text")
            
            # Log
            db.add_log(user['id'], "analyze_text", f"Analyse texte: {truncate_text(text, 50)}")
            
            # Gestion des alertes
            check_and_create_alerts(analysis_id, result)

def render_image_analysis(user):
    """Analyse d'image"""
    st.markdown("### Analyse d'image")
    
    uploaded_file = st.file_uploader(
        "Choisissez une image",
        type=['jpg', 'jpeg', 'png', 'gif', 'bmp']
    )
    
    if uploaded_file is not None:
        # Affichage de l'image
        image = Image.open(uploaded_file)
        st.image(image, caption="Image téléchargée", use_column_width=True)
        
        if st.button("🔍 Analyser l'image", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                # Sauvegarde temporaire
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Création de l'analyse
                analysis_id = db.create_analysis(user['id'], "image", file_path=temp_path)
                
                # Analyse IA
                result = ai_engine.analyze_image(temp_path)
                
                # Mise à jour de la BDD
                db.update_analysis_result(analysis_id, result, result.get('credibility_score', 50))
                
                # Affichage des résultats
                display_analysis_results(result, "image")
                
                # Log
                db.add_log(user['id'], "analyze_image", f"Analyse image: {uploaded_file.name}")

def render_audio_analysis(user):
    """Analyse audio"""
    st.markdown("### Analyse audio")
    
    uploaded_file = st.file_uploader(
        "Choisissez un fichier audio",
        type=['mp3', 'wav', 'm4a', 'ogg', 'flac']
    )
    
    if uploaded_file is not None:
        st.audio(uploaded_file)
        
        if st.button("🔍 Analyser l'audio", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                analysis_id = db.create_analysis(user['id'], "audio", file_path=temp_path)
                result = ai_engine.analyze_audio(temp_path)
                db.update_analysis_result(analysis_id, result, result.get('credibility_score', 50))
                display_analysis_results(result, "audio")
                db.add_log(user['id'], "analyze_audio", f"Analyse audio: {uploaded_file.name}")

def render_video_analysis(user):
    """Analyse vidéo"""
    st.markdown("### Analyse vidéo")
    
    uploaded_file = st.file_uploader(
        "Choisissez une vidéo",
        type=['mp4', 'avi', 'mov', 'mkv']
    )
    
    if uploaded_file is not None:
        st.video(uploaded_file)
        
        if st.button("🔍 Analyser la vidéo", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                analysis_id = db.create_analysis(user['id'], "video", file_path=temp_path)
                result = ai_engine.analyze_video(temp_path)
                db.update_analysis_result(analysis_id, result, result.get('credibility_score', 50))
                display_analysis_results(result, "video")
                db.add_log(user['id'], "analyze_video", f"Analyse vidéo: {uploaded_file.name}")

def display_analysis_results(result: dict, content_type: str):
    """Affiche les résultats d'analyse"""
    st.markdown("### 📊 Résultats de l'analyse")
    
    # Scores
    col1, col2, col3, col4 = st.columns(4)
    
    score_mappings = {
        "text": [
            ("Discours de haine", "hate_speech_score"),
            ("Incitation à la violence", "violence_score"),
            ("Désinformation", "disinformation_score"),
            ("Crédibilité", "credibility_score")
        ],
        "image": [
            ("Violence détectée", "violence_detected"),
            ("Symboles haineux", "hate_symbols"),
            ("Visages détectés", "faces_detected"),
            ("Crédibilité", "credibility_score")
        ],
        "audio": [
            ("Émotions", "emotions"),
            ("Langue", "language"),
            ("Transcription", "transcript"),
            ("Crédibilité", "credibility_score")
        ],
        "video": [
            ("Violence", "violence_detected"),
            ("Foule", "crowd_detected"),
            ("Scènes", "scene_changes"),
            ("Crédibilité", "credibility_score")
        ]
    }
    
    mappings = score_mappings.get(content_type, [])
    
    for i, (label, key) in enumerate(mappings):
        with [col1, col2, col3, col4][i]:
            value = result.get(key, "N/A")
            
            if isinstance(value, bool):
                value = "⚠️ Oui" if value else "✅ Non"
                color = "red" if value == "⚠️ Oui" else "green"
                st.metric(label, value, delta_color=color)
            elif isinstance(value, float) or isinstance(value, int):
                if key == "credibility_score":
                    st.metric(label, f"{value:.1f}%")
                else:
                    st.metric(label, f"{value:.2f}")
            else:
                st.metric(label, str(value)[:20])
    
    # Détails
    if content_type == "text" and "entities" in result:
        st.markdown("#### 🏷️ Entités détectées")
        entities = result.get("entities", [])
        if entities:
            st.write(", ".join(entities))
        else:
            st.write("Aucune entité détectée")
    
    if "sentiment" in result:
        sentiment = result.get("sentiment", "neutre")
        emojis = {"positif": "😊", "neutre": "😐", "négatif": "😞"}
        st.markdown(f"#### Sentiment: {emojis.get(sentiment, '😐')} {sentiment.upper()}")
    
    # Modèle utilisé
    if "model_used" in result:
        st.caption(f"Modèle utilisé: {result.get('model_used', 'basic')}")
    
    # Historique
    st.markdown("---")
    if st.button("📜 Voir l'historique des analyses"):
        st.session_state['page'] = "dashboard"
        st.rerun()

def check_and_create_alerts(analysis_id: str, result: dict):
    """Vérifie et crée des alertes si nécessaire"""
    # Vérification des seuils
    thresholds = THRESHOLDS
    
    if result.get('hate_speech_score', 0) > thresholds['hate_speech']:
        db.create_alert(
            analysis_id,
            "high",
            f"Discours de haine détecté avec un score de {result['hate_speech_score']:.2f}"
        )
    
    if result.get('violence_score', 0) > thresholds['violence']:
        db.create_alert(
            analysis_id,
            "critical",
            f"Incitation à la violence détectée avec un score de {result['violence_score']:.2f}"
        )
    
    if result.get('disinformation_score', 0) > thresholds['disinformation']:
        db.create_alert(
            analysis_id,
            "medium",
            f"Désinformation potentielle détectée avec un score de {result['disinformation_score']:.2f}"
        )
    
    if result.get('credibility_score', 100) < thresholds['credibility'] * 100:
        db.create_alert(
            analysis_id,
            "medium",
            f"Faible crédibilité détectée: {result['credibility_score']:.1f}%"
        )

def render_maps():
    """Page Cartographie"""
    st.title("🗺️ Cartographie des tendances")
    
    if not auth.is_authenticated():
        st.warning("Veuillez vous connecter pour accéder à la cartographie")
        return
    
    # Map interactive (simulée)
    st.markdown("### Carte des tensions")
    
    # Utilisation de Leaflet via HTML (simplifié)
    import folium
    from streamlit_folium import folium_static
    
    # Création d'une carte centrée sur l'Afrique
    m = folium.Map(location=[0, 20], zoom_start=3)
    
    # Points de tension simulés
    hotspots = [
        {"lat": -1.2864, "lon": 36.8172, "name": "Nairobi", "risk": "Élevé"},
        {"lat": 4.0435, "lon": 9.7040, "name": "Douala", "risk": "Moyen"},
        {"lat": 9.0817, "lon": 8.6753, "name": "Abuja", "risk": "Élevé"},
        {"lat": -3.3612, "lon": 29.3499, "name": "Bujumbura", "risk": "Critique"},
        {"lat": -4.0383, "lon": 21.7587, "name": "Mbandaka", "risk": "Élevé"}
    ]
    
    for point in hotspots:
        color = {"Élevé": "red", "Moyen": "orange", "Critique": "darkred"}.get(point["risk"], "blue")
        folium.Marker(
            [point["lat"], point["lon"]],
            popup=f"{point['name']} - Risque: {point['risk']}",
            icon=folium.Icon(color=color, icon="info-sign")
        ).add_to(m)
    
    folium_static(m)
    
    # Statistiques régionales
    st.markdown("### Statistiques par région")
    
    stats_data = pd.DataFrame({
        'Région': ['Afrique de l\'Ouest', 'Afrique de l\'Est', 'Afrique Centrale', 'Afrique du Sud'],
        'Tensions': [45, 62, 38, 27],
        'Alertes': [12, 18, 9, 5]
    })
    
    st.dataframe(stats_data, use_container_width=True)

def render_reports():
    """Page Rapports"""
    st.title("📊 Rapports et Export")
    
    if not auth.is_authenticated():
        st.warning("Veuillez vous connecter pour accéder aux rapports")
        return
    
    user = auth.get_current_user()
    
    tab1, tab2 = st.tabs(["📄 Générer un rapport", "📁 Historique"])
    
    with tab1:
        st.markdown("### Générer un rapport personnalisé")
        
        # Sélection des données
        analyses = db.get_user_analyses(user['id'])
        
        if not analyses:
            st.warning("Aucune analyse trouvée. Effectuez d'abord des analyses.")
            return
        
        selected_analyses = st.multiselect(
            "Sélectionner les analyses à inclure",
            options=[(a['id'], f"{format_timestamp(a['created_at'])} - {a['content_type']}") for a in analyses],
            format_func=lambda x: x[1]
        )
        
        report_name = st.text_input("Nom du rapport", f"Rapport_{datetime.now().strftime('%Y%m%d')}")
        
        col1, col2 = st.columns(2)
        with col1:
            report_format = st.selectbox("Format", ["PDF", "Excel", "CSV"])
        with col2:
            include_scores = st.checkbox("Inclure les scores détaillés", value=True)
        
        if st.button("📥 Générer le rapport", use_container_width=True):
            if not selected_analyses:
                st.error("Veuillez sélectionner au moins une analyse")
                return
            
            with st.spinner("Génération du rapport..."):
                # Récupération des données
                selected_ids = [s[0] for s in selected_analyses]
                selected_data = [db.get_analysis(id) for id in selected_ids]
                
                # Préparation du contenu
                report_content = {
                    "name": report_name,
                    "date": datetime.now().isoformat(),
                    "user": user['username'],
                    "analyses": selected_data,
                    "scores": {},
                    "recommendations": [
                        "Surveiller les sources de ce contenu",
                        "Vérifier les faits auprès de sources fiables",
                        "Documenter l'analyse pour référence future"
                    ]
                }
                
                # Extraction des scores
                for analysis in selected_data:
                    if analysis and analysis.get('result'):
                        result = analysis['result']
                        if isinstance(result, dict):
                            for key in ['hate_speech_score', 'violence_score', 'disinformation_score', 'credibility_score']:
                                if key in result:
                                    report_content['scores'][key] = report_content['scores'].get(key, 0) + result[key]
                
                # Moyenne des scores
                for key in report_content['scores']:
                    report_content['scores'][key] /= len(selected_data)
                
                # Génération du PDF
                if report_format == "PDF":
                    pdf_data = generate_report_pdf(report_content)
                    filename = f"{report_name}.pdf"
                    mime_type = "application/pdf"
                    
                    st.markdown(get_download_link(pdf_data, filename, mime_type), unsafe_allow_html=True)
                    
                    # Sauvegarde dans la BDD
                    db.create_report(user['id'], report_name, report_content, filename)
                    
                    st.success("Rapport généré avec succès!")
                
                elif report_format in ["Excel", "CSV"]:
                    # Export des données
                    df = pd.DataFrame([a for a in selected_data if a])
                    if report_format == "Excel":
                        excel_data = create_excel_export(selected_data)
                        filename = f"{report_name}.xlsx"
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    else:  # CSV
                        csv_data = df.to_csv(index=False).encode()
                        filename = f"{report_name}.csv"
                        mime_type = "text/csv"
                    
                    st.download_button(
                        label=f"Télécharger {filename}",
                        data=excel_data if report_format == "Excel" else csv_data,
                        file_name=filename,
                        mime_type=mime_type
                    )
                    
                    db.create_report(user['id'], report_name, report_content, filename, report_format.lower())
                    st.success("Rapport généré avec succès!")
    
    with tab2:
        st.markdown("### Historique des rapports")
        
        reports = db.get_reports(user['id'])
        
        if reports:
            for report in reports:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{report['name']}**")
                    st.caption(f"Format: {report['format']}")
                with col2:
                    st.caption(f"Créé le {format_timestamp(report['created_at'])}")
                with col3:
                    if report['file_path']:
                        st.caption("📥 Télécharger")
            st.divider()
        else:
            st.info("Aucun rapport généré")

def render_alerts():
    """Page Alertes"""
    st.title("🔔 Gestion des Alertes")
    
    if not auth.is_authenticated():
        st.warning("Veuillez vous connecter pour accéder aux alertes")
        return
    
    user = auth.get_current_user()
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        severity_filter = st.selectbox("Sévérité", ["Toutes", "critical", "high", "medium", "low"])
    with col2:
        status_filter = st.selectbox("Statut", ["Tous", "new", "acknowledged", "resolved"])
    
    # Récupération des alertes
    severity = None if severity_filter == "Toutes" else severity_filter
    status = None if status_filter == "Tous" else status_filter
    
    alerts = db.get_alerts(severity, status)
    
    if alerts:
        for alert in alerts:
            severity = alert['severity']
            icon = get_severity_icon(severity)
            status_color = get_status_color(alert['status'])
            
            with st.container():
                cols = st.columns([1, 4, 1, 1])
                
                with cols[0]:
                    st.markdown(f"{icon} **{severity.upper()}**")
                
                with cols[1]:
                    st.markdown(alert['message'])
                    st.caption(f"Analyse: {alert.get('analysis_id', 'N/A')[:8]}")
                
                with cols[2]:
                    st.markdown(f"*{format_timestamp(alert['created_at'])}*")
                    st.caption(f"Statut: {alert['status']}")
                
                with cols[3]:
                    if alert['status'] == 'new':
                        if st.button("✅ Résoudre", key=f"resolve_{alert['id']}"):
                            db.resolve_alert(alert['id'], user['id'])
                            st.success("Alerte résolue")
                            st.rerun()
                    elif alert['status'] == 'resolved':
                        st.caption(f"Par: {alert.get('resolved_by', 'N/A')}")
                
                st.divider()
    else:
        st.info("Aucune alerte trouvée")

def render_admin():
    """Page Administration"""
    st.title("⚙️ Administration")
    
    if not auth.has_permission("manage_users"):
        st.error("Accès non autorisé")
        return
    
    tab1, tab2, tab3 = st.tabs(["👥 Utilisateurs", "📊 Logs", "⚙️ Configuration"])
    
    with tab1:
        st.markdown("### Gestion des utilisateurs")
        
        users = db.get_all_users()
        
        if users:
            df = pd.DataFrame(users)
            df_display = df[['username', 'email', 'full_name', 'role', 'is_active', 'created_at']].copy()
            df_display['created_at'] = df_display['created_at'].apply(format_timestamp)
            
            st.dataframe(df_display, use_container_width=True)
            
            # Action pour un utilisateur
            col1, col2 = st.columns(2)
            with col1:
                user_to_modify = st.selectbox(
                    "Sélectionner un utilisateur",
                    options=[(u['id'], u['username']) for u in users],
                    format_func=lambda x: x[1]
                )
            
            with col2:
                if user_to_modify:
                    user_id, username = user_to_modify
                    if username != "admin":  # Protection de l'admin
                        new_role = st.selectbox("Nouveau rôle", ["admin", "analyst", "moderator", "observer"])
                        
                        if st.button("Mettre à jour le rôle"):
                            db.update_user(user_id, role=new_role)
                            db.add_log(st.session_state['user']['id'], "update_role", f"Rôle modifié pour {username} -> {new_role}")
                            st.success("Rôle mis à jour")
                            st.rerun()
    
    with tab2:
        st.markdown("### Journal d'audit")
        
        logs = db.get_logs(limit=100)
        
        if logs:
            df_logs = pd.DataFrame(logs)
            df_display = df_logs[['created_at', 'user_id', 'action', 'details']].copy()
            df_display['created_at'] = df_display['created_at'].apply(format_timestamp)
            
            st.dataframe(df_display, use_container_width=True)
            
            # Export des logs
            if st.button("📥 Exporter les logs (CSV)"):
                csv = df_display.to_csv(index=False).encode()
                st.download_button(
                    label="Télécharger",
                    data=csv,
                    file_name=f"logs_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime_type="text/csv"
                )
        else:
            st.info("Aucun log trouvé")
    
    with tab3:
        st.markdown("### Configuration système")
        st.info("Configuration à implémenter dans les futures versions")
        
        # Affichage de la configuration actuelle
        st.markdown("#### Paramètres actuels")
        
        config_data = {
            "Seuils": THRESHOLDS,
            "Rôles": "Liste des rôles disponibles",
            "Langues supportées": len(THRESHOLDS)
        }
        
        st.json(config_data)

# ============ MAIN ============

def main():
    """Fonction principale"""
    
    # Rendu de la sidebar
    render_sidebar()
    
    # Détermination de la page
    page = st.session_state.get('page', 'dashboard')
    
    # Rendu des pages
    if page == 'dashboard':
        render_dashboard()
    elif page == 'analysis':
        render_analysis()
    elif page == 'maps':
        render_maps()
    elif page == 'reports':
        render_reports()
    elif page == 'alerts':
        render_alerts()
    elif page == 'admin':
        render_admin()
    else:
        render_dashboard()
    
    # Footer
    st.markdown("---")
    st.caption(f"{APP_NAME} v{APP_VERSION} - © 2024 - 🕊️ Pour la paix")

if __name__ == "__main__":
    main()