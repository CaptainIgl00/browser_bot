import asyncio
import aiohttp
import random
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScrapingScheduler:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.trigger_endpoint = f"{api_url}/trigger-scrape"
    
    async def trigger_scraping(self):
        """Trigger the scraping process via API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.trigger_endpoint) as response:
                    if response.status == 200:
                        logger.info("Successfully triggered scraping")
                    else:
                        logger.error(f"Failed to trigger scraping: {response.status}")
        except Exception as e:
            logger.error(f"Error triggering scraping: {e}")
    
    async def run(self):
        """Run the scheduler indefinitely"""
        while True:
            try:
                # Calculate next run time (random time in the next 3 days)
                now = datetime.now()
                next_run = now + timedelta(days=3)
                
                # Random hour between 9:00 and 17:00
                next_run = next_run.replace(
                    hour=random.randint(9, 17),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                
                # Calculate seconds to wait
                wait_seconds = (next_run - now).total_seconds()
                
                logger.info(f"Next scraping scheduled for: {next_run}")
                
                # Wait until next run time
                await asyncio.sleep(wait_seconds)
                
                # Trigger scraping
                await self.trigger_scraping()
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)

async def main():
    scheduler = ScrapingScheduler()
    await scheduler.run()

if __name__ == "__main__":
    asyncio.run(main()) 