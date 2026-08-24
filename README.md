# 🕊️ AMANI AI - Système de Détection et Prévention des Conflits par Intelligence Artificielle

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/votre-repo/amani-ai)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28.0-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Table des Matières

- [Aperçu du Projet](#aperçu-du-projet)
- [Fonctionnalités Principales](#fonctionnalités-principales)
- [Architecture Technique](#architecture-technique)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Démarrage Rapide](#démarrage-rapide)
- [Guide d'Utilisation](#guide-dutilisation)
- [Structure des Données](#structure-des-données)
- [API et Intégration](#api-et-intégration)
- [Sécurité](#sécurité)
- [Tests](#tests)
- [Déploiement](#déploiement)
- [Dépannage](#dépannage)
- [Contribuer](#contribuer)
- [Roadmap](#roadmap)
- [Licence](#licence)
- [Contact](#contact)

---

## 🌍 Aperçu du Projet

**AMANI AI** (signifiant "Paix" en swahili) est un système intelligent de détection et prévention des conflits, conçu pour analyser automatiquement les contenus numériques (texte, image, audio, vidéo) et identifier les signes précurseurs de violence, de discours de haine et de désinformation.

### 🎯 Mission

Contribuer à la paix et à la stabilité sociale en fournissant aux institutions (gouvernements, ONG, médias) un outil d'alerte précoce basé sur l'intelligence artificielle.

### 👥 Public Cible

- **Analystes** : Recherche et analyse approfondie
- **Modérateurs** : Validation et correction des alertes
- **Administrateurs** : Gestion du système et des utilisateurs
- **Observateurs** : Consultation du tableau de bord
- **ONG et Institutions** : Veille stratégique

### 🔑 Caractéristiques Uniques

- **Multimodal** : Analyse de 4 types de contenus (texte, image, audio, vidéo)
- **Multilingue** : Support de 10 langues africaines et internationales
- **Temps Réel** : Détection et alertes instantanées
- **Explicable** : Scores de crédibilité avec justifications
- **Modulaire** : Architecture microservices prête pour l'échelle

---

## ⚡ Fonctionnalités Principales

### 1. Analyse de Contenu

| Type | Fonctionnalités | Technologies |
|------|----------------|--------------|
| 📝 **Texte** | • Détection hate speech<br>• Incitation à la violence<br>• Désinformation<br>• Analyse de sentiment<br>• Extraction d'entités | XLM-RoBERTa, AfriBERTa |
| 🖼️ **Image** | • Détection d'objets violents<br>• Symboles haineux<br>• OCR (texte dans l'image)<br>• Métadonnées EXIF | YOLOv8, CLIP, EasyOCR |
| 🎵 **Audio** | • Transcription automatique<br>• Détection d'émotions<br>• Identification de la langue | Whisper, Wav2Vec2 |
| 🎬 **Vidéo** | • Analyse frame par frame<br>• Détection de foule<br>• Violence en mouvement | TimeSformer, OpenCV |

### 2. Système d'Alertes

- **Alertes automatiques** : Basées sur des seuils configurables
- **Niveaux de sévérité** : Critique, Élevé, Moyen, Bas
- **Notifications** : Dans l'application + futures intégrations (email, SMS)
- **Gestion** : Visualisation, résolution, historique

### 3. Score de Crédibilité

Le système attribue un score de 0 à 100 basé sur 8 facteurs pondérés :

| Facteur | Poids | Description |
|---------|-------|-------------|
| Réputation de la source | 20% | Historique de la source |
| Authenticité du contenu | 15% | Analyse de l'authenticité |
| Cohérence des métadonnées | 15% | Vérification des métadonnées |
| Recoupement | 15% | Recherche inversée |
| Cohérence du sentiment | 10% | Analyse des émotions |
| Cohérence factuelle | 15% | Vérification des faits |
| Pertinence contextuelle | 5% | Contexte de l'information |
| Historique des motifs | 5% | Analyse des tendances |

### 4. Tableau de Bord

- **KPIs** : Utilisateurs, analyses, alertes, scores
- **Graphiques** : Distribution, tendances, répartition
- **Analyses récentes** : Liste des derniers contenus analysés
- **Alertes actives** : Vue d'ensemble des menaces

### 5. Cartographie Interactive

- Carte mondiale des tensions
- Visualisation des zones à risque
- Statistiques par région
- Filtrage par type d'incident

### 6. Rapports et Exports

- **PDF** : Rapports professionnels personnalisés
- **Excel/CSV** : Export complet des données
- **Historique** : Conservation de tous les rapports

### 7. Gestion des Utilisateurs

- **Rôles** : Admin, Analyst, Moderator, Observer
- **Permissions** : Contrôle d'accès granulaire
- **Journal d'audit** : Traçabilité des actions

---

## 🏗️ Architecture Technique

### Stack Technologique

```mermaid
graph TB
    subgraph Frontend
        A[Streamlit UI]
        B[Plotly Charts]
        C[Folium Maps]
    end
    
    subgraph Backend
        D[Auth Manager]
        E[AI Engine]
        F[Database Layer]
        G[Utils Module]
    end
    
    subgraph Data
        H[SQLite3]
        I[File Storage]
    end
    
    A --> D
    A --> E
    A --> F
    A --> G
    E --> H
    F --> H


    <!-- A INSTALLER  -->
    # Assurez-vous que pip est à jour
python -m pip install --upgrade pip

# Installation de Streamlit et des dépendances principales
pip install streamlit pandas numpy plotly

# Installation des dépendances pour les rapports
pip install reportlab openpyxl pillow

# Installation pour la cartographie
pip install folium streamlit-folium

# Installation pour l'IA (si vous voulez les modèles complets)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers langdetect

# Installation des utilitaires
pip install python-dotenv

# Vérification de l'installation
pip list | findstr streamlit