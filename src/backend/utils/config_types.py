"""Typed runtime configuration models for the backend."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AppSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(default="job-offer-insight", min_length=1)
    env: Literal["dev", "test", "prod"] = "dev"
    host: str = Field(default="127.0.0.1", min_length=1)
    port: int = Field(default=8000, ge=1, le=65535)
    request_timeout_seconds: float = Field(default=30.0, gt=0)


class LoggingSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    json_logs: bool = False
    include_timestamps: bool = True


class DatabaseSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["sqlite"] = "sqlite"
    path: str = Field(default="data/job_offer_insight.db", min_length=1)
    enable_wal: bool = True
    timeout_seconds: float = Field(default=5.0, ge=0)


class OpenAISection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_key_env_var: str = Field(default="OPENAI_API_KEY", min_length=1)
    model: str = Field(default="gpt-5.2", min_length=1)
    transcription_model: str = Field(default="gpt-4o-mini-transcribe", min_length=1)
    timeout_seconds: float = Field(default=45.0, gt=0)
    max_retries: int = Field(default=2, ge=0)


class WorkflowSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enable_audio_intake: bool = True
    enable_text_intake: bool = True
    enable_missing_info_followups: bool = True
    enable_non_monetary_summary: bool = True
    allow_placeholder_comparisons: bool = True


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["structured-output", "non-structured"] = "structured-output"
    enabled: bool = True
    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    max_output_tokens: int = Field(default=1200, ge=1)


class AgentsSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text_parser: AgentConfig


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppSection
    logging: LoggingSection
    database: DatabaseSection
    openai: OpenAISection
    workflow: WorkflowSection
    agents: AgentsSection
