from __future__ import annotations

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    url: str = Field(min_length=1)
    echo: bool = False


class CORSConfig(BaseModel):
    allow_origins: list[str] = Field(min_length=1)
    allow_credentials: bool = True
    allow_methods: list[str] = Field(min_length=1)
    allow_headers: list[str] = Field(min_length=1)


class ServerConfig(BaseModel):
    cors: CORSConfig


class SeedOfferConfig(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=120)
    base_salary: float = Field(ge=0)
    annual_bonus: float = Field(default=0, ge=0)
    annual_equity: float = Field(default=0, ge=0)
    sign_on_bonus: float = Field(default=0, ge=0)
    col_index: float = Field(default=1.0, gt=0)


class DevConfig(BaseModel):
    seed_offers: list[SeedOfferConfig] = Field(default_factory=list)


class AppConfig(BaseModel):
    database: DatabaseConfig
    server: ServerConfig
    dev: DevConfig = Field(default_factory=DevConfig)
