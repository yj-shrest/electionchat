import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
url = "https://old.reddit.com/r/NepalSocial/comments/1rlxszq/live_nepal_election_2082_live_poll_updates/.json"
# -------- Request Schema --------
class AskRequest(BaseModel):
    prompt: str

def scrape_reddit_post():

    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

    res = requests.get(url, headers=headers, timeout=10)

    if res.status_code != 200:
        raise Exception(f"Reddit request failed: {res.status_code} {res.text}")

    data = res.json()

    post = data[0]["data"]["children"][0]["data"]
    

    text = post.get("title", "") + "\n" + post.get("selftext", "")
    # print(text)

    context = text 

    return context
# -------- Cache Context --------
reddit_context = scrape_reddit_post()



# -------- API --------
@app.post("/ask")
async def ask(req: AskRequest):

    # client = get_client()

    prompt = f"""
Use the following live latest election update of nepal as context.

Context:
{reddit_context}

User Question:
{req.prompt}

Answer based only on the context above.
"""

    contents = [prompt]
    

    # response = client.models.generate_content(
    #     model="gemini-1.5-pro",
    #     contents=contents,
    # )
    client = genai.Client()

    response = client.models.generate_content(
    model="gemini-3-flash-preview", contents=contents
    )

    return {"response": response.text}