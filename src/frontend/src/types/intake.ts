export type IntakeAction = "submit" | "skip_current" | "finish";

export interface TextTurnRequest {
  session_id: string | null;
  action: IntakeAction;
  message_text?: string;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export interface TextTurnResponse {
  session_id: string;
  status:
    | "in_progress"
    | "blocked_required_fields"
    | "saved"
    | "extraction_failed"
    | "transcription_failed";
  assistant_message: string;
  step:
    | "collect_required"
    | "collect_monetary_extras"
    | "collect_non_monetary_extras"
    | "anything_else"
    | "completed";
  can_finish: boolean;
  missing_required_fields: string[];
  current_prompt_key: string | null;
  errors: string[];
  warnings: string[];
  messages: ConversationMessage[];
  offer: Record<string, unknown> | null;
}
