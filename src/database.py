import sqlite3
from datetime import datetime
from contextlib import contextmanager
from typing import List, Optional
from src.scrapper import InstagramPost, InstagramPosts
import aiohttp
import asyncio
from PIL import Image
import os
import io
import hashlib
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "instagram_posts.db", images_dir: str = "static/images"):
        self.db_path = db_path
        self.images_dir = images_dir
        os.makedirs(self.images_dir, exist_ok=True)
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
            
            # Create posts table with local_image_path
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    image_url TEXT NOT NULL,
                    local_image_path TEXT,
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

    async def download_and_convert_image(self, image_url: str) -> Optional[str]:
        """
        Download image from URL and convert it to PNG
        Returns the local path to the saved image
        """
        try:
            # Create a unique filename based on the URL
            filename = hashlib.md5(image_url.encode()).hexdigest() + ".png"
            local_path = os.path.join(self.images_dir, filename)
            
            # If file already exists, return its path
            if os.path.exists(local_path):
                return local_path
            
            # Headers to mimic a browser request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.instagram.com/",
                "Sec-Fetch-Dest": "image",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "same-site",
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, headers=headers, allow_redirects=True) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download image: {response.status} - {image_url}")
                        return None
                    
                    image_data = await response.read()
                    
                    # Convert to PNG using PIL
                    image = Image.open(io.BytesIO(image_data))
                    image = image.convert('RGBA')  # Ensure consistent format
                    image.save(local_path, 'PNG', optimize=True)
                    
                    logger.info(f"Successfully downloaded and converted image: {local_path}")
                    return local_path
        except Exception as e:
            logger.error(f"Error downloading/converting image: {e} - URL: {image_url}")
            return None
    
    def cleanup_old_images(self):
        """
        Delete all images in the images directory that are not referenced in the database
        """
        try:
            # Get all image paths from database
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT local_image_path FROM posts")
                db_images = {row['local_image_path'] for row in cursor.fetchall() if row['local_image_path']}

            # Get all files in the images directory
            for filename in os.listdir(self.images_dir):
                file_path = os.path.join(self.images_dir, filename)
                if file_path not in db_images:
                    os.remove(file_path)
                    logger.info(f"Deleted unused image: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up old images: {e}")

    async def save_posts(self, posts: InstagramPosts) -> None:
        """
        Save or update posts in the database and handle images.
        Previous posts and unused images will be deleted before saving new ones.
        """
        current_time = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete all previous posts
            cursor.execute("DELETE FROM posts")
            conn.commit()

            # Clean up old images before downloading new ones
            self.cleanup_old_images()
            
            for post in posts.posts:
                # Download and convert image
                local_image_path = await self.download_and_convert_image(post.image_url)
                
                # Insert new post
                cursor.execute("""
                    INSERT INTO posts (url, image_url, local_image_path, title, description, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    post.url,
                    post.image_url,
                    local_image_path,
                    post.title,
                    post.description,
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
    
    def get_latest_posts(self, limit: int = 10) -> List[dict]:
        """
        Get the most recent posts with local image paths
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT url, image_url, local_image_path, title, description, first_seen, last_seen
                FROM posts
                ORDER BY last_seen DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
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