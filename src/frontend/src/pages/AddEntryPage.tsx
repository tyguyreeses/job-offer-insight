import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Navbar } from "../components/Navbar";
import { createBrowserAudioRecorder, type AudioRecorderController } from "../services/audioRecorder";
import { sendAudioTurn, sendTextTurn } from "../services/offersApi";
import type { IntakeAction, TextTurnResponse } from "../types/intake";

interface AssistantMessage {
  id: number;
  text: string;
}

type ModeState = "chooser" | "chooser-exit" | "text" | "audio";
type EntryMode = "text" | "audio";

export function AddEntryPage(): JSX.Element {
  const [mode, setMode] = useState<ModeState>("chooser");
  const [entryMode, setEntryMode] = useState<EntryMode>("text");
  const [inputText, setInputText] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversation, setConversation] = useState<TextTurnResponse | null>(null);
  const [assistantMessages, setAssistantMessages] = useState<AssistantMessage[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudioBlob, setRecordedAudioBlob] = useState<Blob | null>(null);
  const [recordingFailureCount, setRecordingFailureCount] = useState(0);
  const audioRecorderRef = useRef<AudioRecorderController | null>(null);

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

  const startMode = (targetMode: EntryMode): void => {
    if (mode !== "chooser") {
      return;
    }
    setEntryMode(targetMode);
    setMode("chooser-exit");
    window.setTimeout(() => {
      setMode(targetMode);
    }, 180);
  };

  const handleTextTurn = async (action: IntakeAction): Promise<void> => {
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

  const beginRecording = async (): Promise<void> => {
    setErrorText(null);
    try {
      const recorder = await createBrowserAudioRecorder();
      audioRecorderRef.current = recorder;
      await recorder.start();
      setRecordedAudioBlob(null);
      setIsRecording(true);
    } catch (error) {
      setRecordingFailureCount((count) => count + 1);
      setErrorText(error instanceof Error ? error.message : "Unable to start recording.");
    }
  };

  const endRecording = async (): Promise<void> => {
    const recorder = audioRecorderRef.current;
    if (!recorder) {
      return;
    }
    try {
      const blob = await recorder.stop();
      setRecordedAudioBlob(blob);
      setRecordingFailureCount(0);
    } catch (error) {
      setRecordingFailureCount((count) => count + 1);
      setErrorText(error instanceof Error ? error.message : "Unable to finish recording.");
    } finally {
      audioRecorderRef.current = null;
      setIsRecording(false);
    }
  };

  const handleAudioTurn = async (action: IntakeAction): Promise<void> => {
    setIsSubmitting(true);
    setErrorText(null);
    try {
      const requestPayload = new FormData();
      requestPayload.append("action", action);
      if (sessionId) {
        requestPayload.append("session_id", sessionId);
      }
      if (action === "submit") {
        if (!recordedAudioBlob) {
          throw new Error("Record audio before submitting.");
        }
        requestPayload.append(
          "audio_file",
          new File([recordedAudioBlob], "entry.webm", {
            type: recordedAudioBlob.type || "audio/webm",
          })
        );
      }

      const response = await sendAudioTurn(requestPayload);
      setConversation(response);
      setSessionId(response.session_id);
      if (action === "submit") {
        setRecordedAudioBlob(null);
      }
      setRecordingFailureCount(0);
    } catch (error) {
      if (action === "submit") {
        setRecordingFailureCount((count) => count + 1);
      }
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

        {mode === "chooser" || mode === "chooser-exit" ? (
          <section
            className={`mode-switcher ${mode === "chooser-exit" ? "motion-fade-exit" : "motion-fade-enter"}`}
            style={
              {
                ["--motion-delay" as string]: mode === "chooser-exit" ? "0ms" : "80ms",
                ["--motion-duration" as string]: mode === "chooser-exit" ? "180ms" : "220ms"
              } as CSSProperties
            }
          >
            <button type="button" className="mode-button selectable" onClick={() => startMode("text")}>
              Text
            </button>
            <button type="button" className="mode-button selectable" onClick={() => startMode("audio")}>
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

            {entryMode === "text" ? (
              <>
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
              </>
            ) : (
              <div className="audio-recorder-panel">
                <p className="input-label">Record details</p>
                <div className="audio-recorder-row">
                  <button
                    type="button"
                    className="action-button selectable"
                    onClick={() => void beginRecording()}
                    disabled={isSubmitting || isRecording}
                  >
                    Start Recording
                  </button>
                  <button
                    type="button"
                    className="secondary-button selectable"
                    onClick={() => void endRecording()}
                    disabled={isSubmitting || !isRecording}
                  >
                    Stop Recording
                  </button>
                </div>
                {isRecording ? (
                  <p className="recording-indicator" role="status">
                    <span className="recording-dot" /> Recording...
                  </p>
                ) : null}
                {recordedAudioBlob ? (
                  <p className="recording-ready" role="status">
                    Recording captured and ready to submit.
                  </p>
                ) : null}
              </div>
            )}

            {errorText ? <p className="error-text">{errorText}</p> : null}

            <div className="action-row">
              <button
                type="button"
                className="action-button selectable"
                onClick={() =>
                  void (entryMode === "text" ? handleTextTurn("submit") : handleAudioTurn("submit"))
                }
                disabled={
                  isSubmitting ||
                  (entryMode === "text" ? inputText.trim().length === 0 : recordedAudioBlob === null) ||
                  isRecording
                }
              >
                Submit
              </button>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() =>
                  void (entryMode === "text"
                    ? handleTextTurn("skip_current")
                    : handleAudioTurn("skip_current"))
                }
                disabled={isSubmitting}
              >
                Skip
              </button>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() =>
                  void (entryMode === "text" ? handleTextTurn("finish") : handleAudioTurn("finish"))
                }
                disabled={isSubmitting || !conversation?.can_finish}
              >
                Finish
              </button>
            </div>
            {entryMode === "audio" && recordingFailureCount >= 2 ? (
              <button
                type="button"
                className="secondary-button selectable switch-mode-button"
                onClick={() => {
                  setEntryMode("text");
                  setMode("text");
                  setErrorText(null);
                }}
              >
                Switch to Text Input
              </button>
            ) : null}

            <p className="edit-later-note">You will be able to edit this information later.</p>
          </section>
        )}
      </main>
    </div>
  );
}
