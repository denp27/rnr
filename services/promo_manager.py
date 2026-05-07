from datetime import datetime, timedelta
import random
import string
from typing import Dict, Tuple
from database import Session, PromoCode, UserPromoUsage, User

class PromoCodeManager:
    def __init__(self):
        self.session = Session()

    def generate_code(self, length=8):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    def create_promo(self, created_by: int, discount_percent: int, max_uses: int = 1, min_payment: float = 0, expires_days: int = 30, custom_code: str = None, description: str = None) -> Dict:
        code = custom_code.upper() if custom_code else self.generate_code()
        if custom_code and self.session.query(PromoCode).filter_by(code=code).first():
            return {"success": False, "error": "Уже существует"}
        promo = PromoCode(code=code, discount_percent=discount_percent, max_uses=max_uses, min_payment=min_payment, created_by=created_by, expires_at=datetime.now()+timedelta(days=expires_days), description=description)
        self.session.add(promo)
        self.session.commit()
        return {"success": True, "code": code, "discount_percent": discount_percent}

    def validate_code(self, code: str, user_id: int, amount: float = None) -> Dict:
        promo = self.session.query(PromoCode).filter_by(code=code.upper(), is_active=True).first()
        if not promo:
            return {"valid": False, "error": "Не найден"}
        if promo.expires_at < datetime.now():
            return {"valid": False, "error": "Истёк"}
        if promo.used_count >= promo.max_uses:
            return {"valid": False, "error": "Превышен лимит"}
        used = self.session.query(UserPromoUsage).filter_by(user_id=user_id, promo_id=promo.id).first()
        if used:
            return {"valid": False, "error": "Уже использован"}
        if amount is not None and promo.min_payment > 0 and amount < promo.min_payment:
            return {"valid": False, "error": f"Мин. сумма {promo.min_payment} руб"}
        return {"valid": True, "promo_id": promo.id, "discount_percent": promo.discount_percent}

    def apply_promo(self, user_id: int, code: str, amount: float) -> Tuple[float, str, float]:
        val = self.validate_code(code, user_id, amount)
        if not val["valid"]:
            return amount, val["error"], 0
        promo = self.session.query(PromoCode).filter_by(id=val["promo_id"]).first()
        discount = amount * (promo.discount_percent / 100)
        new_amount = amount - discount
        usage = UserPromoUsage(user_id=user_id, promo_id=promo.id, applied_amount=new_amount)
        promo.used_count += 1
        self.session.add(usage)
        user = self.session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            user.promo_discount = promo.discount_percent
            user.promo_expires = datetime.now() + timedelta(days=30)
        self.session.commit()
        return new_amount, f"Скидка {promo.discount_percent}%", discount

    def get_all_promos(self):
        return [{"id": p.id, "code": p.code, "discount_percent": p.discount_percent, "used_count": p.used_count, "max_uses": p.max_uses} for p in self.session.query(PromoCode).all()]

    def delete_promo(self, promo_id: int) -> bool:
        promo = self.session.query(PromoCode).filter_by(id=promo_id).first()
        if promo:
            self.session.delete(promo)
            self.session.commit()
            return True
        return False
