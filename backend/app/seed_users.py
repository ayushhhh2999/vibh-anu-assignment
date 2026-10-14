
from getpass import getpass

from sqlalchemy import select

from app.db import Base, engine, SessionLocal
from app import models
from app.security import hash_password


DEPARTMENTS = [
    {
        "full_name": "Marketing",
        "email": "marketing@vibhanu.com",
        "role": "marketing",
    },
    {
        "full_name": "Communication",
        "email": "communication@vibhanu.com",
        "role": "communication",
    },
    {
        "full_name": "Vigilance",
        "email": "vigilance@vibhanu.com",
        "role": "vigilance",
    },
    {
        "full_name": "Support",
        "email": "support@vibhanu.com",
        "role": "support",
    },
    {
        "full_name": "Sales",
        "email": "sales@vibhanu.com",
        "role": "sales",
    },
]


def seed_users():
    # Ensure the model tables exist.
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        try:
            for department in DEPARTMENTS:
                existing_user = db.scalar(
                    select(models.User).where(
                        models.User.email == department["email"]
                    )
                )

                if existing_user:
                    print(
                        f"Skipping {department['email']}: "
                        "account already exists."
                    )
                    continue

                print(f"\nCreating {department['full_name']} account")
                password = getpass(
                    f"Enter the assignment password for "
                    f"{department['email']}: "
                )

                if not password:
                    raise ValueError("Password cannot be empty.")

                user = models.User(
                    full_name=department["full_name"],
                    email=department["email"],
                    role=department["role"],
                    password_hash=hash_password(password),
                )

                db.add(user)

            db.commit()
            print("\nAccount seeding completed.")

        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    seed_users()
