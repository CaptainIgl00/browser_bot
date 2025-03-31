from typing import List
import os

class Settings:
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3300",  # Nuxt dev server
        "http://localhost:3000",  # Alternative Nuxt port
        "http://192.168.1.142:3300",
    ]
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Paths
    STATIC_DIR: str = "static"
    IMAGES_DIR: str = os.path.join(STATIC_DIR, "images")
    
    # Database
    DB_PATH: str = "instagram_posts.db"
    
    # Scraping Settings
    SCRAPE_INTERVAL_DAYS: int = 3
    SCRAPE_START_HOUR: int = 9
    SCRAPE_END_HOUR: int = 17

settings = Settings() 