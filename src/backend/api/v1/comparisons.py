"""Comparison save/list/detail endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
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
