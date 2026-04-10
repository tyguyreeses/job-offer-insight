"""Offer intake and CRUD orchestration for Stage 5.1."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from ...domain.models import OfferRecord
from ...gen_ai.audio_transcriber import AudioTranscriptionError
from ...gen_ai.entry_creation_agent import EntryCreationAgentError
from ...gen_ai.protocols import Agent, AudioTranscriber, ChatAgent, ChatAgentReply
from ...gen_ai.text_parser_agent import TextParserError
from ...storage.repositories.interfaces import OfferRepository
from ...utils.logging import get_logger

logger = get_logger(__name__)

_REQUIRED_COMPENSATION_PATHS = (
    "compensation.annual_base_salary_usd",
    "compensation.hourly_rate_usd",
    "compensation.hours_per_week",
)

_REQUIRED_FIELD_PATHS = (
    "company_name",
    "role_title",
    "location",
    *_REQUIRED_COMPENSATION_PATHS,
)

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
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, list):
        return len(value) > 0
    return True


def _set_path(payload: dict[str, Any], path: str, value: Any) -> None:
    cursor = payload
    parts = path.split(".")
    for part in parts[:-1]:
        child = cursor.get(part)
        if not isinstance(child, dict):
            child = {}
            cursor[part] = child
        cursor = child
    cursor[parts[-1]] = value


def _get_path(payload: dict[str, Any], path: str) -> Any:
    cursor: Any = payload
    for part in path.split("."):
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(part)
    return cursor


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned == "":
            return None
        if cleaned.startswith("$"):
            cleaned = cleaned[1:]
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _merge_payloads(*parts: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for part in parts:
        for key, value in part.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = _merge_payloads(merged[key], value)
            else:
                merged[key] = value
    return merged


def _normalize_compensation(payload: dict[str, Any]) -> None:
    compensation = payload.get("compensation")
    if compensation is None:
        compensation = {}
        payload["compensation"] = compensation
    if not isinstance(compensation, dict):
        raise ValueError("compensation must be an object")

    annual_base = _coerce_float(compensation.get("annual_base_salary_usd"))
    hourly_rate = _coerce_float(compensation.get("hourly_rate_usd"))
    hours_per_week = _coerce_float(compensation.get("hours_per_week"))

    if annual_base is not None:
        compensation["annual_base_salary_usd"] = annual_base
    if hourly_rate is not None:
        compensation["hourly_rate_usd"] = hourly_rate
    if hours_per_week is not None:
        compensation["hours_per_week"] = hours_per_week

    if annual_base is None and hourly_rate is not None and hours_per_week is not None:
        compensation["annual_base_salary_usd"] = hourly_rate * hours_per_week * 52


_OPTIONAL_FIELD_DEFAULTS: dict[str, Any] = {
    "employment_type": "",
    "work_model": "",
    "compensation.signing_bonus_usd": None,
    "compensation.target_bonus_percent": None,
    "monetary_benefits.retirement_match_percent": None,
    "monetary_benefits.retirement_match_cap_usd": None,
    "monetary_benefits.health_insurance_employer_monthly_usd": None,
    "monetary_benefits.hsa_employer_annual_usd": None,
    "monetary_benefits.equity_grant_usd": None,
    "monetary_benefits.equity_vesting_schedule": "",
    "monetary_benefits.other_monetary_benefits": [],
    "non_monetary_benefits.mission_alignment_notes": "",
    "non_monetary_benefits.culture_notes": "",
    "non_monetary_benefits.growth_notes": "",
    "non_monetary_benefits.wellness_notes": "",
    "non_monetary_benefits.pto_days": None,
    "non_monetary_benefits.remote_flexibility_notes": "",
    "non_monetary_benefits.other_non_monetary_benefits": [],
}


def _has_required_compensation(payload: dict[str, Any]) -> bool:
    annual_base = _coerce_float(_get_path(payload, "compensation.annual_base_salary_usd"))
    hourly_rate = _coerce_float(_get_path(payload, "compensation.hourly_rate_usd"))
    hours_per_week = _coerce_float(_get_path(payload, "compensation.hours_per_week"))
    return annual_base is not None or (hourly_rate is not None and hours_per_week is not None)


def _missing_core_required_fields(payload: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not _is_present(payload.get("company_name")):
        missing.append("company_name")
    if not _is_present(payload.get("role_title")):
        missing.append("role_title")
    if not _is_present(payload.get("location")):
        missing.append("location")
    return missing


def _collect_missing_prompts(payload: dict[str, Any]) -> list[FieldPrompt]:
    prompts: list[FieldPrompt] = []

    for path in _missing_core_required_fields(payload):
        prompts.append(
            FieldPrompt(
                path=path,
                required=True,
                message=f"Provide {path} to save this offer.",
            )
        )

    if not _has_required_compensation(payload):
        for path in _REQUIRED_COMPENSATION_PATHS:
            prompts.append(
                FieldPrompt(
                    path=path,
                    required=True,
                    message="Provide required base-pay information to save this offer.",
                )
            )

    for path in _OPTIONAL_FIELD_DEFAULTS:
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
) -> tuple[dict[str, Any], list[str], list[FieldPrompt]]:
    confirmations = omission_confirmations or {}
    warnings: list[str] = []
    unresolved_prompts: list[FieldPrompt] = []

    for path, default_value in _OPTIONAL_FIELD_DEFAULTS.items():
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


def _fill_optional_defaults(payload: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for path, default_value in _OPTIONAL_FIELD_DEFAULTS.items():
        if _is_present(_get_path(payload, path)):
            continue
        _set_path(payload, path, default_value)
        warnings.append(f"Stored blank value for omitted field: {path}")
    return warnings


def _validate_required(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path in _missing_core_required_fields(payload):
        errors.append(f"{path} is required")
    if not _has_required_compensation(payload):
        errors.append(
            "Provide compensation.annual_base_salary_usd or both compensation.hourly_rate_usd and compensation.hours_per_week"
        )

    return errors


def _record_to_payload(record: OfferRecord) -> dict[str, Any]:
    payload = dict(record.payload)
    payload["id"] = record.id
    payload["company_name"] = record.company_name
    payload["role_title"] = record.role_title
    payload.setdefault("offer_meta", {})
    offer_meta = payload["offer_meta"]
    if isinstance(offer_meta, dict):
        offer_meta.setdefault("created_at", record.created_at)
        offer_meta["updated_at"] = record.updated_at
    return payload


def _missing_required_fields(payload: dict[str, Any]) -> list[str]:
    missing = _missing_core_required_fields(payload)
    if not _has_required_compensation(payload):
        missing.extend(_REQUIRED_COMPENSATION_PATHS)
    return missing


def _required_list_text(missing_required_fields: list[str]) -> str:
    ordered: list[str] = []
    for path in _REQUIRED_FIELD_PATHS:
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


def _assistant_message_for_step(step: str, missing_required_fields: list[str]) -> str:
    if step == _STEP_COLLECT_REQUIRED:
        required_list = _required_list_text(missing_required_fields)
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
            "Any additional non-monetary benefits to include (for example culture, mission "
            "alignment, wellness/perks)? If none, you can skip."
        )
    if step == _STEP_ANYTHING_ELSE:
        return "Is there anything else you want to add before saving?"
    if step == _STEP_COMPLETED:
        return "Great, your offer has been saved. You can edit details later."
    return "Please continue."


def _assistant_message_for_blocked_finish(missing_required_fields: list[str]) -> str:
    required_list = _required_list_text(missing_required_fields)
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
) -> str:
    if blocked_finish:
        return _assistant_message_for_blocked_finish(missing_required_fields)
    return _assistant_message_for_step(step, missing_required_fields)


def _fallback_assistant_reply(
    *,
    step: str,
    missing_required_fields: list[str],
    blocked_finish: bool,
) -> ChatAgentReply:
    return ChatAgentReply(
        message=_fallback_assistant_message(
            step=step,
            missing_required_fields=missing_required_fields,
            blocked_finish=blocked_finish,
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


def _apply_prompt_omission_defaults(payload: dict[str, Any], prompt_key: str | None) -> list[str]:
    warnings: list[str] = []
    if prompt_key == _PROMPT_KEY_MONETARY:
        for path, default_value in _OPTIONAL_FIELD_DEFAULTS.items():
            if not path.startswith("monetary_benefits."):
                continue
            if _is_present(_get_path(payload, path)):
                continue
            _set_path(payload, path, default_value)
            warnings.append(f"Stored blank value for omitted field: {path}")
    elif prompt_key == _PROMPT_KEY_NON_MONETARY:
        for path, default_value in _OPTIONAL_FIELD_DEFAULTS.items():
            if not path.startswith("non_monetary_benefits."):
                continue
            if _is_present(_get_path(payload, path)):
                continue
            _set_path(payload, path, default_value)
            warnings.append(f"Stored blank value for omitted field: {path}")
    return warnings


@dataclass
class Stage4OfferService:
    offer_repository: OfferRepository
    text_parser_agent: Agent
    audio_transcriber: AudioTranscriber
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
            return self.entry_creation_agent.reply(
                transcript=session.messages,
                state=state,
            )
        except EntryCreationAgentError:
            return _fallback_assistant_reply(
                step=step,
                missing_required_fields=missing_required_fields,
                blocked_finish=blocked_finish,
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
            _normalize_compensation(session.payload)
            return

        session.payload = _merge_payloads(session.payload, extracted_payload)
        _normalize_compensation(session.payload)

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

        if action == "submit":
            _append_message(session, "user", message)
            if current_prompt_key in (_PROMPT_KEY_MONETARY, _PROMPT_KEY_NON_MONETARY) and _is_typed_omission(message):
                warnings.extend(_apply_prompt_omission_defaults(session.payload, current_prompt_key))
                _advance_on_skip(session)
            elif message:
                if len(_missing_required_fields(session.payload)) > 0:
                    try:
                        extracted_payload = self.text_parser_agent.parse(message)
                    except TextParserError as exc:
                        logger.warning("Failed to parse text: %s", exc)
                        errors.append(f"Unable to extract structured offer data: {exc}")
                    else:
                        session.payload = _merge_payloads(session.payload, extracted_payload)
                        _normalize_compensation(session.payload)
                if session.step == _STEP_COLLECT_REQUIRED:
                    if len(_missing_required_fields(session.payload)) == 0:
                        session.step = _STEP_COLLECT_MONETARY
                elif session.step == _STEP_COLLECT_MONETARY:
                    session.step = _STEP_COLLECT_NON_MONETARY
                elif session.step == _STEP_COLLECT_NON_MONETARY:
                    session.step = _STEP_ANYTHING_ELSE

        elif action == "skip_current":
            warnings.extend(_apply_prompt_omission_defaults(session.payload, current_prompt_key))
            _advance_on_skip(session)

        elif action == "finish":
            _append_message(session, "user", message)
            self._parse_and_merge_finish_payload(session=session, errors=errors)

            missing_required_fields = _missing_required_fields(session.payload)
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

            warnings.extend(_fill_optional_defaults(session.payload))
            now = datetime.now(UTC).isoformat()
            session.payload.setdefault("offer_meta", {})
            offer_meta = session.payload["offer_meta"]
            if isinstance(offer_meta, dict):
                offer_meta.setdefault("status", "active")
                offer_meta["source_input_type"] = session.source_input_type
                offer_meta.setdefault("created_at", now)
                offer_meta["updated_at"] = now

            validation_errors = _validate_required(session.payload)
            if validation_errors:
                session.step = _STEP_COLLECT_REQUIRED
                missing_required_fields = _missing_required_fields(session.payload)
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
                company_name=str(session.payload["company_name"]),
                role_title=str(session.payload["role_title"]),
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

        missing_required_fields = _missing_required_fields(session.payload)
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
            missing_required_fields = _missing_required_fields(session.payload)
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
            missing_required_fields = _missing_required_fields(session.payload)
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

        _normalize_compensation(merged_payload)

        required_errors = _validate_required(merged_payload)
        if required_errors:
            return IntakeResult(
                status="blocked_required_fields",
                errors=required_errors,
                warnings=[],
                missing_field_prompts=_collect_missing_prompts(merged_payload),
                offer=None,
            )

        merged_payload, warnings, unresolved_optional_prompts = _apply_optional_omissions(
            merged_payload,
            omission_confirmations,
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

        record = self.offer_repository.create(
            company_name=str(merged_payload["company_name"]),
            role_title=str(merged_payload["role_title"]),
            payload=merged_payload,
        )
        logger.info(
            "Saved offer id=%s company=%s role=%s source=%s",
            record.offer_id,
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

    def update_offer(self, *, offer_id: str, payload: dict[str, Any]) -> IntakeResult:
        normalized_payload = dict(payload)
        _normalize_compensation(normalized_payload)

        required_errors = _validate_required(normalized_payload)
        if required_errors:
            return IntakeResult(
                status="blocked_required_fields",
                errors=required_errors,
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        existing = self.offer_repository.get_by_id(offer_id)
        if existing is None:
            return IntakeResult(
                status="not_found",
                errors=[f"Offer not found: {offer_id}"],
                warnings=[],
                missing_field_prompts=[],
                offer=None,
            )

        updated = self.offer_repository.update(
            offer_id=offer_id,
            company_name=str(normalized_payload["company_name"]),
            role_title=str(normalized_payload["role_title"]),
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
        return _record_to_payload(record)
