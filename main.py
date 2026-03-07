import requests
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

load_dotenv()
POST_URL = "https://old.reddit.com/r/NepalSocial/comments/1rlxszq/live_nepal_election_2082_live_poll_updates/.json"

reddit_context = ""

def scrape_reddit_post():
    try:
        url = "https://www.reddit.com/r/NepalSocial/comments/1rlxszq/live_nepal_election_2082_live_poll_updates/.json"

        headers = {
            "User-Agent": "election-bot/1.0",
            "Accept": "application/json"
        }

        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            print("Reddit returned:", res.status_code)
            return reddit_context

        data = res.json()

        post = data[0]["data"]["children"][0]["data"]

        title = post["title"]
        body = post["selftext"]

        return f"{title}\n\n{body}"

    except Exception as e:
        print("Scrape failed:", e)
        print("Response preview:", res.text[:200])
        return reddit_context


async def refresh_reddit_context():
    global reddit_context

    while True:
        print("Refreshing reddit post...")
        reddit_context = scrape_reddit_post()
        await asyncio.sleep(300)  # 5 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    global reddit_context

    reddit_context = scrape_reddit_post()
    task = asyncio.create_task(refresh_reddit_context())

    yield

    task.cancel()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    prompt: str


@app.post("/ask")
async def ask(req: AskRequest):
    # print(reddit_context)
    client = genai.Client()

    contents = [
        f"""Answer baseds on the question and the context, No need to do analysis unless asked.
        if asked about a person or constinuency, only give current vote count with names and party only
          Context:\n{reddit_context}""",
        f"User question: {req.prompt}",
    ]

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=contents,
    )

    return {"response": response.text}