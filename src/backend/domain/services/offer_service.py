"""Offer intake and CRUD orchestration for Stage 5.1."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from ...domain.models import OfferRecord
from ...domain.offer_schema import ConfiguredOfferSchema, get_path, is_present, set_path
from ...gen_ai.audio_transcriber import AudioTranscriptionError
from ...gen_ai.entry_creation_agent import EntryCreationAgentError
from ...gen_ai.protocols import Agent, AudioTranscriber, ChatAgent, ChatAgentReply
from ...gen_ai.text_parser_agent import TextParserError
from ...storage.repositories.interfaces import OfferRepository
from ...utils.config_types import TaxProfileSection
from ...utils.logging import get_logger
from .monetary_calculations import compute_derived_monetary_summary

logger = get_logger(__name__)

_TYPED_OMISSION_PHRASES = (
    "no",
    "none",
    "n/a",
    "not applicable",
    "don't have",
    "do not have",
    "not part of this offer",
)

_STEP_COLLECT_REQUIRED = "collect_required"
_STEP_COLLECT_MONETARY = "collect_monetary_extras"
_STEP_COLLECT_NON_MONETARY = "collect_non_monetary_extras"
_STEP_ANYTHING_ELSE = "anything_else"
_STEP_COMPLETED = "completed"

_PROMPT_KEY_REQUIRED = "required_fields_bundle"
_PROMPT_KEY_MONETARY = "monetary_benefits"
_PROMPT_KEY_NON_MONETARY = "non_monetary_benefits"
_PROMPT_KEY_ANYTHING_ELSE = "anything_else"
_TOOL_SUBMIT_ENTRY = "submit_entry"


@dataclass(frozen=True)
class FieldPrompt:
    path: str
    required: bool
    message: str


@dataclass(frozen=True)
class IntakeResult:
    status: str
    errors: list[str]
    warnings: list[str]
    missing_field_prompts: list[FieldPrompt]
    offer: OfferRecord | None


@dataclass(frozen=True)
class TextConversationResult:
    session_id: str
    status: str
    assistant_message: str
    step: str
    can_finish: bool
    missing_required_fields: list[str]
    current_prompt_key: str | None
    errors: list[str]
    warnings: list[str]
    messages: list[dict[str, str]]
    offer: OfferRecord | None


@dataclass
class ConversationSession:
    session_id: str
    payload: dict[str, Any]
    step: str = _STEP_COLLECT_REQUIRED
    source_input_type: str = "text"
    messages: list[dict[str, str]] = field(default_factory=list)


class ConversationSessionNotFound(RuntimeError):
    """Raised when a provided conversation session id does not exist."""


def _is_present(value: Any) -> bool:
    return is_present(value)


def _set_path(payload: dict[str, Any], path: str, value: Any) -> None:
    set_path(payload, path, value)


def _get_path(payload: dict[str, Any], path: str) -> Any:
    return get_path(payload, path)


def _merge_payloads(*parts: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for part in parts:
        for key, value in part.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = _merge_payloads(merged[key], value)
            else:
                merged[key] = value
    return merged


def _normalize_payload(payload: dict[str, Any], offer_schema: ConfiguredOfferSchema) -> None:
    offer_schema.normalize_payload(payload)


def _collect_missing_prompts(
    payload: dict[str, Any],
    offer_schema: ConfiguredOfferSchema,
) -> list[FieldPrompt]:
    prompts: list[FieldPrompt] = []
    required_paths = set(offer_schema.required_all_paths)
    for path in offer_schema.missing_required_paths(payload):
        prompts.append(
            FieldPrompt(
                path=path,
                required=(path in required_paths),
                message=f"Provide {path} to save this offer.",
            )
        )

    for path in offer_schema.optional_default_paths:
        if not _is_present(_get_path(payload, path)):
            prompts.append(
                FieldPrompt(
                    path=path,
                    required=False,
                    message=(
                        f"`{path}` is missing. Provide a value or confirm it is not part of this offer."
                    ),
                )
            )

    return prompts


def _apply_optional_omissions(
    payload: dict[str, Any],
    omission_confirmations: dict[str, bool] | None,
    offer_schema: ConfiguredOfferSchema,
) -> tuple[dict[str, Any], list[str], list[FieldPrompt]]:
    confirmations = omission_confirmations or {}
    warnings: list[str] = []
    unresolved_prompts: list[FieldPrompt] = []

    for path, default_value in offer_schema.optional_default_paths.items():
        if _is_present(_get_path(payload, path)):
            continue
        if confirmations.get(path, False):
            _set_path(payload, path, default_value)
            warnings.append(f"Stored blank value for omitted field: {path}")
            continue
        unresolved_prompts.append(
            FieldPrompt(
                path=path,
                required=False,
                message=(
                    f"`{path}` is missing. Provide a value or confirm it is not part of this offer."
                ),
            )
        )

    return payload, warnings, unresolved_prompts


def _fill_optional_defaults(payload: dict[str, Any], offer_schema: ConfiguredOfferSchema) -> list[str]:
    return offer_schema.fill_optional_defaults(payload)


def _validate_required(payload: dict[str, Any], offer_schema: ConfiguredOfferSchema) -> list[str]:
    errors: list[str] = []
    for path in offer_schema.required_all_paths:
        if _is_present(_get_path(payload, path)):
            continue
        errors.append(f"{path} is required")
    one_of_groups = offer_schema.required_one_of_paths
    if one_of_groups:
        if not any(all(_is_present(_get_path(payload, path)) for path in group) for group in one_of_groups):
            human = " or ".join(" and ".join(group) for group in one_of_groups)
            errors.append(f"Provide {human}")

    return errors


def _record_to_payload(record: OfferRecord, offer_schema: ConfiguredOfferSchema) -> dict[str, Any]:
    payload = offer_schema.apply_migrations(dict(record.payload))
    payload["id"] = record.id
    payload["company_name"] = record.company_name
    payload["role_title"] = record.role_title
    payload.setdefault("offer_meta", {})
    offer_meta = payload["offer_meta"]
    if isinstance(offer_meta, dict):
        offer_meta.setdefault("created_at", record.created_at)
        offer_meta["updated_at"] = record.updated_at
        offer_meta.setdefault("schema_version", offer_schema.version)
    return payload


def _demo_offer_payloads() -> list[dict[str, Any]]:
    return [
        {
            "company_name": "Northstar Robotics",
            "role_title": "Senior Software Engineer",
            "location": "Denver, CO",
            "compensation": {
                "annual_base_salary_usd": 182000,
                "signing_bonus_usd": 20000,
                "target_bonus_percent": 12,
            },
            "monetary_benefits": {
                "equity_grant_usd": 120000,
                "retirement_match_percent": 5,
                "health_insurance_employer_monthly_usd": 900,
                "other_monetary_benefits": ["Home office stipend"],
            },
            "non_monetary_summary_bullets": ["4-day in-office flexibility", "Strong mentorship culture"],
            "offer_meta": {"status": "active", "source_input_type": "debug_seed"},
        },
        {
            "company_name": "Sierra Data Labs",
            "role_title": "Platform Engineer II",
            "location": "Salt Lake City, UT",
            "compensation": {
                "annual_base_salary_usd": 168000,
                "signing_bonus_usd": 10000,
                "target_bonus_percent": 10,
            },
            "monetary_benefits": {
                "equity_grant_usd": 85000,
                "retirement_match_percent": 4,
                "health_insurance_employer_monthly_usd": 760,
                "other_monetary_benefits": ["Annual learning budget"],
            },
            "non_monetary_summary_bullets": ["Remote-first team", "On-call rotation capped at 1 week/month"],
            "offer_meta": {"status": "active", "source_input_type": "debug_seed"},
        },
        {
            "company_name": "Canyon Cloud Systems",
            "role_title": "Backend Engineer",
            "location": "Boulder, CO",
            "compensation": {
                "annual_base_salary_usd": 155000,
                "signing_bonus_usd": 15000,
                "target_bonus_percent": 8,
            },
            "monetary_benefits": {
                "equity_grant_usd": 60000,
                "retirement_match_percent": 3,
                "health_insurance_employer_monthly_usd": 820,
                "other_monetary_benefits": ["Transit pass reimbursement"],
            },
            "non_monetary_summary_bullets": ["Product ownership from day one", "Quarterly team offsites"],
            "offer_meta": {"status": "active", "source_input_type": "debug_seed"},
        },
    ]


def _missing_required_fields(
    payload: dict[str, Any],
    offer_schema: ConfiguredOfferSchema,
) -> list[str]:
    return offer_schema.missing_required_paths(payload)


def _required_list_text(
    missing_required_fields: list[str],
    offer_schema: ConfiguredOfferSchema,
) -> str:
    ordered: list[str] = []
    canonical_order = offer_schema.required_all_paths + [
        path for group in offer_schema.required_one_of_paths for path in group
    ]
    for path in canonical_order:
        if path in missing_required_fields:
            ordered.append(path)
    return ", ".join(ordered)


def _is_typed_omission(message_text: str) -> bool:
    lowered = message_text.strip().lower()
    if not lowered:
        return False

    if re.search(r"\bn\s*/\s*a\b", lowered):
        return True

    for phrase in _TYPED_OMISSION_PHRASES:
        if phrase == "n/a":
            continue
        if " " in phrase or "'" in phrase:
            pattern = r"\b" + re.escape(phrase).replace(r"\ ", r"\s+") + r"\b"
            if re.search(pattern, lowered):
                return True
            continue
        if re.search(r"\b" + re.escape(phrase) + r"\b", lowered):
            return True
    return False


def _current_prompt_key_for_step(step: str) -> str | None:
    if step == _STEP_COLLECT_REQUIRED:
        return _PROMPT_KEY_REQUIRED
    if step == _STEP_COLLECT_MONETARY:
        return _PROMPT_KEY_MONETARY
    if step == _STEP_COLLECT_NON_MONETARY:
        return _PROMPT_KEY_NON_MONETARY
    if step == _STEP_ANYTHING_ELSE:
        return _PROMPT_KEY_ANYTHING_ELSE
    return None


def _assistant_message_for_step(
    step: str,
    missing_required_fields: list[str],
    offer_schema: ConfiguredOfferSchema,
) -> str:
    if step == _STEP_COLLECT_REQUIRED:
        required_list = _required_list_text(missing_required_fields, offer_schema)
        return (
            "Please share the remaining required information: "
            f"{required_list}. You can provide it in one message."
        )
    if step == _STEP_COLLECT_MONETARY:
        return (
            "Any additional monetary benefits to include (for example retirement match, "
            "signing bonus, equity grant)? If none, you can skip."
        )
    if step == _STEP_COLLECT_NON_MONETARY:
        return (
            "Any additional non-monetary benefits to include? Share them naturally and I will "
            "store them as concise bullet points. If none, you can skip."
        )
    if step == _STEP_ANYTHING_ELSE:
        return "Is there anything else you want to add before saving?"
    if step == _STEP_COMPLETED:
        return "Great, your offer has been saved. You can edit details later."
    return "Please continue."


def _assistant_message_for_blocked_finish(
    missing_required_fields: list[str],
    offer_schema: ConfiguredOfferSchema,
) -> str:
    required_list = _required_list_text(missing_required_fields, offer_schema)
    return f"I still need required information before saving: {required_list}."


def _append_message(session: ConversationSession, role: str, content: str) -> None:
    text = content.strip()
    if text == "":
        return
    session.messages.append({"role": role, "content": text})


def _user_messages(session: ConversationSession) -> list[str]:
    messages: list[str] = []
    for entry in session.messages:
        if entry.get("role") != "user":
            continue
        content = entry.get("content")
        if isinstance(content, str) and content.strip() != "":
            messages.append(content.strip())
    return messages


def _looks_like_json_object(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("{") and stripped.endswith("}")


def _fallback_assistant_message(
    *,
    step: str,
    missing_required_fields: list[str],
    blocked_finish: bool,
    offer_schema: ConfiguredOfferSchema,
) -> str:
    if blocked_finish:
        return _assistant_message_for_blocked_finish(missing_required_fields, offer_schema)
    return _assistant_message_for_step(step, missing_required_fields, offer_schema)


def _fallback_assistant_reply(
    *,
    step: str,
    missing_required_fields: list[str],
    blocked_finish: bool,
    offer_schema: ConfiguredOfferSchema,
) -> ChatAgentReply:
    return ChatAgentReply(
        message=_fallback_assistant_message(
            step=step,
            missing_required_fields=missing_required_fields,
            blocked_finish=blocked_finish,
            offer_schema=offer_schema,
        ),
        tool_calls=[],
    )


def _requested_submit_entry(reply: ChatAgentReply) -> bool:
    for tool_call in reply.tool_calls:
        if tool_call.name == _TOOL_SUBMIT_ENTRY:
            return True
    return False


def _advance_on_skip(session: ConversationSession) -> None:
    if session.step == _STEP_COLLECT_MONETARY:
        session.step = _STEP_COLLECT_NON_MONETARY
        return
    if session.step == _STEP_COLLECT_NON_MONETARY:
        session.step = _STEP_ANYTHING_ELSE
        return


def _apply_prompt_omission_defaults(
    payload: dict[str, Any],
    prompt_key: str | None,
    offer_schema: ConfiguredOfferSchema,
) -> list[str]:
    if prompt_key == _PROMPT_KEY_MONETARY:
        return offer_schema.apply_group_defaults(payload, group="monetary")
    if prompt_key == _PROMPT_KEY_NON_MONETARY:
        return offer_schema.apply_group_defaults(payload, group="non_monetary")
    return []


@dataclass
class Stage4OfferService:
    offer_repository: OfferRepository
    text_parser_agent: Agent
    audio_transcriber: AudioTranscriber
    offer_schema: ConfiguredOfferSchema
    tax_config: TaxProfileSection
    entry_creation_agent: ChatAgent | None = None
    text_conversation_sessions: dict[str, ConversationSession] = field(default_factory=dict)

    def describe_capabilities(self) -> dict[str, str]:
        return {
            "service": "offer",
            "status": "stage_5_1_ready",
            "message": (
                "Conversational text intake, audio intake, validation, and persistence are active."
            ),
        }

    def _get_or_create_session(self, session_id: str | None) -> ConversationSession:
        if session_id is None:
            created_session_id = str(uuid4())
            session = ConversationSession(session_id=created_session_id, payload={})
            self.text_conversation_sessions[created_session_id] = session
            return session

        existing = self.text_conversation_sessions.get(session_id)
        if existing is None:
            raise ConversationSessionNotFound(f"Conversation session not found: {session_id}")
        return existing

    def _get_existing_session(self, session_id: str | None) -> ConversationSession:
        if session_id is None:
            raise ConversationSessionNotFound("Conversation session not found: <missing>")
        existing = self.text_conversation_sessions.get(session_id)
        if existing is None:
            raise ConversationSessionNotFound(f"Conversation session not found: {session_id}")
        return existing

    def _build_assistant_message(
        self,
        *,
        session: ConversationSession,
        step: str,
        missing_required_fields: list[str],
        blocked_finish: bool,
        errors: list[str],
        warnings: list[str],
    ) -> ChatAgentReply:
        if self.entry_creation_agent is None:
            return _fallback_assistant_reply(
                step=step,
                missing_required_fields=missing_required_fields,
                blocked_finish=blocked_finish,
                offer_schema=self.offer_schema,
            )

        state = {
            "step": step,
            "missing_required_fields": missing_required_fields,
            "can_finish": step == _STEP_ANYTHING_ELSE and len(missing_required_fields) == 0,
            "current_prompt_key": _current_prompt_key_for_step(step),
            "errors": errors,
            "warnings": warnings,
            "structured_payload": session.payload,
            "source_input_type": session.source_input_type,
            "blocked_finish": blocked_finish,
        }
        try:
            start = perf_counter()
            return self.entry_creation_agent.reply(
                transcript=session.messages,
                state=state,
            )
        except EntryCreationAgentError:
            return _fallback_assistant_reply(
                step=step,
                missing_required_fields=missing_required_fields,
                blocked_finish=blocked_finish,
                offer_schema=self.offer_schema,
            )
        finally:
            elapsed_ms = (perf_counter() - start) * 1000
            logger.debug(
                "Entry creation agent reply session_id=%s step=%s elapsed_ms=%.1f",
                session.session_id,
                step,
                elapsed_ms,
            )

    def _parse_and_merge_finish_payload(
        self,
        *,
        session: ConversationSession,
        errors: list[str],
    ) -> None:
        user_messages = _user_messages(session)
        if not user_messages:
            return

        combined_user_text = "\n\n".join(user_messages)
        try:
            start = perf_counter()
            extracted_payload = self.text_parser_agent.parse(combined_user_text)
        except TextParserError as combined_exc:
            logger.warning("Failed to parse combined text: %s", combined_exc)
            # Fallback for local JSON payload inputs without making extra model calls.
            inline_json_payload: dict[str, Any] = {}
            for message in user_messages:
                if not _looks_like_json_object(message):
                    continue
                try:
                    piece = self.text_parser_agent.parse(message)
                except TextParserError:
                    continue
                inline_json_payload = _merge_payloads(inline_json_payload, piece)

            if not inline_json_payload:
                errors.append(
                    "Unable to extract structured offer data from conversation transcript: "
                    f"{combined_exc}"
                )
                return

            session.payload = _merge_payloads(session.payload, inline_json_payload)
            _normalize_payload(session.payload, self.offer_schema)
            return
        finally:
            elapsed_ms = (perf_counter() - start) * 1000
            logger.debug(
                "Text parser combined transcript session_id=%s elapsed_ms=%.1f",
                session.session_id,
                elapsed_ms,
            )

        session.payload = _merge_payloads(session.payload, extracted_payload)
        _normalize_payload(session.payload, self.offer_schema)

    def intake_text_offer(
        self,
        *,
        session_id: str | None,
        action: str,
        message_text: str | None = None,
        source_input_type: str = "text",
    ) -> TextConversationResult:
        session = self._get_or_create_session(session_id)
        session.source_input_type = source_input_type
        errors: list[str] = []
        warnings: list[str] = []

        message = (message_text or "").strip()
        current_prompt_key = _current_prompt_key_for_step(session.step)
        logger.debug(
            "Text intake turn action=%s session_id=%s step=%s source=%s message_length=%s",
            action,
            session.session_id,
            session.step,
            source_input_type,
            len(message),
        )

        if action == "submit":
            _append_message(session, "user", message)
            if current_prompt_key in (_PROMPT_KEY_MONETARY, _PROMPT_KEY_NON_MONETARY) and _is_typed_omission(message):
                warnings.extend(
                    _apply_prompt_omission_defaults(
                        session.payload,
                        current_prompt_key,
                        self.offer_schema,
                    )
                )
                _advance_on_skip(session)
            elif message:
                if len(_missing_required_fields(session.payload, self.offer_schema)) > 0:
                    logger.debug(
                        "Parsing submit text for session_id=%s missing_required=%s",
                        session.session_id,
                        len(_missing_required_fields(session.payload, self.offer_schema)),
                    )
                    try:
                        start = perf_counter()
                        extracted_payload = self.text_parser_agent.parse(message)
                    except TextParserError as exc:
                        logger.warning("Failed to parse text: %s", exc)
                        errors.append(f"Unable to extract structured offer data: {exc}")
                    else:
                        session.payload = _merge_payloads(session.payload, extracted_payload)
                        _normalize_payload(session.payload, self.offer_schema)
                        logger.debug(
                            "Merged parsed submit text for session_id=%s payload_keys=%s",
                            session.session_id,
                            len(session.payload.keys()),
                        )
                    finally:
                        elapsed_ms = (perf_counter() - start) * 1000
                        logger.debug(
                            "Text parser submit session_id=%s elapsed_ms=%.1f",
                            session.session_id,
                            elapsed_ms,
                        )
                if session.step == _STEP_COLLECT_REQUIRED:
                    if len(_missing_required_fields(session.payload, self.offer_schema)) == 0:
                        session.step = _STEP_COLLECT_MONETARY
                elif session.step == _STEP_COLLECT_MONETARY:
                    session.step = _STEP_COLLECT_NON_MONETARY
                elif session.step == _STEP_COLLECT_NON_MONETARY:
                    session.step = _STEP_ANYTHING_ELSE

        elif action == "skip_current":
            warnings.extend(
                _apply_prompt_omission_defaults(
                    session.payload,
                    current_prompt_key,
                    self.offer_schema,
                )
            )
            _advance_on_skip(session)

        elif action == "finish":
            _append_message(session, "user", message)
            self._parse_and_merge_finish_payload(session=session, errors=errors)

            missing_required_fields = _missing_required_fields(session.payload, self.offer_schema)
            if missing_required_fields:
                session.step = _STEP_COLLECT_REQUIRED
                assistant_reply = self._build_assistant_message(
                    session=session,
                    step=session.step,
                    missing_required_fields=missing_required_fields,
                    blocked_finish=True,
                    errors=errors,
                    warnings=warnings,
                )
                assistant_message = assistant_reply.message
                _append_message(session, "assistant", assistant_message)
                logger.debug(
                    "Text intake blocked finish session_id=%s missing_required=%s warnings=%s",
                    session.session_id,
                    len(missing_required_fields),
                    len(warnings),
                )
                return TextConversationResult(
                    session_id=session.session_id,
                    status="blocked_required_fields",
                    assistant_message=assistant_message,
                    step=session.step,
                    can_finish=False,
                    missing_required_fields=missing_required_fields,
                    current_prompt_key=_current_prompt_key_for_step(session.step),
                    errors=errors,
                    warnings=warnings,
                    messages=list(session.messages),
                    offer=None,
                )

            warnings.extend(_fill_optional_defaults(session.payload, self.offer_schema))
            now = datetime.now(UTC).isoformat()
            session.payload.setdefault("offer_meta", {})
            offer_meta = session.payload["offer_meta"]
            if isinstance(offer_meta, dict):
                offer_meta.setdefault("status", "active")
                offer_meta["source_input_type"] = session.source_input_type
                offer_meta.setdefault("created_at", now)
                offer_meta["updated_at"] = now
                offer_meta["schema_version"] = self.offer_schema.version

            validation_errors = _validate_required(session.payload, self.offer_schema)
            if validation_errors:
                session.step = _STEP_COLLECT_REQUIRED
                missing_required_fields = _missing_required_fields(session.payload, self.offer_schema)
                assistant_reply = self._build_assistant_message(
                    session=session,
                    step=session.step,
                    missing_required_fields=missing_required_fields,
                    blocked_finish=True,
                    errors=validation_errors,
                    warnings=warnings,
                )
                assistant_message = assistant_reply.message
                _append_message(session, "assistant", assistant_message)
                logger.debug(
                    "Text intake blocked by validation session_id=%s missing_required=%s warnings=%s",
                    session.session_id,
                    len(missing_required_fields),
                    len(warnings),
                )
                return TextConversationResult(
                    session_id=session.session_id,
                    status="blocked_required_fields",
                    assistant_message=assistant_message,
                    step=session.step,
                    can_finish=False,
                    missing_required_fields=missing_required_fields,
                    current_prompt_key=_current_prompt_key_for_step(session.step),
                    errors=validation_errors,
                    warnings=warnings,
                    messages=list(session.messages),
                    offer=None,
                )

            logger.debug(
                "Final offer payload on finish for session %s:\n%s",
                session.session_id,
                json.dumps(session.payload, indent=2, sort_keys=True, ensure_ascii=True),
            )
            record = self.offer_repository.create(
                company_name=str(_get_path(session.payload, self.offer_schema.company_name_path)),
                role_title=str(_get_path(session.payload, self.offer_schema.role_title_path)),
                payload=session.payload,
            )
            session.step = _STEP_COMPLETED
            assistant_reply = self._build_assistant_message(
                session=session,
                step=_STEP_COMPLETED,
                missing_required_fields=[],
                blocked_finish=False,
                errors=[],
                warnings=warnings,
            )
            assistant_message = assistant_reply.message
            _append_message(session, "assistant", assistant_message)
            messages = list(session.messages)
            del self.text_conversation_sessions[session.session_id]
            logger.debug(
                "Text intake saved offer session_id=%s offer_id=%s warnings=%s",
                session.session_id,
                record.id,
                len(warnings),
            )
            return TextConversationResult(
                session_id=session.session_id,
                status="saved",
                assistant_message=assistant_message,
                step=_STEP_COMPLETED,
                can_finish=True,
                missing_required_fields=[],
                current_prompt_key=None,
                errors=[],
                warnings=warnings,
                messages=messages,
                offer=record,
            )

        missing_required_fields = _missing_required_fields(session.payload, self.offer_schema)
        assistant_reply = self._build_assistant_message(
            session=session,
            step=session.step,
            missing_required_fields=missing_required_fields,
            blocked_finish=False,
            errors=errors,
            warnings=warnings,
        )
        if action in ("submit", "skip_current") and _requested_submit_entry(assistant_reply):
            return self.intake_text_offer(
                session_id=session.session_id,
                action="finish",
                source_input_type=source_input_type,
            )
        assistant_message = assistant_reply.message
        _append_message(session, "assistant", assistant_message)
        logger.debug(
            "Text intake in progress session_id=%s step=%s can_finish=%s missing_required=%s errors=%s warnings=%s",
            session.session_id,
            session.step,
            session.step == _STEP_ANYTHING_ELSE and len(missing_required_fields) == 0,
            len(missing_required_fields),
            len(errors),
            len(warnings),
        )
        return TextConversationResult(
            session_id=session.session_id,
            status="in_progress",
            assistant_message=assistant_message,
            step=session.step,
            can_finish=(session.step == _STEP_ANYTHING_ELSE and len(missing_required_fields) == 0),
            missing_required_fields=missing_required_fields,
            current_prompt_key=_current_prompt_key_for_step(session.step),
            errors=errors,
            warnings=warnings,
            messages=list(session.messages),
            offer=None,
        )

    def intake_audio_offer(
        self,
        *,
        session_id: str | None,
        action: str,
        audio_bytes: bytes | None = None,
        filename: str = "",
        content_type: str | None = None,
    ) -> TextConversationResult:
        logger.debug(
            "Audio intake turn action=%s session_id=%s has_audio=%s",
            action,
            session_id or "<new>",
            audio_bytes is not None,
        )
        session = self._get_or_create_session(session_id)
        session.source_input_type = "audio"

        if action != "submit":
            return self.intake_text_offer(
                session_id=session.session_id,
                action=action,
                source_input_type="audio",
            )

        if not audio_bytes:
            missing_required_fields = _missing_required_fields(session.payload, self.offer_schema)
            assistant_message = "Unable to transcribe audio input: Audio file is empty."
            _append_message(session, "assistant", assistant_message)
            return TextConversationResult(
                session_id=session.session_id,
                status="transcription_failed",
                assistant_message=assistant_message,
                step=session.step,
                can_finish=(session.step == _STEP_ANYTHING_ELSE and len(missing_required_fields) == 0),
                missing_required_fields=missing_required_fields,
                current_prompt_key=_current_prompt_key_for_step(session.step),
                errors=[assistant_message],
                warnings=[],
                messages=list(session.messages),
                offer=None,
            )

        try:
            transcript = self.audio_transcriber.transcribe(
                audio_bytes=audio_bytes,
                filename=filename,
                content_type=content_type,
            )
        except AudioTranscriptionError as exc:
            missing_required_fields = _missing_required_fields(session.payload, self.offer_schema)
            message = f"Unable to transcribe audio input: {exc}"
            logger.warning("Audio transcription failed for session_id=%s: %s", session.session_id, exc)
            _append_message(session, "assistant", message)
            return TextConversationResult(
                session_id=session.session_id,
                status="transcription_failed",
                assistant_message=message,
                step=session.step,
                can_finish=(session.step == _STEP_ANYTHING_ELSE and len(missing_required_fields) == 0),
                missing_required_fields=missing_required_fields,
                current_prompt_key=_current_prompt_key_for_step(session.step),
                errors=[message],
                warnings=[],
                messages=list(session.messages),
                offer=None,
            )
        return self.intake_text_offer(
            session_id=session.session_id,
            action="submit",
            message_text=transcript,
            source_input_type="audio",
        )

    def finalize_intake_session(self, *, session_id: str) -> TextConversationResult:
        session = self._get_existing_session(session_id)
        errors: list[str] = []
        warnings: list[str] = []

        missing_required_fields = _missing_required_fields(session.payload, self.offer_schema)
        if missing_required_fields:
            session.step = _STEP_COLLECT_REQUIRED
            logger.debug(
                "Finalize intake blocked session_id=%s missing_required=%s warnings=%s",
                session.session_id,
                len(missing_required_fields),
                len(warnings),
            )
            return TextConversationResult(
                session_id=session.session_id,
                status="blocked_required_fields",
                assistant_message="",
                step=session.step,
                can_finish=False,
                missing_required_fields=missing_required_fields,
                current_prompt_key=_current_prompt_key_for_step(session.step),
                errors=errors,
                warnings=warnings,
                messages=list(session.messages),
                offer=None,
            )

        warnings.extend(_fill_optional_defaults(session.payload, self.offer_schema))
        now = datetime.now(UTC).isoformat()
        session.payload.setdefault("offer_meta", {})
        offer_meta = session.payload["offer_meta"]
        if isinstance(offer_meta, dict):
            offer_meta.setdefault("status", "active")
            offer_meta["source_input_type"] = session.source_input_type
            offer_meta.setdefault("created_at", now)
            offer_meta["updated_at"] = now
            offer_meta["schema_version"] = self.offer_schema.version

        validation_errors = _validate_required(session.payload, self.offer_schema)
        if validation_errors:
            session.step = _STEP_COLLECT_REQUIRED
            missing_required_fields = _missing_required_fields(session.payload, self.offer_schema)
            logger.debug(
                "Finalize intake validation blocked session_id=%s missing_required=%s warnings=%s",
                session.session_id,
                len(missing_required_fields),
                len(warnings),
            )
            return TextConversationResult(
                session_id=session.session_id,
                status="blocked_required_fields",
                assistant_message="",
                step=session.step,
                can_finish=False,
                missing_required_fields=missing_required_fields,
                current_prompt_key=_current_prompt_key_for_step(session.step),
                errors=validation_errors,
                warnings=warnings,
                messages=list(session.messages),
                offer=None,
            )

        record = self.offer_repository.create(
            company_name=str(_get_path(session.payload, self.offer_schema.company_name_path)),
            role_title=str(_get_path(session.payload, self.offer_schema.role_title_path)),
            payload=session.payload,
        )
        session.step = _STEP_COMPLETED
        messages = list(session.messages)
        del self.text_conversation_sessions[session.session_id]
        logger.debug(
            "Finalize intake saved offer session_id=%s offer_id=%s warnings=%s",
            session.session_id,
            record.id,
            len(warnings),
        )
        return TextConversationResult(
            session_id=session.session_id,
            status="saved",
            assistant_message="",
            step=_STEP_COMPLETED,
            can_finish=True,
            missing_required_fields=[],
            current_prompt_key=None,
            errors=[],
            warnings=warnings,
            messages=messages,
            offer=record,
        )

    def _intake_offer_from_text(
        self,
        *,
        text: str,
        omission_confirmations: dict[str, bool] | None,
        extracted_offer_overrides: dict[str, Any] | None,
        source_input_type: str,
    ) -> IntakeResult:
        try:
            extracted_payload = self.text_parser_agent.parse(text)
        except TextParserError as exc:
            return IntakeResult(
                status="extraction_failed",
                errors=[f"Unable to extract structured offer data: {exc}"],
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        merged_payload = _merge_payloads(extracted_payload, extracted_offer_overrides or {})

        _normalize_payload(merged_payload, self.offer_schema)

        required_errors = _validate_required(merged_payload, self.offer_schema)
        if required_errors:
            return IntakeResult(
                status="blocked_required_fields",
                errors=required_errors,
                warnings=[],
                missing_field_prompts=_collect_missing_prompts(merged_payload, self.offer_schema),
                offer=None,
            )

        merged_payload, warnings, unresolved_optional_prompts = _apply_optional_omissions(
            merged_payload,
            omission_confirmations,
            self.offer_schema,
        )

        if unresolved_optional_prompts:
            return IntakeResult(
                status="missing_information",
                errors=[],
                warnings=[],
                missing_field_prompts=unresolved_optional_prompts,
                offer=None,
            )

        now = datetime.now(UTC).isoformat()
        merged_payload.setdefault("offer_meta", {})
        offer_meta = merged_payload["offer_meta"]
        if isinstance(offer_meta, dict):
            offer_meta.setdefault("status", "active")
            offer_meta["source_input_type"] = source_input_type
            offer_meta.setdefault("created_at", now)
            offer_meta["updated_at"] = now
            offer_meta["schema_version"] = self.offer_schema.version

        record = self.offer_repository.create(
            company_name=str(_get_path(merged_payload, self.offer_schema.company_name_path)),
            role_title=str(_get_path(merged_payload, self.offer_schema.role_title_path)),
            payload=merged_payload,
        )
        logger.info(
            "Saved offer id=%s company=%s role=%s source=%s",
            record.id,
            record.company_name,
            record.role_title,
            source_input_type,
        )

        return IntakeResult(
            status="saved",
            errors=[],
            warnings=warnings,
            missing_field_prompts=[],
            offer=record,
        )

    def list_offers(
        self,
        *,
        sort_by: Literal["created_at", "company_name", "role_title"] = "created_at",
        sort_direction: Literal["asc", "desc"] = "desc",
    ) -> list[OfferRecord]:
        return self.offer_repository.list_all(sort_by=sort_by, sort_direction=sort_direction)

    def get_offer(self, offer_id: str) -> OfferRecord | None:
        return self.offer_repository.get_by_id(offer_id)

    def delete_offer(self, offer_id: str) -> bool:
        return self.offer_repository.delete(offer_id)

    def seed_demo_offers(self) -> list[OfferRecord]:
        created: list[OfferRecord] = []
        for payload in _demo_offer_payloads():
            created.append(
                self.offer_repository.create(
                    company_name=str(payload["company_name"]),
                    role_title=str(payload["role_title"]),
                    payload=payload,
                )
            )
        return created

    def update_offer(self, *, offer_id: str, payload: dict[str, Any]) -> IntakeResult:
        existing = self.offer_repository.get_by_id(offer_id)
        if existing is None:
            return IntakeResult(
                status="not_found",
                errors=[f"Offer not found: {offer_id}"],
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        normalized_payload = dict(payload)
        _normalize_payload(normalized_payload, self.offer_schema)

        required_errors = _validate_required(normalized_payload, self.offer_schema)
        if required_errors:
            return IntakeResult(
                status="blocked_required_fields",
                errors=required_errors,
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        updated = self.offer_repository.update(
            offer_id=offer_id,
            company_name=str(_get_path(normalized_payload, self.offer_schema.company_name_path)),
            role_title=str(_get_path(normalized_payload, self.offer_schema.role_title_path)),
            payload=normalized_payload,
        )
        if updated is None:
            return IntakeResult(
                status="not_found",
                errors=[f"Offer not found: {offer_id}"],
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        return IntakeResult(
            status="saved",
            errors=[],
            warnings=[],
            missing_field_prompts=[],
            offer=updated,
        )

    def render_offer_payload(self, record: OfferRecord) -> dict[str, Any]:
        payload = _record_to_payload(record, self.offer_schema)
        payload["derived_monetary"] = compute_derived_monetary_summary(
            payload,
            tax_config=self.tax_config,
        ).as_payload()
        return payload

    def get_offer_schema(self) -> dict[str, Any]:
        return self.offer_schema.as_public_payload()
