import streamlit as st
import pandas as pd
import io
import base64
from datetime import datetime
import json
import hashlib
from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_report_pdf(content: Dict[str, Any], filename: str = "report.pdf") -> bytes:
    """Génère un rapport PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a5276')
    )
    story.append(Paragraph("Rapport Amani AI", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Date
    story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Résumé
    story.append(Paragraph("Résumé de l'analyse", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    if 'content' in content:
        story.append(Paragraph(f"Contenu analysé: {content['content'][:200]}...", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    # Scores
    if 'scores' in content:
        story.append(Paragraph("Scores de détection", styles['Heading2']))
        data = []
        for key, value in content['scores'].items():
            data.append([key.replace('_', ' ').title(), f"{value:.2f}%"])
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2*inch))
    
    # Recommandations
    story.append(Paragraph("Recommandations", styles['Heading2']))
    recommendations = content.get('recommendations', [
        "Surveiller les sources de ce contenu",
        "Vérifier les faits auprès de sources fiables",
        "Documenter l'analyse pour référence future"
    ])
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", styles['Normal']))
    
    # Construction du PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def create_excel_export(analyses: List[Dict]) -> bytes:
    """Crée un export Excel"""
    df = pd.DataFrame(analyses)
    
    # Nettoyage des données
    if 'result' in df.columns:
        df['result'] = df['result'].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Analyses')
    
    buffer.seek(0)
    return buffer.getvalue()

def create_dashboard_charts(stats: Dict[str, Any]):
    """Crée les graphiques du dashboard"""
    
    # 1. Analyses par type
    if 'analyses_by_type' in stats and stats['analyses_by_type']:
        fig1 = go.Figure(data=[
            go.Pie(
                labels=list(stats['analyses_by_type'].keys()),
                values=list(stats['analyses_by_type'].values()),
                hole=.3,
                marker=dict(colors=['#3498db', '#e74c3c', '#2ecc71', '#f39c12'])
            )
        ])
        fig1.update_layout(
            title="Analyses par type",
            height=350,
            showlegend=True
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    # 2. Alertes par sévérité
    if 'alerts_by_severity' in stats and stats['alerts_by_severity']:
        severity_colors = {
            'critical': '#e74c3c',
            'high': '#f39c12',
            'medium': '#f1c40f',
            'low': '#3498db'
        }
        
        fig2 = go.Figure(data=[
            go.Bar(
                x=list(stats['alerts_by_severity'].keys()),
                y=list(stats['alerts_by_severity'].values()),
                marker_color=[severity_colors.get(s, '#95a5a6') for s in stats['alerts_by_severity'].keys()]
            )
        ])
        fig2.update_layout(
            title="Alertes par sévérité",
            height=350,
            xaxis_title="Sévérité",
            yaxis_title="Nombre d'alertes"
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # 3. Distribution des scores
    st.subheader("Distribution des scores de crédibilité")
    # Graphique simulé
    import numpy as np
    scores = np.random.normal(65, 20, 100)
    scores = np.clip(scores, 0, 100)
    
    fig3 = go.Figure(data=[
        go.Histogram(
            x=scores,
            nbinsx=20,
            marker_color='#3498db'
        )
    ])
    fig3.update_layout(
        height=300,
        xaxis_title="Score de crédibilité",
        yaxis_title="Fréquence"
    )
    st.plotly_chart(fig3, use_container_width=True)

def display_metrics(user_count: int, analysis_count: int, alert_count: int, avg_score: float):
    """Affiche les métriques KPI"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="👥 Utilisateurs",
            value=user_count,
            delta="Actifs"
        )
    
    with col2:
        st.metric(
            label="📊 Analyses",
            value=analysis_count,
            delta="Total"
        )
    
    with col3:
        st.metric(
            label="🔔 Alertes",
            value=alert_count,
            delta="En cours"
        )
    
    with col4:
        st.metric(
            label="📈 Score moyen",
            value=f"{avg_score:.1f}%",
            delta="Crédibilité"
        )

def hash_file_content(content: str) -> str:
    """Génère un hash du contenu"""
    return hashlib.sha256(content.encode()).hexdigest()

def get_download_link(data: bytes, filename: str, mime_type: str) -> str:
    """Génère un lien de téléchargement"""
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">Télécharger {filename}</a>'

def validate_email(email: str) -> bool:
    """Valide un email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_timestamp(timestamp_str: str) -> str:
    """Formate un timestamp"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return timestamp_str

def get_status_color(status: str) -> str:
    """Retourne la couleur du statut"""
    colors = {
        'pending': '#f39c12',
        'processing': '#3498db',
        'completed': '#2ecc71',
        'failed': '#e74c3c',
        'new': '#e74c3c',
        'acknowledged': '#f39c12',
        'resolved': '#2ecc71'
    }
    return colors.get(status, '#95a5a6')

def get_severity_icon(severity: str) -> str:
    """Retourne l'icône de sévérité"""
    icons = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🔵'
    }
    return icons.get(severity, '⚪')

def truncate_text(text: str, max_length: int = 100) -> str:
    """Tronque un texte"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'

def safe_json_parse(json_str: str) -> Dict:
    """Parse un JSON de manière sécurisée"""
    try:
        return json.loads(json_str)
    except:
        return {}

def create_sentiment_chart(sentiment_data: Dict):
    """Crée un graphique de sentiment"""
    if not sentiment_data:
        return
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(sentiment_data.keys()),
            y=list(sentiment_data.values()),
            marker_color=['#2ecc71', '#f1c40f', '#e74c3c']
        )
    ])
    fig.update_layout(
        title="Répartition des sentiments",
        height=300,
        xaxis_title="Sentiment",
        yaxis_title="Nombre"
    )
    st.plotly_chart(fig, use_container_width=True)