import httpx
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import Dict
from config import Config

class AururaPayClient:
    def __init__(self):
        self.api_key = Config.AURURA_API_KEY
        self.secret = Config.AURURA_SECRET_KEY
        self.wallet_id = Config.AURURA_WALLET_ID
        self.callback_secret = Config.AURURA_CALLBACK_SECRET
        self.base_url = "https://api.aururapay.com/v1"

    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        async with httpx.AsyncClient() as client:
            timestamp = str(int(datetime.now().timestamp()))
            nonce = str(uuid.uuid4())
            body = json.dumps(data, sort_keys=True) if data else ""
            sign_str = f"{method}\n{endpoint}\n{timestamp}\n{nonce}\n{body}"
            signature = hmac.new(self.secret.encode(), sign_str.encode(), hashlib.sha256).hexdigest()
            headers = {"X-API-Key": self.api_key, "X-Timestamp": timestamp, "X-Nonce": nonce, "X-Signature": signature}
            url = f"{self.base_url}{endpoint}"
            if method == "GET":
                resp = await client.get(url, headers=headers, params=data)
            else:
                resp = await client.post(url, headers=headers, json=data)
            return resp.json()

    async def create_payment(self, amount: float, user_id: int, order_id: str = None) -> Dict:
        if not order_id:
            order_id = f"ORDER_{user_id}_{int(datetime.now().timestamp())}"
        payload = {
            "amount": amount,
            "currency": "RUB",
            "order_id": order_id,
            "description": "Пополнение баланса",
            "callback_url": f"{Config.WEBHOOK_URL}/webhook/aurura",
            "wallet_id": self.wallet_id,
            "metadata": {"user_id": user_id}
        }
        result = await self._request("POST", "/payment/create", payload)
        return {"payment_id": result["payment_id"], "payment_url": result["payment_url"]}

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        expected = hmac.new(self.callback_secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

class AururaPaymentHandler:
    def __init__(self, bot):
        self.client = AururaPayClient()
        self.bot = bot

    async def init_payment(self, user_id: int, amount: float) -> Dict:
        return await self.client.create_payment(amount, user_id)
