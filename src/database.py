import sqlite3
from datetime import datetime
from contextlib import contextmanager
from typing import List, Optional
from src.scrapper import InstagramPost, InstagramPosts

class Database:
    def __init__(self, db_path: str = "instagram_posts.db"):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize the database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create posts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    image_url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    first_seen TIMESTAMP NOT NULL,
                    last_seen TIMESTAMP NOT NULL
                )
            """)
            
            # Create scraping_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT
                )
            """)
            
            conn.commit()
    
    def save_posts(self, posts: InstagramPosts) -> None:
        """
        Save or update posts in the database
        """
        current_time = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for post in posts.posts:
                # Try to insert new post or update if exists
                cursor.execute("""
                    INSERT INTO posts (url, image_url, title, description, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(url) DO UPDATE SET
                        image_url = excluded.image_url,
                        title = excluded.title,
                        description = excluded.description,
                        last_seen = ?
                """, (
                    post.url,
                    post.image_url,
                    post.title,
                    post.description,
                    current_time,
                    current_time,
                    current_time
                ))
            
            conn.commit()
    
    def log_scraping(self, status: str, error_message: Optional[str] = None) -> None:
        """
        Log a scraping attempt
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scraping_history (timestamp, status, error_message) VALUES (?, ?, ?)",
                (datetime.now(), status, error_message)
            )
            conn.commit()
    
    def get_latest_posts(self, limit: int = 10) -> List[InstagramPost]:
        """
        Get the most recent posts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, image_url, title, description
                FROM posts
                ORDER BY last_seen DESC
                LIMIT ?
            """, (limit,))
            
            return [
                InstagramPost(
                    url=row['url'],
                    image_url=row['image_url'],
                    title=row['title'],
                    description=row['description']
                )
                for row in cursor.fetchall()
            ]
    
    def get_scraping_history(self, limit: int = 10) -> List[dict]:
        """
        Get recent scraping history
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, status, error_message
                FROM scraping_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()] 