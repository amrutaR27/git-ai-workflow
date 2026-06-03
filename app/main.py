import os, hmac, hashlib
from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from .worker import run_agentic_workflow
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
SECRET = os.getenv("WEBHOOK_SECRET").encode()

@app.post("/webhook")
async def github_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None)
):
    payload = await request.body()
    
    # Verify signature
    signature = hmac.new(SECRET, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(f"sha256={signature}", x_hub_signature_256):
        print("⚠️ [WEBHOOK] Signature verification failed!")
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()
    action = data.get("action")
    print(f"📥 [WEBHOOK] Received webhook event with action: '{action}'")

    # Treat "opened" (first creation) and "synchronize" (new commits pushed) as execution triggers
    if action in ["opened", "synchronize"]:
        print(f"🕒 [WEBHOOK] Handing off PR #{data['pull_request']['number']} to background process")
        background_tasks.add_task(run_agentic_workflow, data)
        
    return {"status": "accepted"}