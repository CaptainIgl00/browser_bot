from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig
import asyncio
from dotenv import load_dotenv
from pydantic import SecretStr
import os
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

browser = Browser(
    config=BrowserConfig(
        chrome_instance_path="/usr/bin/google-chrome-stable",
    )
)

agent = Agent(
    task="Go to github.com and find the browser-use repo",
    llm=ChatOpenAI(
        model="deepseek-chat",
        api_key=SecretStr(api_key),
        base_url='https://api.deepseek.com/v1',
        streaming=True,
        temperature=0
    ),
    use_vision=False,
    browser=browser
)

async def main():
    await agent.run()
    input("Press Enter to close the browser...")
    await browser.close()

asyncio.run(main()) 