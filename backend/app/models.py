from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import ConfigDict, field_validator
from sqlmodel import Field, SQLModel


class OfferBase(SQLModel):
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=120)

    base_salary: float = Field(ge=0)
    annual_bonus: float = Field(default=0, ge=0)
    annual_equity: float = Field(default=0, ge=0)
    sign_on_bonus: float = Field(default=0, ge=0)
    col_index: float = Field(default=1.0, gt=0)

    @field_validator("company", "role", "location")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class Offer(OfferBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class OfferCreate(OfferBase):
    pass


class OfferUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    company: Optional[str] = Field(default=None, min_length=1, max_length=120)
    role: Optional[str] = Field(default=None, min_length=1, max_length=120)
    location: Optional[str] = Field(default=None, min_length=1, max_length=120)

    base_salary: Optional[float] = Field(default=None, ge=0)
    annual_bonus: Optional[float] = Field(default=None, ge=0)
    annual_equity: Optional[float] = Field(default=None, ge=0)
    sign_on_bonus: Optional[float] = Field(default=None, ge=0)
    col_index: Optional[float] = Field(default=None, gt=0)

    @field_validator("company", "role", "location")
    @classmethod
    def strip_optional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class OfferRead(OfferBase):
    id: int
    created_at: datetime
    updated_at: datetime


class OfferCompareItem(OfferRead):
    total_comp_annual: float
    total_comp_year1: float
    total_comp_col_adjusted: float


class CompareResponse(SQLModel):
    offers: list[OfferCompareItem]
