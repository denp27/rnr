import logging
from fastapi import FastAPI, Request, HTTPException
from services.platega_client import PlategaClient
from services.aurura_pay import AururaPayClient
from database import update_balance, add_transaction

app = FastAPI()
platega = PlategaClient()
aurura = AururaPayClient()
logger = logging.getLogger(__name__)

@app.post("/webhook/platega")
async def platega_webhook(request: Request):
    data = await request.json()
    signature = request.headers.get("X-Platega-Signature", "")
    if not platega.verify_webhook(data, signature):
        logger.warning(f"Неверная подпись Platega: {signature}")
        raise HTTPException(401, "Invalid signature")
    if data.get("status") == "success":
        user_id = data.get("custom_data", {}).get("user_id")
        amount = data.get("amount", 0)
        if user_id and amount:
            update_balance(int(user_id), amount)
            add_transaction(int(user_id), "topup", amount, external_id=data.get("payment_id"))
            logger.info(f"Platega: user {user_id} пополнил {amount}")
    return {"status": "ok"}

@app.post("/webhook/aurura")
async def aurura_webhook(request: Request):
    raw = await request.body()
    signature = request.headers.get("X-Aurura-Signature", "")
    if not aurura.verify_webhook_signature(raw, signature):
        logger.warning(f"Неверная подпись Aurura")
        raise HTTPException(401, "Invalid signature")
    data = await request.json()
    if data.get("status") == "success":
        user_id = data.get("metadata", {}).get("user_id")
        amount = data.get("amount", 0)
        if user_id and amount:
            update_balance(int(user_id), amount)
            add_transaction(int(user_id), "topup", amount, external_id=data.get("payment_id"))
            logger.info(f"Aurura: user {user_id} пополнил {amount}")
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}