import { useEffect, useMemo, useState } from "react";

import { Navbar } from "../components/Navbar";
import { sendTextTurn } from "../services/offersApi";
import type { IntakeAction, TextTurnResponse } from "../types/intake";

interface AssistantMessage {
  id: number;
  text: string;
}

type ModeState = "chooser" | "chooser-exit" | "text";

export function AddEntryPage(): JSX.Element {
  const [mode, setMode] = useState<ModeState>("chooser");
  const [inputText, setInputText] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversation, setConversation] = useState<TextTurnResponse | null>(null);
  const [assistantMessages, setAssistantMessages] = useState<AssistantMessage[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  useEffect(() => {
    if (conversation?.assistant_message) {
      setAssistantMessages((previous) => [
        ...previous,
        {
          id: previous.length + 1,
          text: conversation.assistant_message
        }
      ]);
    }
  }, [conversation?.assistant_message]);

  const latestAssistantMessage = useMemo(
    () => assistantMessages[assistantMessages.length - 1] ?? null,
    [assistantMessages]
  );

  const startTextMode = (): void => {
    if (mode !== "chooser") {
      return;
    }
    setMode("chooser-exit");
    window.setTimeout(() => {
      setMode("text");
    }, 180);
  };

  const handleTurn = async (action: IntakeAction): Promise<void> => {
    setIsSubmitting(true);
    setErrorText(null);
    try {
      const messageText = inputText.trim();
      const requestPayload = {
        session_id: sessionId,
        action,
        ...(action === "submit" || (action === "finish" && messageText)
          ? { message_text: messageText }
          : {})
      };
      const response = await sendTextTurn(requestPayload);
      setConversation(response);
      setSessionId(response.session_id);
      if (action === "submit") {
        setInputText("");
      }
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unable to process your request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="app-shell">
      <Navbar />
      <main className="main-panel">
        <h1
          className="main-title motion-fade-enter"
          style={{ ["--motion-delay" as string]: "0ms", ["--motion-duration" as string]: "220ms" }}
        >
          Create a Job Entry
        </h1>

        {mode !== "text" ? (
          <section
            className={`mode-switcher ${mode === "chooser-exit" ? "motion-fade-exit" : "motion-fade-enter"}`}
            style={
              {
                ["--motion-delay" as string]: mode === "chooser-exit" ? "0ms" : "80ms",
                ["--motion-duration" as string]: mode === "chooser-exit" ? "180ms" : "220ms"
              } as React.CSSProperties
            }
          >
            <button type="button" className="mode-button selectable" onClick={startTextMode}>
              Text
            </button>
            <button type="button" className="mode-button selectable" aria-disabled="true">
              Audio
            </button>
          </section>
        ) : (
          <section
            className="conversation-panel motion-fade-enter"
            style={{ ["--motion-delay" as string]: "80ms", ["--motion-duration" as string]: "220ms" }}
          >
            {latestAssistantMessage ? (
              <div
                className="assistant-message motion-fade-enter"
                style={{
                  ["--motion-delay" as string]: "0ms",
                  ["--motion-duration" as string]: "200ms",
                  ["--motion-from-y" as string]: "6px"
                }}
              >
                {latestAssistantMessage.text}
              </div>
            ) : null}

            <label className="input-label" htmlFor="job-entry-text">
              Add details
            </label>
            <textarea
              id="job-entry-text"
              className="job-entry-input selectable"
              value={inputText}
              onChange={(event) => setInputText(event.target.value)}
              placeholder="Paste or type offer details here..."
              rows={6}
            />

            {errorText ? <p className="error-text">{errorText}</p> : null}

            <div className="action-row">
              <button
                type="button"
                className="action-button selectable"
                onClick={() => void handleTurn("submit")}
                disabled={isSubmitting || inputText.trim().length === 0}
              >
                Submit
              </button>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() => void handleTurn("skip_current")}
                disabled={isSubmitting}
              >
                Skip
              </button>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() => void handleTurn("finish")}
                disabled={isSubmitting || !conversation?.can_finish}
              >
                Finish
              </button>
            </div>

            <p className="edit-later-note">You will be able to edit this information later.</p>
          </section>
        )}
      </main>
    </div>
  );
}
