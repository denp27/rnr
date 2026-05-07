import asyncio
import sys
from database import init_db, Session, Admin

async def add_admin(telegram_id: int, username: str = None):
    init_db()
    session = Session()
    if not session.query(Admin).filter_by(telegram_id=telegram_id).first():
        admin = Admin(telegram_id=telegram_id, username=username or str(telegram_id), role="superadmin")
        session.add(admin)
        session.commit()
        print(f"Admin {telegram_id} added")
    else:
        print("Already exists")
    session.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(add_admin(int(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None))
    else:
        print("Usage: python add_admin.py TELEGRAM_ID")
