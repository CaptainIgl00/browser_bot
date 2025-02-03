from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from src.scrapper import scrape_instagram, InstagramPosts
from src.database import Database
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Instagram Scraper API")

# Initialize database
db = Database()

class ScrapeStatus(BaseModel):
    status: str
    timestamp: str
    last_result: InstagramPosts | None = None
    error_message: str | None = None

# Global variable to store the current scraping status
current_status = ScrapeStatus(
    status="idle",
    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    last_result=None,
    error_message=None
)

async def run_scraping():
    global current_status
    try:
        logger.info("Starting scraping process")
        current_status.status = "running"
        current_status.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_status.error_message = None
        
        # Log scraping start
        logger.debug("Logging scraping start to database")
        db.log_scraping("started")
        
        # Run the scraping
        logger.info("Running scraper...")
        success, result = await scrape_instagram()
        logger.debug(f"Scraper returned: success={success}, result type={type(result)}")
        
        if success:
            logger.info("Scraping completed successfully")
            current_status.status = "completed"
            current_status.last_result = result
            # Save posts to database
            logger.debug(f"Saving {len(result.posts)} posts to database")
            db.save_posts(result)
            # Log success
            db.log_scraping("completed")
        else:
            logger.error(f"Scraping failed: {result}")
            current_status.status = "error"
            current_status.error_message = result
            # Log error
            db.log_scraping("error", result)
            
    except Exception as e:
        logger.exception("Unexpected error during scraping")
        current_status.status = "error"
        current_status.error_message = str(e)
        # Log error
        db.log_scraping("error", str(e))
    finally:
        current_status.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Scraping process ended with status: {current_status.status}")

@app.post("/trigger-scrape")
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Trigger a new Instagram scraping job"""
    global current_status
    
    # If a scraping is already running, return its status
    if current_status.status == "running":
        return JSONResponse(
            status_code=409,
            content={"error": "A scraping job is already running", "current_status": current_status.model_dump()}
        )
    
    # Reset status before starting new job
    current_status.last_result = None
    current_status.error_message = None
    
    # Start the scraping in the background
    background_tasks.add_task(run_scraping)
    
    return {"message": "Scraping job started", "status": current_status.model_dump()}

@app.get("/status")
async def get_status():
    """Get the current status of the scraping job"""
    return current_status.model_dump()

@app.get("/posts")
async def get_posts(limit: int = 10):
    """Get the latest posts from the database"""
    posts = db.get_latest_posts(limit)
    return {"posts": [post.model_dump() for post in posts]}

@app.get("/history")
async def get_history(limit: int = 10):
    """Get the scraping history"""
    return {"history": db.get_scraping_history(limit)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 