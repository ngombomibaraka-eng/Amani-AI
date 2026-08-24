# ai_engine.py
import re
import json
import random
from datetime import datetime
from typing import Dict, Any, List
import hashlib

# Import des bibliothèques d'IA si disponibles
try:
    import torch
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

class AIEngine:
    """Moteur d'Intelligence Artificielle pour l'analyse de contenu"""
    
    def __init__(self):
        self.models_loaded = False
        self.text_model = None
        self.tokenizer = None
        
        if AI_AVAILABLE:
            self.load_models()
        else:
            print("⚠️ Mode dégradé : les modèles IA ne sont pas disponibles")
    
    def load_models(self):
        """Charge les modèles d'IA"""
        try:
            # Modèle de détection de discours de haine (simplifié)
            model_name = "cardiffnlp/twitter-roberta-base-hate-latest"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.text_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.models_loaded = True
        except Exception as e:
            print(f"Erreur de chargement des modèles: {e}")
            self.models_loaded = False
    
    def analyze_text(self, text: str, language: str = "fr") -> Dict[str, Any]:
        """Analyse un texte pour détecter les problèmes"""
        if not text or len(text.strip()) < 3:
            return {
                "error": "Texte trop court",
                "hate_speech_score": 0.0,
                "violence_score": 0.0,
                "disinformation_score": 0.0,
                "sentiment": "neutre",
                "credibility_score": 50.0,
                "entities": [],
                "language": language
            }
        
        # Si les modèles sont disponibles, utilisation de l'IA
        if self.models_loaded and AI_AVAILABLE:
            return self._analyze_text_ai(text, language)
        
        # Sinon, mode dégradé avec analyse basique
        return self._analyze_text_basic(text, language)
    
    def _analyze_text_ai(self, text: str, language: str) -> Dict[str, Any]:
        """Analyse de texte avec IA réelle"""
        try:
            # Prétraitement
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            # Prédiction
            with torch.no_grad():
                outputs = self.text_model(**inputs)
                scores = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            hate_score = float(scores[0][1])  # Classe hate speech
            
            # Score de violence (basé sur le texte)
            violence_keywords = ['violence', 'attaquer', 'tuer', 'sang', 'arme', 'guerre', 'massacre']
            violence_score = sum(1 for kw in violence_keywords if kw.lower() in text.lower()) / len(violence_keywords)
            violence_score = min(violence_score * 1.5, 1.0)
            
            # Score de désinformation
            disinfo_patterns = [
                r'\bfake\b',
                r'\b(faux|fausse)\b',
                r'\bcomplot\b',
                r'\b(théorie|theorie)\b',
                r'\b(cacher|cache)\b'
            ]
            disinfo_score = sum(1 for pattern in disinfo_patterns if re.search(pattern, text.lower())) / len(disinfo_patterns)
            
            # Sentiment
            sentiment = self._analyze_sentiment(text)
            
            # Entités nommées (simulé)
            entities = self._extract_entities(text)
            
            # Score de crédibilité
            credibility_score = self._calculate_credibility({
                'hate_speech': hate_score,
                'violence': violence_score,
                'disinformation': disinfo_score,
                'sentiment': sentiment,
                'text_length': len(text)
            })
            
            return {
                "hate_speech_score": round(hate_score, 3),
                "violence_score": round(violence_score, 3),
                "disinformation_score": round(disinfo_score, 3),
                "sentiment": sentiment,
                "credibility_score": round(credibility_score, 2),
                "entities": entities,
                "language": language,
                "model_used": "ai"
            }
        except Exception as e:
            return self._analyze_text_basic(text, language, error=str(e))
    
    def _analyze_text_basic(self, text: str, language: str, error: str = None) -> Dict[str, Any]:
        """Analyse de texte basique (fallback)"""
        text_lower = text.lower()
        
        # Mots-clés pour différentes catégories
        hate_keywords = ['haine', 'détester', 'nègre', 'blanc', 'juif', 'musulman', 'chrétien', 'raciste', 'xénophobe']
        violence_keywords = ['violence', 'attaquer', 'tuer', 'sang', 'arme', 'guerre', 'massacre', 'frapper']
        disinfo_keywords = ['fake', 'faux', 'complot', 'théorie', 'cacher', 'manipuler', 'myth']
        
        # Scores
        hate_score = sum(1 for kw in hate_keywords if kw in text_lower) / len(hate_keywords)
        violence_score = sum(1 for kw in violence_keywords if kw in text_lower) / len(violence_keywords)
        disinfo_score = sum(1 for kw in disinfo_keywords if kw in text_lower) / len(disinfo_keywords)
        
        # Normalisation
        hate_score = min(hate_score * 2, 1.0)
        violence_score = min(violence_score * 2, 1.0)
        disinfo_score = min(disinfo_score * 1.5, 1.0)
        
        # Sentiment simple
        if any(word in text_lower for word in ['bon', 'bien', 'excellent', 'génial', 'super']):
            sentiment = "positif"
        elif any(word in text_lower for word in ['mauvais', 'mal', 'terrible', 'horrible', 'nul']):
            sentiment = "négatif"
        else:
            sentiment = "neutre"
        
        # Entités (simulation)
        entities = self._extract_entities(text)
        
        # Score de crédibilité
        credibility_score = self._calculate_credibility({
            'hate_speech': hate_score,
            'violence': violence_score,
            'disinformation': disinfo_score,
            'sentiment': sentiment,
            'text_length': len(text)
        })
        
        result = {
            "hate_speech_score": round(hate_score, 3),
            "violence_score": round(violence_score, 3),
            "disinformation_score": round(disinfo_score, 3),
            "sentiment": sentiment,
            "credibility_score": round(credibility_score, 2),
            "entities": entities,
            "language": language,
            "model_used": "basic"
        }
        
        if error:
            result["error"] = error
        
        return result
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyse le sentiment du texte"""
        # Utilisation d'un modèle simple de sentiment si disponible
        try:
            sentiment_pipeline = pipeline("sentiment-analysis")
            result = sentiment_pipeline(text[:512])[0]
            if result['score'] > 0.6:
                return result['label'].lower()
            return "neutre"
        except:
            # Fallback
            text_lower = text.lower()
            if any(word in text_lower for word in ['bon', 'bien', 'excellent', 'génial', 'super', 'paix']):
                return "positif"
            elif any(word in text_lower for word in ['mauvais', 'mal', 'terrible', 'horrible', 'nul', 'haine']):
                return "négatif"
            return "neutre"
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extrait les entités nommées du texte"""
        entities = []
        
        # Recherche de noms propres (majuscules)
        name_pattern = r'\b[A-Z][a-zà-ÿ]+\s[A-Z][a-zà-ÿ]+\b'
        names = re.findall(name_pattern, text)
        entities.extend([n for n in names if len(n) > 3])
        
        # Recherche de lieux
        place_keywords = ['ville', 'pays', 'région', 'province', 'capital']
        for keyword in place_keywords:
            pattern = r'\b\w+\s+' + keyword + r'\b'
            matches = re.findall(pattern, text.lower())
            entities.extend([m for m in matches if len(m) > 3])
        
        # Recherche d'organisations
        org_pattern = r'\b[A-Z]{2,}\b'
        orgs = re.findall(org_pattern, text)
        entities.extend([o for o in orgs if len(o) > 1])
        
        return list(set(entities))[:5]  # Limiter à 5 entités
    
    def _calculate_credibility(self, scores: Dict[str, Any]) -> float:
        """Calcule le score de crédibilité basé sur plusieurs facteurs"""
        # Poids des facteurs
        weights = {
            'hate_speech': -0.3,  # Score élevé = crédibilité basse
            'violence': -0.3,
            'disinformation': -0.25,
            'sentiment': 0.05,
            'text_length': 0.1
        }
        
        base_score = 50.0
        
        # Ajustement selon les scores
        for key, weight in weights.items():
            if key == 'sentiment':
                # Le sentiment neutre est plus crédible
                if scores.get('sentiment') == 'neutre':
                    base_score += weight * 20
                elif scores.get('sentiment') in ['positif', 'négatif']:
                    base_score += weight * 10
            elif key == 'text_length':
                # Les textes plus longs sont généralement plus crédibles
                length = scores.get(key, 0)
                if length > 100:
                    base_score += weight * 20
                elif length > 50:
                    base_score += weight * 10
            else:
                # Pour hate_speech, violence, disinformation
                score_value = scores.get(key, 0)
                base_score += weight * (score_value * 100)
        
        # Limitation
        base_score = max(0, min(100, base_score))
        
        # Arrondi
        return round(base_score, 2)
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyse une image pour détecter des problèmes"""
        # Simulé - en production, utiliser des modèles de vision
        results = {
            "violence_detected": random.random() > 0.85,
            "hate_symbols": random.random() > 0.9,
            "faces_detected": random.randint(0, 10),
            "ocr_text": "Texte extrait de l'image (simulé)",
            "metadata": {
                "width": 1920,
                "height": 1080,
                "format": "JPEG"
            },
            "credibility_score": round(random.uniform(40, 80), 2)
        }
        return results
    
    def analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """Analyse un fichier audio"""
        # Simulé - en production, utiliser Whisper
        results = {
            "transcript": "Ceci est une transcription simulée du fichier audio",
            "emotions": {
                "anger": random.random() * 100,
                "fear": random.random() * 100,
                "joy": random.random() * 100,
                "sadness": random.random() * 100
            },
            "language": "fr",
            "credibility_score": round(random.uniform(40, 80), 2)
        }
        return results
    
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """Analyse une vidéo"""
        # Simulé
        results = {
            "frame_count": 100,
            "violence_detected": random.random() > 0.8,
            "crowd_detected": random.random() > 0.7,
            "scene_changes": random.randint(5, 20),
            "credibility_score": round(random.uniform(40, 80), 2)
        }
        return results
    
    def detect_language(self, text: str) -> str:
        """Détecte la langue du texte"""
        # Simulé - en production, utiliser FastText ou langdetect
        try:
            from langdetect import detect
            return detect(text)
        except:
            # Simple détection basée sur des mots-clés
            french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles']
            english_words = ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'you', 'he', 'she', 'we', 'they']
            
            text_lower = text.lower()
            fr_count = sum(1 for w in french_words if w in text_lower)
            en_count = sum(1 for w in english_words if w in text_lower)
            
            if fr_count > en_count:
                return "fr"
            elif en_count > fr_count:
                return "en"
            else:
                return "fr"  # Par défaut