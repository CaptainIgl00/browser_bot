from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig, Controller
import asyncio
from pydantic import BaseModel
from typing import List
import random
from datetime import datetime

class InstagramPost(BaseModel):
    url: str
    image_url: str
    title: str
    description: str

class InstagramPosts(BaseModel):
    posts: List[InstagramPost]

# Configuration for browser
BROWSER_CONFIG = BrowserConfig(
    chrome_instance_path="/usr/bin/google-chrome-stable",
    extra_chromium_args=[
        "--profile-directory=Profile 1",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-accelerated-2d-canvas",
        "--no-first-run",
        "--no-zygote",
        "--disable-gpu",
        "--ignore-certificate-errors",
        "--ignore-certificate-errors-spki-list",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
)

# Initial actions for the agent
INITIAL_ACTIONS = [
    {"open_tab": {"url": "https://www.instagram.com/"}},
    {"scroll_down": {"amount": random.randint(100, 500)}}
]

async def create_agent() -> Agent:
    """Create a new agent with a fresh browser instance"""
    browser = Browser(config=BROWSER_CONFIG)
    controller = Controller(output_model=InstagramPosts)
    
    return Agent(
        task = (
            "In instagram, search for the account 'brasserie chez ju' and scroll down to load recent posts. "
            f"You need to find the last posts that involve content about events to come or already happening (today date is {datetime.now().strftime('%d/%m/%Y')}). "
            "Extract the URLs of these posts along with the URLs of their associated images, the title of the post and a synthetized description (for the disabled users) in FRENCH. "
            "Return the data in a JSON format that matches the InstagramPosts Pydantic model structure."
        ),
        initial_actions=INITIAL_ACTIONS,
        llm=ChatOpenAI(
            model="gpt-4o",
            temperature=0
        ),
        use_vision=True,
        browser=browser,
        controller=controller
    )

async def scrape_instagram() -> tuple[bool, InstagramPosts | str]:
    """
    Scrape Instagram posts for events from 'brasserie chez ju'.
    
    Returns:
        tuple[bool, InstagramPosts | str]: A tuple containing:
            - bool: Success status
            - InstagramPosts | str: Either the parsed posts data or error message
    """
    try:
        # Create a new agent with a fresh browser for each scraping session
        agent = await create_agent()
        history = await agent.run()
        result = history.final_result()
        
        if not result:
            return False, "No result returned from agent"
            
        try:
            # Validate and parse the JSON result
            parsed: InstagramPosts = InstagramPosts.model_validate_json(result)
            
            # Validate the content of each post
            for post in parsed.posts:
                if not all([
                    # Accept any Instagram post URL that contains /p/
                    "/p/" in post.url and post.url.startswith("https://www.instagram.com/"),
                    post.image_url.startswith("http"),
                    post.title.strip(),
                    post.description.strip()
                ]):
                    return False, f"Invalid post data format: {post.model_dump_json()}"
            
            # Log the successful extraction
            print("\nExtracted Instagram Posts:")
            for i, post in enumerate(parsed.posts, 1):
                print(f"\nPost {i}:")
                print(f"URL: {post.url}")
                print(f"Image URL: {post.image_url}")
                print(f"Title: {post.title}")
                print(f"Description: {post.description}")
            
            # Save the raw JSON to a file
            with open("output.json", "w") as f:
                f.write(result)
            
            return True, parsed
            
        except Exception as e:
            error_msg = f"Error parsing result: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error during scraping: {str(e)}"
        print(error_msg)
        return False, error_msg

if __name__ == "__main__":
    success, result = asyncio.run(scrape_instagram())
    if not success:
        print(f"Scraping failed: {result}")
    else:
        print("Scraping completed successfully")