"""Offer intake and CRUD endpoints."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, model_validator

from ...dependencies import get_offer_service
from ...domain.services.interfaces import OfferService
from ...domain.services.offer_service import ConversationSessionNotFound

router = APIRouter(prefix="/offers")


class MissingFieldPromptResponse(BaseModel):
    path: str
    required: bool
    message: str


class TextIntakeRequest(BaseModel):
    session_id: str | None = None
    action: Literal["submit", "skip_current", "finish"]
    message_text: str | None = None

    @model_validator(mode="after")
    def validate_for_action(self) -> "TextIntakeRequest":
        if self.action == "submit":
            if self.message_text is None or self.message_text.strip() == "":
                raise ValueError("message_text is required for action=submit.")
        return self


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


class TextConversationResponse(BaseModel):
    session_id: str
    status: str
    assistant_message: str
    step: str
    can_finish: bool
    missing_required_fields: list[str]
    current_prompt_key: str | None
    errors: list[str]
    warnings: list[str]
    offer: dict[str, Any] | None


class OfferUpdateRequest(BaseModel):
    payload: dict[str, Any]


@router.post("/intake/text", response_model=TextConversationResponse)
def intake_offer_from_text(
    request: TextIntakeRequest,
    offer_service: OfferService = Depends(get_offer_service),
) -> TextConversationResponse:
    try:
        result = offer_service.intake_text_offer(
            session_id=request.session_id,
            action=request.action,
            message_text=request.message_text,
        )
    except ConversationSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    offer_payload = (
        offer_service.render_offer_payload(result.offer) if result.offer is not None else None
    )
    return TextConversationResponse(
        session_id=result.session_id,
        status=result.status,
        assistant_message=result.assistant_message,
        step=result.step,
        can_finish=result.can_finish,
        missing_required_fields=result.missing_required_fields,
        current_prompt_key=result.current_prompt_key,
        errors=result.errors,
        warnings=result.warnings,
        offer=offer_payload,
    )


@router.post("/intake/audio", response_model=TextConversationResponse)
def intake_offer_from_audio(
    action: Literal["submit", "skip_current", "finish"] = Form(...),
    session_id: str | None = Form(default=None),
    audio_file: UploadFile | None = File(default=None),
    offer_service: OfferService = Depends(get_offer_service),
) -> TextConversationResponse:
    if action == "submit" and audio_file is None:
        raise HTTPException(status_code=422, detail="audio_file is required for action=submit.")

    audio_bytes = audio_file.file.read() if audio_file is not None else None
    try:
        result = offer_service.intake_audio_offer(
            session_id=session_id,
            action=action,
            audio_bytes=audio_bytes,
            filename=(audio_file.filename or "audio.webm") if audio_file is not None else "",
            content_type=audio_file.content_type if audio_file is not None else None,
        )
    except ConversationSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    offer_payload = offer_service.render_offer_payload(result.offer) if result.offer is not None else None
    return TextConversationResponse(
        session_id=result.session_id,
        status=result.status,
        assistant_message=result.assistant_message,
        step=result.step,
        can_finish=result.can_finish,
        missing_required_fields=result.missing_required_fields,
        current_prompt_key=result.current_prompt_key,
        errors=result.errors,
        warnings=result.warnings,
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
