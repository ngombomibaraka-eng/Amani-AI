# database.py
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import hashlib
import uuid

class Database:
    """Gestionnaire de base de données SQLite3"""
    
    def __init__(self, db_file="amani_ai.db"):
        self.db_file = db_file
        self.init_database()
    
    def get_connection(self):
        """Crée une connexion à la base de données"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialise toutes les tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'observer',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Table analyses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content TEXT,
                file_path TEXT,
                result TEXT,
                score REAL,
                status TEXT DEFAULT 'pending',
                language TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                resolved_by TEXT,
                FOREIGN KEY (analysis_id) REFERENCES analyses (id),
                FOREIGN KEY (resolved_by) REFERENCES users (id)
            )
        ''')
        
        # Table reports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                content TEXT,
                file_path TEXT,
                format TEXT DEFAULT 'pdf',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Table configurations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configurations (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Création de l'admin par défaut
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(uuid.uuid4()), "admin", "admin@amani.ai", admin_password, "Administrateur", "admin"))
        
        conn.commit()
        conn.close()
    
    # ============ USER OPERATIONS ============
    
    def create_user(self, username: str, email: str, password: str, full_name: str = "", role: str = "observer") -> Optional[str]:
        """Crée un nouvel utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            user_id = str(uuid.uuid4())
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO users (id, username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, email, password_hash, full_name, role))
            
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Récupère un utilisateur par son nom"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Récupère un utilisateur par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Met à jour un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['full_name', 'role', 'is_active']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        return True
    
    def update_last_login(self, user_id: str):
        """Met à jour la date de dernière connexion"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    def get_all_users(self) -> List[Dict]:
        """Récupère tous les utilisateurs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, email, full_name, role, is_active, created_at, last_login FROM users')
        users = cursor.fetchall()
        conn.close()
        
        return [dict(user) for user in users]
    
    # ============ ANALYSIS OPERATIONS ============
    
    def create_analysis(self, user_id: str, content_type: str, content: str = "", file_path: str = "") -> str:
        """Crée une nouvelle analyse"""
        analysis_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analyses (id, user_id, content_type, content, file_path, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (analysis_id, user_id, content_type, content, file_path, "pending"))
        
        conn.commit()
        conn.close()
        
        return analysis_id
    
    def update_analysis_result(self, analysis_id: str, result: Dict, score: float, status: str = "completed"):
        """Met à jour les résultats d'une analyse"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE analyses 
            SET result = ?, score = ?, status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (json.dumps(result), score, status, analysis_id))
        
        conn.commit()
        conn.close()
    
    def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Récupère une analyse par son ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
        analysis = cursor.fetchone()
        conn.close()
        
        if analysis:
            analysis = dict(analysis)
            if analysis['result']:
                analysis['result'] = json.loads(analysis['result'])
            return analysis
        return None
    
    def get_user_analyses(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Récupère les analyses d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analyses 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        analyses = cursor.fetchall()
        conn.close()
        
        result = []
        for analysis in analyses:
            analysis = dict(analysis)
            if analysis['result']:
                analysis['result'] = json.loads(analysis['result'])
            result.append(analysis)
        
        return result
    
    def get_all_analyses(self, limit: int = 100) -> List[Dict]:
        """Récupère toutes les analyses"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, u.username 
            FROM analyses a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        analyses = cursor.fetchall()
        conn.close()
        
        result = []
        for analysis in analyses:
            analysis = dict(analysis)
            if analysis['result']:
                analysis['result'] = json.loads(analysis['result'])
            result.append(analysis)
        
        return result
    
    # ============ ALERT OPERATIONS ============
    
    def create_alert(self, analysis_id: str, severity: str, message: str) -> str:
        """Crée une nouvelle alerte"""
        alert_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (id, analysis_id, severity, message)
            VALUES (?, ?, ?, ?)
        ''', (alert_id, analysis_id, severity, message))
        
        conn.commit()
        conn.close()
        
        return alert_id
    
    def get_alerts(self, severity: str = None, status: str = None, limit: int = 50) -> List[Dict]:
        """Récupère les alertes avec filtres"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT a.*, u.username as created_by
            FROM alerts a
            LEFT JOIN analyses an ON a.analysis_id = an.id
            LEFT JOIN users u ON an.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if severity:
            query += " AND a.severity = ?"
            params.append(severity)
        
        if status:
            query += " AND a.status = ?"
            params.append(status)
        
        query += " ORDER BY a.created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        alerts = cursor.fetchall()
        conn.close()
        
        return [dict(alert) for alert in alerts]
    
    def resolve_alert(self, alert_id: str, resolved_by: str):
        """Marque une alerte comme résolue"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE alerts 
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP, resolved_by = ?
            WHERE id = ?
        ''', (resolved_by, alert_id))
        
        conn.commit()
        conn.close()
    
    # ============ REPORT OPERATIONS ============
    
    def create_report(self, user_id: str, name: str, content: Dict, file_path: str = "", format: str = "pdf") -> str:
        """Crée un nouveau rapport"""
        report_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reports (id, user_id, name, content, file_path, format)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (report_id, user_id, name, json.dumps(content), file_path, format))
        
        conn.commit()
        conn.close()
        
        return report_id
    
    def get_reports(self, user_id: str = None, limit: int = 20) -> List[Dict]:
        """Récupère les rapports"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT * FROM reports 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM reports 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        reports = cursor.fetchall()
        conn.close()
        
        result = []
        for report in reports:
            report = dict(report)
            if report['content']:
                report['content'] = json.loads(report['content'])
            result.append(report)
        
        return result
    
    # ============ LOG OPERATIONS ============
    
    def add_log(self, user_id: str, action: str, details: str = "", ip_address: str = ""):
        """Ajoute une entrée de log"""
        log_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO logs (id, user_id, action, details, ip_address)
            VALUES (?, ?, ?, ?, ?)
        ''', (log_id, user_id, action, details, ip_address))
        
        conn.commit()
        conn.close()
    
    def get_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Récupère les logs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT * FROM logs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        return [dict(log) for log in logs]
    
    # ============ STATISTICS ============
    
    def get_statistics(self) -> Dict:
        """Récupère les statistiques globales"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Nombre d'utilisateurs
        cursor.execute('SELECT COUNT(*) as count FROM users')
        stats['total_users'] = cursor.fetchone()['count']
        
        # Nombre d'analyses
        cursor.execute('SELECT COUNT(*) as count FROM analyses')
        stats['total_analyses'] = cursor.fetchone()['count']
        
        # Alertes actives
        cursor.execute('SELECT COUNT(*) as count FROM alerts WHERE status = "new"')
        stats['active_alerts'] = cursor.fetchone()['count']
        
        # Analyses par type
        cursor.execute('''
            SELECT content_type, COUNT(*) as count 
            FROM analyses 
            GROUP BY content_type
        ''')
        stats['analyses_by_type'] = {row['content_type']: row['count'] for row in cursor.fetchall()}
        
        # Alertes par sévérité
        cursor.execute('''
            SELECT severity, COUNT(*) as count 
            FROM alerts 
            GROUP BY severity
        ''')
        stats['alerts_by_severity'] = {row['severity']: row['count'] for row in cursor.fetchall()}
        
        # Score moyen
        cursor.execute('SELECT AVG(score) as avg_score FROM analyses WHERE score IS NOT NULL')
        avg_score = cursor.fetchone()['avg_score']
        stats['average_score'] = round(avg_score, 2) if avg_score else 0
        
        conn.close()
        return stats