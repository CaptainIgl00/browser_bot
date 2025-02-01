from langchain_openai import ChatOpenAI
from browser_use import Agent, Browser, BrowserConfig
import asyncio
from dotenv import load_dotenv
from pydantic import SecretStr
import os
import json
import random
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

browser = Browser(
    config=BrowserConfig(
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
)

initial_actions = [
    {"open_tab": {"url": "https://www.instagram.com/"}},
    {"scroll_down": {"amount": random.randint(100, 500)}}
]

agent = Agent(
    task = (
        "In instagram, search for the account 'brasserie chez ju' and scroll down to load recent posts. "
        "Extract the URLs of the three most recent posts along with the URLs of their associated images. "
        "Return ONLY a single, plain JSON string and nothing else—do not include any explanation, markdown, or extra formatting. "
        "Your output must be exactly a valid JSON string (i.e. the output must be enclosed in double quotes as plain text), not a JSON object or a Python dictionary. "
        "The JSON string must exactly follow the format below (replace the sample values with the extracted ones):\n"
        "{\"posts\": ["
        "    {\"url\": \"https://www.instagram.com/p/<url_post1>/\", \"image_url\": \"https://scontent-cdg4-3.cdninstagram.com/v/<url_image1>\"}, "
        "    {\"url\": \"https://www.instagram.com/p/<url_post2>/\", \"image_url\": \"https://scontent-cdg4-3.cdninstagram.com/v/<url_image2>\"}, "
        "    {\"url\": \"https://www.instagram.com/p/<url_post3>/\", \"image_url\": \"https://scontent-cdg4-3.cdninstagram.com/v/<url_image3>\"}"
        "]}"
    ),
    initial_actions=initial_actions,
    llm=ChatOpenAI(
        model="deepseek-chat",
        api_key=SecretStr(api_key),
        base_url='https://api.deepseek.com/v1',
        temperature=0
    ),
    use_vision=False,
    browser=browser,
)

async def main():
    history = await agent.run()
    print(f'Gros output qui marche pas: {history.final_result()}')
    # save the output to a file
    with open("output.json", "w") as f:
        f.write(history.final_result())
    # output is a string, we need to parse it to a json object
    try:
        output_json = json.loads(history.final_result())
        print(output_json)
    except json.JSONDecodeError:
        print("Error: Invalid JSON output")

asyncio.run(main())