import requests
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
import os

app = FastAPI()

reddit_context = ""

POST_URL = "https://old.reddit.com/r/NepalSocial/comments/1rlxszq/live_nepal_election_2082_live_poll_updates/.json"


def scrape_reddit_post():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(POST_URL, headers=headers, timeout=10)
        data = res.json()

        post = data[0]["data"]["children"][0]["data"]

        title = post["title"]
        body = post["selftext"]

        return f"{title}\n\n{body}"

    except Exception as e:
        print("Scrape failed:", e)
        return reddit_context


async def refresh_reddit_context():
    global reddit_context

    while True:
        print("Refreshing reddit post...")
        reddit_context = scrape_reddit_post()
        await asyncio.sleep(300)  # 5 minutes


@app.on_event("startup")
async def startup_event():
    global reddit_context
    reddit_context = scrape_reddit_post()
    asyncio.create_task(refresh_reddit_context())


class AskRequest(BaseModel):
    prompt: str


@app.post("/ask")
async def ask(req: AskRequest):
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    client = genai.Client(api_key=gemini_api_key)

    contents = [
        f"Context from reddit post:\n{reddit_context}",
        f"Question: {req.prompt}"
    ]

    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=contents
    )

    return {"response": response.text}