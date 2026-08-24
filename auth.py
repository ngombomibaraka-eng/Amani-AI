# auth.py
import streamlit as st
import hashlib
import jwt
from datetime import datetime, timedelta
from config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import Database

class AuthManager:
    """Gestionnaire d'authentification"""
    
    def __init__(self):
        self.db = Database()
    
    def login(self, username: str, password: str) -> bool:
        """Authentifie un utilisateur"""
        user = self.db.get_user_by_username(username)
        
        if not user:
            return False
        
        # Vérification du mot de passe
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user['password_hash'] != password_hash:
            return False
        
        if not user['is_active']:
            return False
        
        # Mise à jour de la dernière connexion
        self.db.update_last_login(user['id'])
        
        # Création du token JWT
        token = self.create_token(user['id'], user['username'], user['role'])
        
        # Stockage dans la session
        st.session_state['user'] = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'full_name': user['full_name'],
            'role': user['role']
        }
        st.session_state['token'] = token
        st.session_state['logged_in'] = True
        
        # Log de connexion
        self.db.add_log(user['id'], "login", "Connexion réussie")
        
        return True
    
    def logout(self):
        """Déconnecte l'utilisateur"""
        if 'user' in st.session_state:
            self.db.add_log(st.session_state['user']['id'], "logout", "Déconnexion")
        
        st.session_state.clear()
        st.rerun()
    
    def create_token(self, user_id: str, username: str, role: str) -> str:
        """Crée un token JWT"""
        payload = {
            'sub': user_id,
            'username': username,
            'role': role,
            'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> dict:
        """Vérifie un token JWT"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user(self):
        """Récupère l'utilisateur actuel"""
        if 'user' in st.session_state and st.session_state.get('logged_in', False):
            return st.session_state['user']
        return None
    
    def is_authenticated(self) -> bool:
        """Vérifie si l'utilisateur est authentifié"""
        return 'logged_in' in st.session_state and st.session_state['logged_in']
    
    def has_permission(self, permission: str) -> bool:
        """Vérifie les permissions de l'utilisateur"""
        if not self.is_authenticated():
            return False
        
        user = self.get_current_user()
        role = user.get('role', 'observer')
        
        from config import ROLES
        if role in ROLES:
            if '*' in ROLES[role] or permission in ROLES[role]:
                return True
        
        return False
    
    def require_auth(self):
        """Décore une fonction pour exiger l'authentification"""
        if not self.is_authenticated():
            st.error("Veuillez vous connecter pour accéder à cette page")
            st.stop()
        return self.get_current_user()
    
    def require_role(self, role: str):
        """Décore une fonction pour exiger un rôle spécifique"""
        user = self.require_auth()
        if user['role'] != role and user['role'] != 'admin':
            st.error("Permission insuffisante")
            st.stop()
        return user
    
    def register_user(self, username: str, email: str, password: str, full_name: str, role: str = "observer") -> bool:
        """Inscrit un nouvel utilisateur"""
        user_id = self.db.create_user(username, email, password, full_name, role)
        if user_id:
            self.db.add_log(user_id, "register", f"Inscription réussie avec le rôle {role}")
            return True
        return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change le mot de passe d'un utilisateur"""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return False
        
        old_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if user['password_hash'] != old_hash:
            return False
        
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        success = self.db.update_user(user_id, password_hash=new_hash)
        
        if success:
            self.db.add_log(user_id, "change_password", "Mot de passe modifié")
        
        return success
    
    def list_users(self):
        """Liste tous les utilisateurs (admin seulement)"""
        if self.has_permission("manage_users"):
            return self.db.get_all_users()
        return None