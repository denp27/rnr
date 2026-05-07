from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///bot.db", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    total_stars_bought = Column(Integer, default=0)
    referrer_id = Column(Integer, nullable=True)
    referrals_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    is_premium = Column(Boolean, default=False)
    promo_discount = Column(Integer, default=0)
    promo_expires = Column(DateTime, nullable=True)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    type = Column(String)
    amount = Column(Float)
    stars_amount = Column(Integer, nullable=True)
    target_username = Column(String, nullable=True)
    gift_id = Column(Integer, nullable=True)
    gift_name = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    status = Column(String, default="pending")
    external_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

class PromoCode(Base):
    __tablename__ = "promocodes"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, index=True)
    discount_percent = Column(Integer)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    min_payment = Column(Float, default=0)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    description = Column(String, nullable=True)

class UserPromoUsage(Base):
    __tablename__ = "user_promo_usage"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    promo_id = Column(Integer, index=True)
    used_at = Column(DateTime, default=datetime.now)
    applied_amount = Column(Float, nullable=True)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    role = Column(String, default="admin")
    added_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

class GiftCache(Base):
    __tablename__ = "gifts_cache"
    id = Column(Integer, primary_key=True)
    gift_id = Column(Integer, unique=True, index=True)
    name = Column(String)
    price = Column(Integer)
    type = Column(String)
    supply = Column(Integer, nullable=True)
    total_supply = Column(Integer, nullable=True)
    first_seen = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

class ChannelWithdrawal(Base):
    __tablename__ = "channel_withdrawals"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    channel_username = Column(String)
    stars_amount = Column(Integer)
    rub_amount = Column(Float)
    withdrawal_url = Column(String, nullable=True)
    status = Column(String, default="pending")
    fragment_withdrawal_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

def init_db():
    Base.metadata.create_all(engine)

def get_user(telegram_id: int):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=str(telegram_id))
        session.add(user)
        session.commit()
    session.close()
    return user

def update_balance(telegram_id: int, amount: float) -> bool:
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.balance += amount
        session.commit()
        session.close()
        return True
    session.close()
    return False

def add_transaction(user_id: int, trans_type: str, amount: float, **kwargs):
    session = Session()
    tx = Transaction(user_id=user_id, type=trans_type, amount=amount, status="completed", **kwargs)
    session.add(tx)
    session.commit()
    session.close()

def is_admin(telegram_id: int) -> bool:
    session = Session()
    admin = session.query(Admin).filter_by(telegram_id=telegram_id, is_active=True).first()
    session.close()
    return admin is not None