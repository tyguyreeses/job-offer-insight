"""Comparison save/list/detail endpoints."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from ...dependencies import get_comparison_service
from ...domain.models import ComparisonRecord
from ...domain.services.interfaces import ComparisonService

router = APIRouter(prefix="/comparisons")


class ComparisonCreateRequest(BaseModel):
    mode: Literal["one_to_one", "one_to_all"]
    selected_offer_ids: list[str]
    base_offer_id: str | None = None
    note: str | None = None


class ComparisonResponse(BaseModel):
    id: str
    comparison_mode: Literal["one_to_one", "one_to_all"]
    base_offer_id: str
    selected_offer_ids: list[str]
    summary_text: str
    note: str | None
    created_at: str
    updated_at: str


class ComparisonCreateResponse(BaseModel):
    status: str
    errors: list[str]
    comparison: ComparisonResponse | None


class ComparisonGenerateCodeResponse(BaseModel):
    status: str
    errors: list[str]
    draft_id: str | None
    mode: Literal["one_to_one", "one_to_all"] | None
    base_offer_id: str | None
    selected_offer_ids: list[str]
    code_section: dict[str, Any] | None
    ai_section_pending: bool


class ComparisonGenerateAIResponse(BaseModel):
    status: str
    errors: list[str]
    draft_id: str | None
    ai_section: dict[str, Any] | None


class ComparisonListResponse(BaseModel):
    comparisons: list[ComparisonResponse]


def _to_response(record: ComparisonRecord) -> ComparisonResponse:
    return ComparisonResponse(
        id=record.id,
        comparison_mode=record.comparison_mode,
        base_offer_id=record.base_offer_id,
        selected_offer_ids=record.selected_offer_ids,
        summary_text=record.summary_text,
        note=record.note,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post("", response_model=ComparisonCreateResponse)
def create_comparison(
    request: ComparisonCreateRequest,
    comparison_service: ComparisonService = Depends(get_comparison_service),
) -> ComparisonCreateResponse:
    result = comparison_service.create_comparison(
        mode=request.mode,
        selected_offer_ids=request.selected_offer_ids,
        base_offer_id=request.base_offer_id,
        note=request.note,
    )
    return ComparisonCreateResponse(
        status=result.status,
        errors=result.errors,
        comparison=_to_response(result.comparison) if result.comparison is not None else None,
    )


@router.post("/generate", response_model=ComparisonGenerateCodeResponse)
def generate_comparison_draft(
    request: ComparisonCreateRequest,
    comparison_service: ComparisonService = Depends(get_comparison_service),
) -> ComparisonGenerateCodeResponse:
    result = comparison_service.generate_comparison_draft(
        mode=request.mode,
        selected_offer_ids=request.selected_offer_ids,
        base_offer_id=request.base_offer_id,
        note=request.note,
    )
    return ComparisonGenerateCodeResponse(
        status=result.status,
        errors=result.errors,
        draft_id=result.draft_id,
        mode=result.mode,
        base_offer_id=result.base_offer_id,
        selected_offer_ids=result.selected_offer_ids,
        code_section=result.code_section,
        ai_section_pending=result.ai_section_pending,
    )


@router.post("/generate/{draft_id}/ai", response_model=ComparisonGenerateAIResponse)
def generate_comparison_ai_section(
    draft_id: str,
    comparison_service: ComparisonService = Depends(get_comparison_service),
) -> ComparisonGenerateAIResponse:
    result = comparison_service.generate_comparison_ai_section(draft_id=draft_id)
    return ComparisonGenerateAIResponse(
        status=result.status,
        errors=result.errors,
        draft_id=result.draft_id,
        ai_section=result.ai_section,
    )


@router.get("", response_model=ComparisonListResponse)
def list_comparisons(
    comparison_service: ComparisonService = Depends(get_comparison_service),
) -> ComparisonListResponse:
    comparisons = [_to_response(record) for record in comparison_service.list_comparisons()]
    return ComparisonListResponse(comparisons=comparisons)


@router.get("/{comparison_id}", response_model=ComparisonResponse)
def get_comparison(
    comparison_id: str,
    comparison_service: ComparisonService = Depends(get_comparison_service),
) -> ComparisonResponse:
    comparison = comparison_service.get_comparison(comparison_id)
    if comparison is None:
        raise HTTPException(status_code=404, detail=f"Comparison not found: {comparison_id}")
    return _to_response(comparison)


@router.delete("/{comparison_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_comparison(
    comparison_id: str,
    comparison_service: ComparisonService = Depends(get_comparison_service),
) -> Response:
    deleted = comparison_service.delete_comparison(comparison_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Comparison not found: {comparison_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
