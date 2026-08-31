# config.py
import os
from datetime import timedelta

# Configuration de l'application
APP_NAME = "Amani AI - Détection de Conflits"
APP_VERSION = "1.0.0"

# Base de données
DATABASE_URL = "sqlite:///amani_ai.db"
DB_FILE = "amani_ai.db"

# Sécurité
JWT_SECRET_KEY = "votre_clé_secrète_ultra_sécurisée_à_changer_en_production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Session
SESSION_EXPIRY = timedelta(days=1)

# Analyse
MAX_TEXT_LENGTH = 5000
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

# Seuils de détection
THRESHOLDS = {
    "hate_speech": 0.6,
    "violence": 0.7,
    "disinformation": 0.5,
    "credibility": 0.5
}

# Rôles et permissions
ROLES = {
    "admin": ["*"],
    "analyst": ["analyse", "reports", "dashboard"],
    "moderator": ["analyse", "alerts", "dashboard"],
    "observer": ["dashboard", "maps"]
}

# Langues supportées
SUPPORTED_LANGUAGES = [
    "fr", "en", "ar", "sw", "ln", "kg", "rw", "yo", "ha", "zu"
]

# Messages d'erreur
ERROR_MESSAGES = {
    "auth_failed": "Identifiants incorrects",
    "unauthorized": "Accès non autorisé",
    "not_found": "Ressource non trouvée",
    "invalid_input": "Données invalides",
    "server_error": "Erreur serveur",
    "rate_limit": "Trop de requêtes, veuillez patienter"
}

# Configuration des alertes
ALERT_LEVELS = {
    "low": {"color": "info", "score": 0.3},
    "medium": {"color": "warning", "score": 0.6},
    "high": {"color": "danger", "score": 0.8},
    "critical": {"color": "critical", "score": 0.95}
}