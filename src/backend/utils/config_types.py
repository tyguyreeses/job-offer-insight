"""Typed runtime configuration models for the backend."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    accepted_audio_extensions: list[str] = Field(
        default_factory=lambda: [".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"],
        min_length=1,
    )
    timeout_seconds: float = Field(default=45.0, gt=0)
    max_retries: int = Field(default=2, ge=0)


class WorkflowSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enable_audio_intake: bool = True
    enable_text_intake: bool = True
    enable_missing_info_followups: bool = True
    enable_non_monetary_summary: bool = True
    allow_placeholder_comparisons: bool = True


class TaxProfileSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_state: str = Field(default="CO", min_length=2, max_length=2)
    default_filing_status: Literal["single", "married_joint", "head_of_household"] = "single"
    federal_tax_rate: float = Field(default=0.22, ge=0, le=1)
    fica_tax_rate: float = Field(default=0.0765, ge=0, le=1)
    default_pre_tax_deduction_percent: float = Field(default=0.0, ge=0, le=100)
    state_tax_rates: dict[str, float] = Field(default_factory=lambda: {"CO": 0.044})

    @model_validator(mode="after")
    def validate_state_tax_rates(self) -> "TaxProfileSection":
        normalized: dict[str, float] = {}
        for state, rate in self.state_tax_rates.items():
            cleaned_state = state.strip().upper()
            if len(cleaned_state) != 2:
                raise ValueError("state_tax_rates keys must be 2-letter state codes")
            if rate < 0 or rate > 1:
                raise ValueError("state_tax_rates values must be between 0 and 1")
            normalized[cleaned_state] = rate
        self.state_tax_rates = normalized
        self.default_state = self.default_state.strip().upper()
        return self


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["structured-output", "non-structured"] = "structured-output"
    enabled: bool = True
    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    max_output_tokens: int = Field(default=1200, ge=1)
    tools: list["AgentToolConfig"] = Field(default_factory=list)
    reasoning: "AgentReasoningConfig | None" = None


class AgentReasoningConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    effort: Literal["low", "medium", "high"] | None = None
    summary: Literal["auto", "concise", "detailed"] | None = None


class AgentToolConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    description: str = ""
    enabled: bool = True


class AgentsSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entry_creation: AgentConfig
    parse_entry: AgentConfig
    comparison_one_to_one: AgentConfig
    comparison_one_to_all: AgentConfig


class OfferSchemaIdentitySection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name_path: str = Field(default="company_name", min_length=1)
    role_title_path: str = Field(default="role_title", min_length=1)


class OfferSchemaRequiredSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    all_of: list[str] = Field(default_factory=list)
    one_of: list[list[str]] = Field(default_factory=list)


class OfferSchemaCardSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)


class OfferSchemaEditSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)


class OfferSchemaFieldCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visible: bool = True
    section_id: str = Field(min_length=1)
    order: int = Field(default=0)
    style: Literal["value", "labeled_value", "list"] = "labeled_value"


class OfferSchemaFieldEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visible: bool = True
    section_id: str = Field(min_length=1)
    order: int = Field(default=0)
    widget: Literal["text", "number", "textarea", "textarea_list"] = "text"


class OfferSchemaField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = ""
    storage_path: str = Field(min_length=1)
    data_type: Literal["string", "number", "integer", "list_string"]
    group: Literal["core", "compensation", "monetary", "non_monetary", "meta"]
    required: bool = False
    default_when_omitted: Any = None
    card: OfferSchemaFieldCard
    edit: OfferSchemaFieldEdit

    @model_validator(mode="after")
    def validate_defaults_match_type(self) -> "OfferSchemaField":
        if self.default_when_omitted is None:
            return self
        if self.data_type == "string" and not isinstance(self.default_when_omitted, str):
            raise ValueError("default_when_omitted must be string for string fields")
        if self.data_type in ("number", "integer") and not isinstance(
            self.default_when_omitted, (int, float)
        ):
            raise ValueError("default_when_omitted must be numeric for number/integer fields")
        if self.data_type == "list_string":
            if not isinstance(self.default_when_omitted, list) or any(
                not isinstance(item, str) for item in self.default_when_omitted
            ):
                raise ValueError("default_when_omitted must be list[str] for list_string fields")
        return self


class OfferSchemaMigrationRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_path: str = Field(min_length=1)
    to_path: str = Field(min_length=1)


class OfferSchemaMigration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_version: int = Field(ge=1)
    rules: list[OfferSchemaMigrationRule] = Field(default_factory=list)


class OfferSchemaSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(default=1, ge=1)
    identity: OfferSchemaIdentitySection
    required: OfferSchemaRequiredSection
    card_sections: list[OfferSchemaCardSection]
    edit_sections: list[OfferSchemaEditSection]
    fields: list[OfferSchemaField]
    migrations: list[OfferSchemaMigration] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_field_ids_and_paths(self) -> "OfferSchemaSection":
        field_ids = [field.id for field in self.fields]
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("offer_schema.fields contains duplicate field ids")

        storage_paths = [field.storage_path for field in self.fields]
        if len(storage_paths) != len(set(storage_paths)):
            raise ValueError("offer_schema.fields contains duplicate storage_path values")

        card_ids = {section.section_id for section in self.card_sections}
        edit_ids = {section.section_id for section in self.edit_sections}
        for field in self.fields:
            if field.card.section_id not in card_ids:
                raise ValueError(
                    f"Field '{field.id}' references unknown card section '{field.card.section_id}'"
                )
            if field.edit.section_id not in edit_ids:
                raise ValueError(
                    f"Field '{field.id}' references unknown edit section '{field.edit.section_id}'"
                )

        known_ids = set(field_ids)
        for field_id in self.required.all_of:
            if field_id not in known_ids:
                raise ValueError(f"required.all_of references unknown field id: {field_id}")
        for group in self.required.one_of:
            if not group:
                raise ValueError("required.one_of groups may not be empty")
            for field_id in group:
                if field_id not in known_ids:
                    raise ValueError(f"required.one_of references unknown field id: {field_id}")

        return self


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app: AppSection
    logging: LoggingSection
    database: DatabaseSection
    openai: OpenAISection
    workflow: WorkflowSection
    tax_profile: TaxProfileSection
    agents: AgentsSection
    offer_schema: OfferSchemaSection
