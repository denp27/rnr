import httpx
import logging
from typing import Dict, List, Optional
from config import Config

logger = logging.getLogger(__name__)

class FragmentClient:
    def __init__(self):
        self.api_key = Config.FRAGMENT_API_KEY
        self.seed = Config.FRAGMENT_SEED
        self.base_url = "https://api.fragment.com/api/v2"

    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Fragment API {method} {url} data={data}")
        async with httpx.AsyncClient(timeout=60) as client:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            try:
                if method == "GET":
                    resp = await client.get(url, headers=headers, params=data)
                else:
                    resp = await client.post(url, headers=headers, json=data)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Fragment API error: {e}, status={getattr(resp, 'status_code', None)}")
                raise

    async def purchase_stars(self, username: str, amount: int) -> Dict:
        try:
            result = await self._request("POST", "/stars/gift", {"username": username, "stars": amount, "seed": self.seed})
            return {"success": True, "transaction_id": result.get("transaction_id")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def purchase_premium(self, username: str, months: int) -> Dict:
        try:
            if months not in [3,6,12]:
                return {"success": False, "error": "Некорректный срок"}
            result = await self._request("POST", "/premium/gift", {"username": username, "months": months, "seed": self.seed})
            if result.get("success") or result.get("transaction_id"):
                return {"success": True, "transaction_id": result.get("transaction_id")}
            return {"success": False, "error": result.get("error", "Ошибка API")}
        except Exception as e:
            logger.exception("Premium purchase error")
            return {"success": False, "error": str(e)}

    async def get_channel_stars_balance(self, channel_username: str) -> Dict:
        try:
            result = await self._request("GET", f"/channel/{channel_username}/stars/balance")
            return {"success": True, "balance": result.get("balance", 0), "total_earned": result.get("total_earned", 0)}
        except Exception as e:
            return {"success": False, "error": str(e), "balance": 0}

    async def withdraw_channel_stars(self, channel_username: str, stars_amount: int, destination: str = "balance") -> Dict:
        try:
            result = await self._request("POST", f"/channel/{channel_username}/stars/withdraw", {"amount": stars_amount, "destination": destination, "seed": self.seed})
            return {"success": True, "withdrawal_id": result.get("withdrawal_id")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_available_gifts(self) -> List[Dict]:
        try:
            result = await self._request("GET", "/gifts/available")
            return result.get("gifts", [])
        except:
            return [{"id": 1, "name": "Мишка", "price": 50}, {"id": 2, "name": "Сердце", "price": 100}]
