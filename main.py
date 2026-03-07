import requests
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
import os

load_dotenv()
POST_URL = "https://old.reddit.com/r/NepalSocial/comments/1rlxszq/live_nepal_election_2082_live_poll_updates/.json"

reddit_context = ""


openai.api_key = os.getenv("OPENAI_API_KEY")

def answer_from_context(prompt, context):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Reddit post:\n{context}\n\nQuestion: {prompt}"}
        ],
        max_tokens=200,
    )
    return response['choices'][0]['message']['content']

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
    global reddit_context

    # Build your context as one string
    context_text = f"""Answer based on the question and the context. No analysis unless asked.
If asked about a person or constituency, only give current vote count with names and party only.

Context:
{reddit_context}
"""
    # Call the function with user question
    answer = answer_from_context(req.prompt, context_text)

    return {"response": answer}