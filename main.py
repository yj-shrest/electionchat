import os
import requests
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI  # new SDK style

POST_URL = "https://old.reddit.com/r/NepalSocial/comments/1rlxszq/live_nepal_election_2082_live_poll_updates/.json"

reddit_context = ""


def scrape_reddit_post():
    try:
        headers = {"User-Agent": "election-bot/1.0", "Accept": "application/json"}
        res = requests.get(POST_URL, headers=headers, timeout=10)
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

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    prompt: str


client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))  # new SDK style


@app.post("/ask")
async def ask(req: AskRequest):
    global reddit_context

    instructions = (
        "Answer based on the question and the context. "
        "No analysis unless asked. "
        "If asked about a person or constituency, only give current vote count with names and party."
    )

    user_input = f"Context:\n{reddit_context}\n\nQuestion: {req.prompt}"

    try:
        response = client.responses.create(
            model="gpt-5.2",  # new model style
            instructions=instructions,
            input=user_input,
        )
        return {"response": response.output_text}
    except Exception as e:
        return {"error": str(e)}