from fastapi import FastAPI, Request
import httpx, os

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.get("/")
def root():
    return {"message": "Bot is running"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return "Unauthorized", 403

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    for entry in data.get("entry", []):
        for msg_event in entry.get("messaging", []):
            sender_id = msg_event["sender"]["id"]
            if "message" in msg_event and "text" in msg_event["message"]:
                text = msg_event["message"]["text"]
                reply = await get_reply(text)
                await send_message(sender_id, reply)
    return {"status": "ok"}

async def get_reply(text):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": text}],
        "temperature": 0.7
    }
    async with httpx.AsyncClient() as client:
        res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
        return res.json()["choices"][0]["message"]["content"]

async def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)
