from __future__ import annotations

from sqlmodel import Session, select

from src.database import engine
from src.models import Offer


def run() -> None:
    with Session(engine) as session:
        existing = list(session.exec(select(Offer)))
        if existing:
            print(f"Seed skipped: {len(existing)} offer(s) already present.")
            return

        offers = [
            Offer(
                company="Nimbus Labs",
                role="Software Engineer I",
                location="Denver, CO",
                base_salary=132000,
                annual_bonus=10000,
                annual_equity=18000,
                sign_on_bonus=15000,
                col_index=1.06,
            ),
            Offer(
                company="Atlas Analytics",
                role="Data Engineer",
                location="Austin, TX",
                base_salary=140000,
                annual_bonus=8000,
                annual_equity=12000,
                sign_on_bonus=10000,
                col_index=0.98,
            ),
            Offer(
                company="Summit AI",
                role="ML Engineer",
                location="San Francisco, CA",
                base_salary=170000,
                annual_bonus=15000,
                annual_equity=35000,
                sign_on_bonus=20000,
                col_index=1.35,
            ),
        ]

        for offer in offers:
            session.add(offer)

        session.commit()
        print(f"Seed complete: inserted {len(offers)} offers.")


if __name__ == "__main__":
    run()
