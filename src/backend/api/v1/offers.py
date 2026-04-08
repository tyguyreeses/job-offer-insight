"""Offer intake and CRUD endpoints for Stage 4."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...dependencies import get_offer_service
from ...domain.services.interfaces import OfferService

router = APIRouter(prefix="/offers")


class MissingFieldPromptResponse(BaseModel):
    path: str
    required: bool
    message: str


class TextIntakeRequest(BaseModel):
    text: str = Field(min_length=1)
    omission_confirmations: dict[str, bool] = Field(default_factory=dict)
    extracted_offer_overrides: dict[str, Any] = Field(default_factory=dict)


class OfferResponse(BaseModel):
    offer: dict[str, Any]


class OfferListResponse(BaseModel):
    offers: list[dict[str, Any]]


class OfferIntakeResponse(BaseModel):
    status: str
    errors: list[str]
    warnings: list[str]
    missing_field_prompts: list[MissingFieldPromptResponse]
    offer: dict[str, Any] | None


class OfferUpdateRequest(BaseModel):
    payload: dict[str, Any]


@router.post("/intake/text", response_model=OfferIntakeResponse)
def intake_offer_from_text(
    request: TextIntakeRequest,
    offer_service: OfferService = Depends(get_offer_service),
) -> OfferIntakeResponse:
    result = offer_service.intake_text_offer(
        text=request.text,
        omission_confirmations=request.omission_confirmations,
        extracted_offer_overrides=request.extracted_offer_overrides,
    )
    offer_payload = (
        offer_service.render_offer_payload(result.offer) if result.offer is not None else None
    )
    return OfferIntakeResponse(
        status=result.status,
        errors=result.errors,
        warnings=result.warnings,
        missing_field_prompts=[MissingFieldPromptResponse(**prompt.__dict__) for prompt in result.missing_field_prompts],
        offer=offer_payload,
    )


@router.get("", response_model=OfferListResponse)
def list_offers(offer_service: OfferService = Depends(get_offer_service)) -> OfferListResponse:
    offers = [offer_service.render_offer_payload(record) for record in offer_service.list_offers()]
    return OfferListResponse(offers=offers)


@router.get("/{offer_id}", response_model=OfferResponse)
def get_offer(offer_id: str, offer_service: OfferService = Depends(get_offer_service)) -> OfferResponse:
    record = offer_service.get_offer(offer_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Offer not found: {offer_id}")
    return OfferResponse(offer=offer_service.render_offer_payload(record))


@router.put("/{offer_id}", response_model=OfferIntakeResponse)
def update_offer(
    offer_id: str,
    request: OfferUpdateRequest,
    offer_service: OfferService = Depends(get_offer_service),
) -> OfferIntakeResponse:
    result = offer_service.update_offer(offer_id=offer_id, payload=request.payload)
    if result.status == "not_found":
        raise HTTPException(status_code=404, detail=result.errors[0])

    offer_payload = (
        offer_service.render_offer_payload(result.offer) if result.offer is not None else None
    )
    return OfferIntakeResponse(
        status=result.status,
        errors=result.errors,
        warnings=result.warnings,
        missing_field_prompts=[MissingFieldPromptResponse(**prompt.__dict__) for prompt in result.missing_field_prompts],
        offer=offer_payload,
    )
