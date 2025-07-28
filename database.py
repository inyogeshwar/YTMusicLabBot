import sqlite3
import os
from datetime import datetime
from typing import List, Tuple, Optional

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Downloads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                song_title TEXT,
                format TEXT,
                effect TEXT,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Bot settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Promotional content table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                caption TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add a new user or update existing user info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def update_user_activity(self, user_id: int):
        """Update user's last active timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_active = ? WHERE user_id = ?
        ''', (datetime.now(), user_id))
        
        conn.commit()
        conn.close()
    
    def add_download(self, user_id: int, song_title: str, format: str, effect: str = None):
        """Record a download"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO downloads (user_id, song_title, format, effect)
            VALUES (?, ?, ?, ?)
        ''', (user_id, song_title, format, effect))
        
        conn.commit()
        conn.close()
    
    def get_user_count(self) -> Tuple[int, int]:
        """Get total and active user counts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        active_users = cursor.fetchone()[0]
        
        conn.close()
        return total_users, active_users
    
    def get_download_stats(self) -> dict:
        """Get download statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total downloads
        cursor.execute('SELECT COUNT(*) FROM downloads')
        total_downloads = cursor.fetchone()[0]
        
        # Downloads by format
        cursor.execute('SELECT format, COUNT(*) FROM downloads GROUP BY format')
        format_stats = dict(cursor.fetchall())
        
        # Downloads by effect
        cursor.execute('SELECT effect, COUNT(*) FROM downloads WHERE effect IS NOT NULL GROUP BY effect')
        effect_stats = dict(cursor.fetchall())
        
        # Today's downloads
        cursor.execute('SELECT COUNT(*) FROM downloads WHERE DATE(downloaded_at) = DATE("now")')
        today_downloads = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total': total_downloads,
            'formats': format_stats,
            'effects': effect_stats,
            'today': today_downloads
        }
    
    def get_all_users(self) -> List[int]:
        """Get all user IDs for broadcasting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE is_active = 1')
        user_ids = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return user_ids
    
    def set_setting(self, key: str, value: str):
        """Set a bot setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO bot_settings (key, value)
            VALUES (?, ?)
        ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get a bot setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM bot_settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def set_bot_setting(self, key: str, value: str):
        """Set a bot setting (alias for set_setting)"""
        self.set_setting(key, value)
    
    def delete_bot_setting(self, key: str):
        """Delete a bot setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM bot_settings WHERE key = ?', (key,))
        
        conn.commit()
        conn.close()
    
    def add_promo(self, promo_data: dict):
        """Add promotional content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO promos (file_id, caption, created_at)
            VALUES (?, ?, ?)
        ''', (promo_data['file_id'], promo_data['caption'], promo_data['created_at']))
        
        conn.commit()
        conn.close()
    
    def delete_latest_promo(self) -> bool:
        """Delete the latest promotional content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get the latest promo ID
        cursor.execute('SELECT id FROM promos ORDER BY created_at DESC LIMIT 1')
        result = cursor.fetchone()
        
        if result:
            cursor.execute('DELETE FROM promos WHERE id = ?', (result[0],))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def delete_all_promos(self) -> int:
        """Delete all promotional content and return count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM promos')
        count = cursor.fetchone()[0]
        
        cursor.execute('DELETE FROM promos')
        
        conn.commit()
        conn.close()
        return count
    
    def get_current_promo(self) -> Optional[dict]:
        """Get the current (latest) promotional content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_id, caption, created_at 
            FROM promos 
            ORDER BY created_at DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        
        conn.close()
        if result:
            return {
                'file_id': result[0],
                'caption': result[1],
                'created_at': result[2]
            }
        return None
    
    def get_random_promo(self) -> Optional[dict]:
        """Get a random promotional content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_id, caption, created_at 
            FROM promos 
            ORDER BY RANDOM() 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        
        conn.close()
        if result:
            return {
                'file_id': result[0],
                'caption': result[1],
                'created_at': result[2]
            }
        return None
