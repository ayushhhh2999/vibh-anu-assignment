import os
from pathlib import Path
import sys

from dotenv import dotenv_values


TEST_KIT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = TEST_KIT_DIR.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

for name, value in dotenv_values(TEST_KIT_DIR / ".env.test").items():
    if value is not None:
        os.environ.setdefault(name, value)

if os.getenv("APP_ENV", "").lower() not in {"test", "dev", "development"}:
    raise RuntimeError("Test accounts can only be seeded in a test or development environment.")

database_url = os.getenv("DATABASE_URL")
if not database_url:
    database_path = TEST_KIT_DIR / ".test-data" / "vibanu-test.db"
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite:///{database_path}"
    os.environ["DATABASE_URL"] = database_url

if not database_url.startswith("sqlite:"):
    raise RuntimeError("Test accounts may only be seeded into a SQLite database.")

from sqlalchemy import select

from app import models
from app.db import Base, SessionLocal, engine
from app.security import hash_password, verify_password


USERS = (
    ("Marketing", "marketing@vibhanu.com", "marketing", "E2E_MARKETING_PASSWORD"),
    ("Communication", "communication@vibhanu.com", "communication", "E2E_COMMUNICATION_PASSWORD"),
    ("Vigilance", "vigilance@vibhanu.com", "vigilance", "E2E_VIGILANCE_PASSWORD"),
    ("Support", "support@vibhanu.com", "support", "E2E_SUPPORT_PASSWORD"),
    ("Sales", "sales@vibhanu.com", "sales", "E2E_SALES_PASSWORD"),
)


def seed_test_users() -> None:
    Base.metadata.create_all(bind=engine)
    created = 0
    updated = 0

    with SessionLocal() as db:
        try:
            for full_name, email, role, password_key in USERS:
                password = os.getenv(password_key)
                if not password:
                    raise RuntimeError(f"Missing local test configuration value: {password_key}")

                user = db.scalar(select(models.User).where(models.User.email == email))
                if user is None:
                    user = models.User(
                        full_name=full_name,
                        email=email,
                        role=role,
                        password_hash=hash_password(password),
                    )
                    db.add(user)
                    created += 1
                    continue

                changed = user.full_name != full_name or user.role != role
                user.full_name = full_name
                user.role = role
                if not verify_password(password, user.password_hash):
                    user.password_hash = hash_password(password)
                    changed = True
                updated += int(changed)

            db.commit()
        except Exception:
            db.rollback()
            raise

    print(f"Test accounts ready: {created} created, {updated} updated.")


if __name__ == "__main__":
    seed_test_users()