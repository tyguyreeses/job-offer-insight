from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc
from sqlmodel import Session, select

from configs.config_loader import load_app_config
from configs.config_types import AppConfig, SeedOfferConfig

from .database import create_db_and_tables, create_engine_from_settings, make_session_dependency
from .models import CompareResponse, Offer, OfferCompareItem, OfferCreate, OfferRead, OfferUpdate
from .services import compute_metrics

APP_CONFIG = load_app_config()


def get_app_config(request: Request) -> AppConfig:
    return cast(AppConfig, request.app.state.config)


def get_seed_offers(config: AppConfig = Depends(get_app_config)) -> list[SeedOfferConfig]:
    return config.dev.seed_offers


def get_session(request: Request):
    session_dependency = cast(Any, request.app.state.session_dependency)
    yield from session_dependency()


def create_app(config: AppConfig) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = create_engine_from_settings(config.database.url, echo=config.database.echo)
        app.state.config = config
        app.state.engine = engine
        app.state.session_dependency = make_session_dependency(engine)
        create_db_and_tables(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Job Offer Insight API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.server.cors.allow_origins,
        allow_credentials=config.server.cors.allow_credentials,
        allow_methods=config.server.cors.allow_methods,
        allow_headers=config.server.cors.allow_headers,
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
    def seed_demo_data(
        seed_offers: list[SeedOfferConfig] = Depends(get_seed_offers),
        session: Session = Depends(get_session),
    ) -> list[Offer]:
        existing = list(session.exec(select(Offer)))
        if existing:
            return existing

        for seed_offer in seed_offers:
            session.add(Offer.model_validate(seed_offer.model_dump()))

        session.commit()
        statement = select(Offer).order_by(desc(cast(Any, Offer.created_at)))
        return list(session.exec(statement))

    @app.get("/offers/{offer_id}", response_model=OfferRead)
    def get_offer(offer_id: int, session: Session = Depends(get_session)) -> Offer:
        offer = session.get(Offer, offer_id)
        if not offer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
        return offer

    return app


app = create_app(APP_CONFIG)
