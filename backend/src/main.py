from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import CompareResponse, Offer, OfferCompareItem, OfferCreate, OfferRead, OfferUpdate
from .services import compute_metrics


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Job Offer Insight API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/offers", response_model=list[OfferRead])
def list_offers(session: Session = Depends(get_session)) -> list[Offer]:
    statement = select(Offer).order_by(desc(cast(Any, Offer.created_at)))
    return list(session.exec(statement))


@app.post("/offers", response_model=OfferRead, status_code=status.HTTP_201_CREATED)
def create_offer(payload: OfferCreate, session: Session = Depends(get_session)) -> Offer:
    offer = Offer.model_validate(payload)
    session.add(offer)
    session.commit()
    session.refresh(offer)
    return offer


@app.patch("/offers/{offer_id}", response_model=OfferRead)
def update_offer(offer_id: int, payload: OfferUpdate, session: Session = Depends(get_session)) -> Offer:
    offer = session.get(Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(offer, key, value)

    offer.updated_at = datetime.now(UTC)
    session.add(offer)
    session.commit()
    session.refresh(offer)
    return offer


@app.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_offer(offer_id: int, session: Session = Depends(get_session)) -> Response:
    offer = session.get(Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    session.delete(offer)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/offers/compare", response_model=CompareResponse)
def compare_offers(
    sort_by: str = Query(default="total_comp_annual"),
    descending: bool = Query(default=True),
    session: Session = Depends(get_session),
) -> CompareResponse:
    valid_sort_fields = {"total_comp_annual", "total_comp_year1", "total_comp_col_adjusted", "base_salary"}
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort_by value")

    statement = select(Offer)
    offers = list(session.exec(statement))

    offer_items: list[OfferCompareItem] = []
    for offer in offers:
        metrics = compute_metrics(offer)
        offer_items.append(
            OfferCompareItem(
                **offer.model_dump(),
                total_comp_annual=metrics.total_comp_annual,
                total_comp_year1=metrics.total_comp_year1,
                total_comp_col_adjusted=metrics.total_comp_col_adjusted,
            )
        )

    offer_items.sort(key=lambda item: getattr(item, sort_by), reverse=descending)
    return CompareResponse(offers=offer_items)


@app.post("/dev/seed", response_model=list[OfferRead])
def seed_demo_data(session: Session = Depends(get_session)) -> list[Offer]:
    existing = list(session.exec(select(Offer)))
    if existing:
        return existing

    sample_offers = [
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

    for offer in sample_offers:
        session.add(offer)

    session.commit()
    return list(session.exec(select(Offer).order_by(desc(str(Offer.created_at)))))


@app.get("/offers/{offer_id}", response_model=OfferRead)
def get_offer(offer_id: int, session: Session = Depends(get_session)) -> Offer:
    offer = session.get(Offer, offer_id)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return offer
