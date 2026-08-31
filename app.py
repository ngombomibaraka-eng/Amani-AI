import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image

from config import APP_NAME, APP_VERSION, THRESHOLDS
from database import Database
from auth import AuthManager
from ai_engine import AIEngine
from utils import (
    create_dashboard_charts, format_timestamp,
    get_severity_icon, truncate_text
)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

db = Database()
auth = AuthManager()
ai_engine = AIEngine()

# ==================== SIDEBAR ====================
def render_sidebar():
    with st.sidebar:
        st.title("🕊️ AMANI AI")
        st.caption(f"{APP_NAME} v{APP_VERSION}")
        st.caption("Hub Tech DRC - Goma 2026")
        st.divider()

        if auth.is_authenticated():
            user = auth.get_current_user()
            with st.container(border=True):
                st.markdown(f"👤 **{user.get('full_name', user.get('username'))}**")
                st.badge(f"{user.get('role', 'observer').upper()}", color="blue")

            st.subheader("Navigation")
            menu = {
                "🏠 Tableau de bord": "dashboard",
                "📝 Analyse IA": "analysis",
                "🗺️ Cartographie": "maps",
                "📊 Rapports": "reports",
                "🔔 Alertes": "alerts"
            }
            if auth.has_permission("manage_users"):
                menu["⚙️ Administration"] = "admin"

            sel = st.radio("Aller vers", list(menu.keys()), label_visibility="collapsed")
            st.session_state['page'] = menu[sel]
            st.divider()
            # ✅ Correction 1: use_container_width -> width
            if st.button("🚪 Déconnexion", width="stretch"):
                auth.logout()
                st.rerun()
        else:
            st.subheader("🔐 Espace Membre")
            tab1, tab2 = st.tabs(["Connexion", "Inscription"])
            with tab1: login_form()
            with tab2: register_form()

            st.divider()
            with st.container(border=True):
                st.markdown("**Pourquoi nous rejoindre?**")
                st.markdown("✅ 1200+ observateurs actifs")
                st.markdown("✅ 5 langues locales")
                st.markdown("✅ 100% gratuit")

def login_form():
    with st.form("login_form"):
        u = st.text_input("Nom d'utilisateur")
        p = st.text_input("Mot de passe", type="password")
        # ✅ Correction 2: use_container_width -> width
        if st.form_submit_button("Se connecter", type="primary", width="stretch"):
            if auth.login(u, p):
                st.success("Connexion réussie!")
                st.rerun()
            else:
                st.error("Identifiants incorrects")

def register_form():
    with st.form("register_form"):
        username = st.text_input("Nom d'utilisateur *")
        email = st.text_input("Email *")
        full_name = st.text_input("Nom complet")
        password = st.text_input("Mot de passe", type="password")
        role = st.selectbox("Je suis", ["observer", "analyst", "moderator"])
        # ✅ Correction 3: use_container_width -> width
        if st.form_submit_button("Créer mon compte", width="stretch"):
            if auth.register_user(username, email, password, full_name, role):
                st.success("Compte créé! Connectez-vous.")
            else:
                st.error("Utilisateur existe déjà")

# ==================== PAGE D'ACCUEIL PRO AVEC VRAIES DONNEES ====================
def render_landing_page():
    stats = db.get_statistics()
    total_analyses = stats.get('total_analyses', 0)
    active_alerts = stats.get('active_alerts', 0)
    total_users = stats.get('total_users', 0)
    avg_score = stats.get('average_score', 0)
    recent_analyses = db.get_all_analyses(limit=4)
    recent_alerts = db.get_alerts(limit=3)

    with st.container(border=True):
        col1, col2 = st.columns([2, 1], vertical_alignment="center")
        with col1:
            st.title("🕊️ La désinformation divise. Amani AI rassemble.")
            st.subheader(f"Première plateforme IA de lutte contre la haine en RDC.")
            st.markdown(
                f"Développée à Goma par Hub Tech DRC. Notre système a déjà analysé **{total_analyses} contenus** "
                f"grâce à **{total_users} observateurs**. Notre mission : protéger la vérité."
            )
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                # ✅ Correction 4: use_container_width -> width
                st.button("🚀 Commencer l'analyse", type="primary", width="stretch")
            with c2:
                st.button("📖 Comment ça marche?", width="stretch")
        with col2:
            with st.container(border=True):
                st.markdown("**🎯 Impact en direct**")
                st.metric("Contenus analysés", f"{total_analyses}", delta="données réelles")
                st.metric("Alertes actives", f"{active_alerts}", delta="à traiter", delta_color="inverse")
                st.metric("Score moyen", f"{avg_score:.1f}%")
                if total_analyses > 0:
                    st.progress(int(avg_score), text="Fiabilité globale")
                else:
                    st.progress(0, text="En attente de premières analyses")

    st.subheader("📊 État du système - Données réelles")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📝 Total Analyses", total_analyses)
    m2.metric("🔔 Alertes Actives", active_alerts)
    m3.metric("👥 Observateurs", total_users)
    m4.metric("🎯 Crédibilité", f"{avg_score:.1f}%")

    st.divider()

    left, right = st.columns([1.6, 1], gap="large")

    with left:
        st.subheader("💡 3 Piliers de la plateforme")
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True):
                st.markdown("#### 🧠 1. Détecter")
                st.markdown("Module `AIEngine`")
                st.markdown("- `analyze_text()`")
                st.markdown("- `analyze_image()`")
                st.markdown("- `analyze_audio()`")
                st.info("5 langues: FR, EN, SW, LN, AR")
        with c2:
            with st.container(border=True):
                st.markdown("#### 🗺️ 2. Cartographier")
                st.markdown("Module `Database`")
                st.markdown("- `get_alerts()`")
                st.markdown("- `get_statistics()`")
                st.markdown("- Carte Folium")
                st.warning("Foyers: Goma, Bukavu, Bujumbura")
        with c3:
            with st.container(border=True):
                st.markdown("#### 📄 3. Agir")
                st.markdown("Module `utils`")
                st.markdown("- `generate_report_pdf()`")
                st.markdown("- `create_excel_export()`")
                st.success("Preuves pour ONG & Médias")

        st.divider()
        st.subheader("⚙️ Flux de l'application vu en cours")
        with st.container(border=True):
            s1, s2, s3, s4 = st.columns(4)
            s1.markdown("**1. AUTH**\n\n`AuthManager`\n`login()`\n`register_user()`")
            s2.markdown("**2. ANALYSE**\n\n`AIEngine`\nScore 0-100%\n`THRESHOLDS`")
            s3.markdown("**3. BDD**\n\n`Database`\n`create_analysis()`\n`create_alert()`")
            s4.markdown("**4. UI**\n\n`Streamlit`\n`st.metric`\n`st.dataframe`")

    with right:
        with st.container(border=True):
            st.subheader("🔴 Activité en direct")
            st.caption("Données issues de votre SQLite")

            if recent_analyses:
                st.markdown("**Dernières analyses :**")
                for a in recent_analyses:
                    score = a.get('score', 0)
                    if score < 40:
                        st.error(f"🚨 {a['content_type'].upper()} | {score:.0f}% | {format_timestamp(a['created_at'])}")
                    elif score < 70:
                        st.warning(f"⚠️ {a['content_type'].upper()} | {score:.0f}% | {format_timestamp(a['created_at'])}")
                    else:
                        st.success(f"✅ {a['content_type'].upper()} | {score:.0f}% | {format_timestamp(a['created_at'])}")
            else:
                st.info("Aucune analyse enregistrée. Soyez le premier à tester le système!", icon="👋")
                st.markdown("Allez dans **📝 Analyse IA** pour coller un texte suspect.")

            st.divider()

            if recent_alerts:
                st.markdown("**Dernières alertes :**")
                for alert in recent_alerts:
                    st.markdown(f"{get_severity_icon(alert['severity'])} **{alert['severity'].upper()}** - {truncate_text(alert['message'], 60)}")
                    st.caption(format_timestamp(alert['created_at']))
            else:
                st.success("Aucune alerte critique. Système calme.", icon="🕊️")

            st.divider()
            # ✅ Correction 5: use_container_width -> width
            st.button("👉 Créer mon compte gratuit", type="primary", width="stretch")
            st.caption("Gratuit • Sécurisé • Fait à Goma")

# ==================== DASHBOARD CONNECTÉ AVEC VRAIES DONNEES ====================
def render_dashboard():
    if not auth.is_authenticated():
        render_landing_page()
        return

    user = auth.get_current_user()
    stats = db.get_statistics()

    st.title(f"Bon retour, {user.get('full_name', user.get('username')).split()[0]} 👋")
    st.caption(f"Bienvenue sur {APP_NAME} - Détecteur de désinformation")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📝 Analyses", stats.get('total_analyses', 0), delta="Aujourd'hui")
    m2.metric("🔔 Alertes", stats.get('active_alerts', 0), delta="Actives", delta_color="inverse")
    m3.metric("🎯 Score Moyen", f"{stats.get('average_score', 0):.1f}%")
    m4.metric("👥 Utilisateurs", stats.get('total_users', 0))

    st.divider()

    col_g, col_d = st.columns([2, 1.2])
    with col_g:
        with st.container(border=True):
            st.subheader("📈 Tendances de détection")
            create_dashboard_charts(stats)

    with col_d:
        with st.container(border=True):
            st.subheader("📋 Analyses récentes")
            recent = db.get_all_analyses(limit=5)
            if recent:
                df = pd.DataFrame(recent)
                st.dataframe(df[['created_at', 'content_type', 'score', 'status']], use_container_width=True, hide_index=True)
            else:
                st.info("Aucune donnée")

        with st.container(border=True):
            st.subheader("🔔 Alertes")
            alerts = db.get_alerts(limit=3)
            if alerts:
                for alert in alerts:
                    st.markdown(f"{get_severity_icon(alert['severity'])} {alert['severity'].upper()} - {truncate_text(alert['message'], 50)}")
                    if alert['status'] == 'new':
                        # ✅ Correction 6: use_container_width -> width
                        if st.button("Résoudre", key=f"d_{alert['id']}", width="stretch"):
                            db.resolve_alert(alert['id'], user['id'])
                            st.rerun()
            else:
                st.success("Aucune alerte")

# ==================== PAGES ANALYSE COMPLÈTES ====================
def render_analysis():
    st.title("📝 Centre d'Analyse IA")
    st.markdown("Soumettez un contenu. L'IA analyse en 3 secondes.")
    if not auth.is_authenticated():
        st.warning("Connectez-vous")
        return
    user = auth.get_current_user()
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Texte", "🖼️ Image", "🎵 Audio", "🎬 Vidéo"])
    with tab1: render_text_analysis(user)
    with tab2: render_image_analysis(user)
    with tab3: render_audio_analysis(user)
    with tab4: render_video_analysis(user)

def render_text_analysis(user):
    with st.container(border=True):
        st.subheader("Analyse de texte")
        text = st.text_area("Entrez le texte", height=180, placeholder="Collez le texte ici...")
        lang = st.selectbox("Langue", ["fr", "en", "ar", "sw", "ln"])
        # ✅ Correction 7: use_container_width -> width
        if st.button("🔍 Analyser le texte", type="primary", width="stretch") and text:
            if len(text) < 10:
                st.warning("Texte trop court")
                return
            with st.spinner("Analyse avec AIEngine.analyze_text()..."):
                aid = db.create_analysis(user['id'], "text", text[:500])
                res = ai_engine.analyze_text(text, lang)
                db.update_analysis_result(aid, res, res.get('credibility_score', 50))
                display_analysis_results(res, "text")
                check_and_create_alerts(aid, res)

def render_image_analysis(user):
    with st.container(border=True):
        st.subheader("Analyse d'image")
        f = st.file_uploader("Image", type=['jpg', 'jpeg', 'png'])
        if f:
            # ✅ Correction 8: use_container_width -> width
            st.image(f, width=400)
            # ✅ Correction 9: use_container_width -> width
            if st.button("🔍 Analyser l'image", type="primary", width="stretch"):
                path = f"/tmp/{f.name}"
                with open(path, "wb") as out: out.write(f.getbuffer())
                aid = db.create_analysis(user['id'], "image", file_path=path)
                res = ai_engine.analyze_image(path)
                db.update_analysis_result(aid, res, res.get('credibility_score', 50))
                display_analysis_results(res, "image")

def render_audio_analysis(user):
    with st.container(border=True):
        st.subheader("Analyse audio")
        f = st.file_uploader("Audio", type=['mp3', 'wav', 'm4a'])
        if f:
            st.audio(f)
            # ✅ Correction 10: use_container_width -> width
            if st.button("🔍 Analyser l'audio", type="primary", width="stretch"):
                path = f"/tmp/{f.name}"
                with open(path, "wb") as out: out.write(f.getbuffer())
                aid = db.create_analysis(user['id'], "audio", file_path=path)
                res = ai_engine.analyze_audio(path)
                db.update_analysis_result(aid, res, res.get('credibility_score', 50))
                display_analysis_results(res, "audio")

def render_video_analysis(user):
    with st.container(border=True):
        st.subheader("Analyse vidéo")
        f = st.file_uploader("Vidéo", type=['mp4', 'avi', 'mov'])
        if f:
            st.video(f)
            # ✅ Correction 11: use_container_width -> width
            if st.button("🔍 Analyser la vidéo", type="primary", width="stretch"):
                path = f"/tmp/{f.name}"
                with open(path, "wb") as out: out.write(f.getbuffer())
                aid = db.create_analysis(user['id'], "video", file_path=path)
                res = ai_engine.analyze_video(path)
                db.update_analysis_result(aid, res, res.get('credibility_score', 50))
                display_analysis_results(res, "video")

def display_analysis_results(result, ctype):
    st.divider()
    st.subheader("📊 Résultats")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Haine", f"{result.get('hate_speech_score', 0):.2f}")
    c2.metric("Violence", f"{result.get('violence_score', 0):.2f}")
    c3.metric("Désinfo", f"{result.get('disinformation_score', 0):.2f}")
    c4.metric("Crédibilité", f"{result.get('credibility_score', 0):.1f}%")
    if result.get('sentiment'):
        st.info(f"Sentiment: {result.get('sentiment')}")
    with st.expander("Voir JSON complet du résultat (dict retourné par AIEngine)"):
        st.json(result)

def check_and_create_alerts(aid, result):
    if result.get('hate_speech_score', 0) > THRESHOLDS['hate_speech']:
        db.create_alert(aid, "high", f"Haine détectée: {result['hate_speech_score']:.2f}")
    if result.get('violence_score', 0) > THRESHOLDS['violence']:
        db.create_alert(aid, "critical", f"Violence: {result['violence_score']:.2f}")
    if result.get('disinformation_score', 0) > THRESHOLDS['disinformation']:
        db.create_alert(aid, "medium", f"Désinfo: {result['disinformation_score']:.2f}")

def render_maps():
    st.title("🗺️ Cartographie des tendances")
    if not auth.is_authenticated():
        st.warning("Connectez-vous")
        return
    with st.container(border=True):
        st.subheader("Carte des foyers - Données réelles de get_alerts()")
        try:
            import folium
            # ✅ Correction 12: remplacer folium_static par st_folium
            from streamlit_folium import st_folium
            m = folium.Map(location=[-1.6585, 29.2205], zoom_start=5)
            alerts = db.get_alerts(limit=20)
            for alert in alerts:
                folium.Marker([-1.6585, 29.2205], popup=alert['message'][:50]).add_to(m)
            # ✅ Correction : st_folium au lieu de folium_static
            st_folium(m, width=1100, height=500, returned_objects=[])
        except ImportError:
            st.info("Installez folium et streamlit-folium pour voir la carte")
            st.code("pip install folium streamlit-folium")
        except Exception as e:
            st.error(f"Erreur : {e}")

def render_reports():
    st.title("📊 Rapports")
    if not auth.is_authenticated():
        st.warning("Connectez-vous")
        return
    user = auth.get_current_user()
    with st.container(border=True):
        st.subheader("Générer un rapport avec vos vraies analyses")
        analyses = db.get_user_analyses(user['id'])
        if not analyses:
            st.info("Aucune analyse. Faites d'abord une analyse.")
            return
        df = pd.DataFrame(analyses)
        st.dataframe(df, use_container_width=True)
        # ✅ Correction 13: use_container_width -> width
        st.button("📥 Exporter en PDF (generate_report_pdf)", type="primary", width="stretch")

def render_alerts():
    st.title("🔔 Alertes")
    if not auth.is_authenticated():
        st.warning("Connectez-vous")
        return
    alerts = db.get_alerts()
    if alerts:
        for alert in alerts:
            with st.container(border=True):
                st.markdown(f"{get_severity_icon(alert['severity'])} **{alert['severity'].upper()}** - {alert['message']}")
                st.caption(format_timestamp(alert['created_at']))
    else:
        st.success("Aucune alerte - Système calme", icon="🕊️")

def render_admin():
    st.title("⚙️ Administration")
    if not auth.has_permission("manage_users"):
        st.error("Accès admin uniquement")
        return
    users = db.get_all_users()
    with st.container(border=True):
        st.subheader(f"Utilisateurs enregistrés : {len(users)}")
        st.dataframe(pd.DataFrame(users), use_container_width=True)

def main():
    render_sidebar()
    page = st.session_state.get('page', 'dashboard')
    if page == 'dashboard': render_dashboard()
    elif page == 'analysis': render_analysis()
    elif page == 'maps': render_maps()
    elif page == 'reports': render_reports()
    elif page == 'alerts': render_alerts()
    elif page == 'admin': render_admin()
    st.divider()
    st.caption(f"{APP_NAME} v{APP_VERSION} - © 2026 Hub Tech DRC - Travail Pratique Python Streamlit - Fait à Goma")

if __name__ == "__main__":
    main()