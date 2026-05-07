import httpx
import hashlib
import hmac
from typing import Dict
from config import Config

class PlategaClient:
    def __init__(self):
        self.api_key = Config.PLATEGA_API_KEY
        self.shop_id = Config.PLATEGA_SHOP_ID
        self.secret = Config.PLATEGA_SECRET
        self.base_url = "https://api.platega.io/v2"

    async def create_payment(self, amount: float, order_id: str, user_id: int) -> Dict:
        async with httpx.AsyncClient() as client:
            payload = {
                "shop_id": self.shop_id,
                "amount": amount,
                "order_id": order_id,
                "currency": "RUB",
                "description": f"Пополнение на {amount} руб",
                "webhook_url": f"{Config.WEBHOOK_URL}/webhook/platega",
                "custom_data": {"user_id": user_id}
            }
            payload["sign"] = self._sign(payload)
            resp = await client.post(f"{self.base_url}/payment/create", json=payload, headers={"Authorization": f"Bearer {self.api_key}"})
            data = resp.json()
            return {"payment_id": data["payment"]["id"], "payment_url": data["payment"]["url"]}

    def _sign(self, data: Dict) -> str:
        sorted_items = sorted(data.items())
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_items if v]) + self.secret
        return hashlib.md5(sign_str.encode()).hexdigest()

    def verify_webhook(self, data: Dict, signature: str) -> bool:
        expected = self._sign({k:v for k,v in data.items() if k != "sign"})
        return hmac.compare_digest(expected, signature)
