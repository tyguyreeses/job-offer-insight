import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Navbar } from "../components/Navbar";
import { createBrowserAudioRecorder, type AudioRecorderController } from "../services/audioRecorder";
import { sendAudioTurn, sendTextTurn } from "../services/offersApi";
import type { ConversationMessage, IntakeAction, TextTurnResponse } from "../types/intake";

type ModeState = "chooser" | "chooser-exit" | "text" | "audio";
type AudioLabelPhase = "steady" | "fade-out" | "fade-in";

export function AddEntryPage(): JSX.Element {
  const [mode, setMode] = useState<ModeState>("chooser");
  const [inputText, setInputText] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversation, setConversation] = useState<TextTurnResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudioBlob, setRecordedAudioBlob] = useState<Blob | null>(null);
  const [recordingFailureCount, setRecordingFailureCount] = useState(0);
  const [audioCentered, setAudioCentered] = useState(false);
  const [audioSubmitFailed, setAudioSubmitFailed] = useState(false);
  const [audioButtonLabel, setAudioButtonLabel] = useState("Audio");
  const [audioLabelPhase, setAudioLabelPhase] = useState<AudioLabelPhase>("steady");
  const audioRecorderRef = useRef<AudioRecorderController | null>(null);
  const audioCenteringTimeoutRef = useRef<number | null>(null);
  const audioLabelTimeoutsRef = useRef<number[]>([]);

  useEffect(() => {
    return () => {
      if (audioCenteringTimeoutRef.current !== null) {
        window.clearTimeout(audioCenteringTimeoutRef.current);
      }
      for (const timeoutId of audioLabelTimeoutsRef.current) {
        window.clearTimeout(timeoutId);
      }
    };
  }, []);

  const transcript = useMemo<ConversationMessage[]>(
    () => conversation?.messages ?? [],
    [conversation?.messages]
  );

  const transitionAudioLabel = (nextLabel: string): void => {
    if (audioButtonLabel === nextLabel) {
      return;
    }
    for (const timeoutId of audioLabelTimeoutsRef.current) {
      window.clearTimeout(timeoutId);
    }
    audioLabelTimeoutsRef.current = [];

    setAudioLabelPhase("fade-out");

    const swapTimeout = window.setTimeout(() => {
      setAudioButtonLabel(nextLabel);
      setAudioLabelPhase("fade-in");
    }, 120);
    audioLabelTimeoutsRef.current.push(swapTimeout);

    const settleTimeout = window.setTimeout(() => {
      setAudioLabelPhase("steady");
      audioLabelTimeoutsRef.current = [];
    }, 260);
    audioLabelTimeoutsRef.current.push(settleTimeout);
  };

  const startMode = (targetMode: "text" | "audio"): void => {
    if (mode !== "chooser") {
      return;
    }

    if (targetMode === "audio") {
      setMode("audio");
      setAudioCentered(false);
      if (audioCenteringTimeoutRef.current !== null) {
        window.clearTimeout(audioCenteringTimeoutRef.current);
      }
      audioCenteringTimeoutRef.current = window.setTimeout(() => {
        setAudioCentered(true);
        transitionAudioLabel("Record");
      }, 20);
      return;
    }

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

  const submitAudioBlob = async (blob: Blob): Promise<void> => {
    setIsSubmitting(true);
    setErrorText(null);
    setAudioSubmitFailed(false);
    try {
      const requestPayload = new FormData();
      requestPayload.append("action", "submit");
      if (sessionId) {
        requestPayload.append("session_id", sessionId);
      }
      requestPayload.append(
        "audio_file",
        new File([blob], "entry.webm", {
          type: blob.type || "audio/webm"
        })
      );

      const response = await sendAudioTurn(requestPayload);
      setConversation(response);
      setSessionId(response.session_id);
      setRecordedAudioBlob(null);
      setRecordingFailureCount(0);
    } catch (error) {
      setAudioSubmitFailed(true);
      setRecordingFailureCount((count) => count + 1);
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
      setAudioSubmitFailed(false);
      setIsRecording(true);
    } catch (error) {
      setRecordingFailureCount((count) => count + 1);
      setErrorText(error instanceof Error ? error.message : "Unable to start recording.");
    }
  };

  const stopRecordingAndSubmit = async (): Promise<void> => {
    const recorder = audioRecorderRef.current;
    if (!recorder) {
      return;
    }
    try {
      const blob = await recorder.stop();
      setRecordedAudioBlob(blob);
      setRecordingFailureCount(0);
      await submitAudioBlob(blob);
    } catch (error) {
      setRecordingFailureCount((count) => count + 1);
      setErrorText(error instanceof Error ? error.message : "Unable to finish recording.");
    } finally {
      audioRecorderRef.current = null;
      setIsRecording(false);
    }
  };

  const handleAudioControlClick = async (): Promise<void> => {
    if (isSubmitting) {
      return;
    }

    if (isRecording) {
      await stopRecordingAndSubmit();
      return;
    }

    if (audioSubmitFailed && recordedAudioBlob) {
      await submitAudioBlob(recordedAudioBlob);
      return;
    }

    await beginRecording();
  };

  const handleAudioTurn = async (action: Exclude<IntakeAction, "submit">): Promise<void> => {
    setIsSubmitting(true);
    setErrorText(null);
    try {
      const requestPayload = new FormData();
      requestPayload.append("action", action);
      if (sessionId) {
        requestPayload.append("session_id", sessionId);
      }

      const response = await sendAudioTurn(requestPayload);
      setConversation(response);
      setSessionId(response.session_id);
      setRecordingFailureCount(0);
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unable to process your request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const desiredAudioLabel = useMemo(() => {
    if (mode !== "audio") {
      return "Audio";
    }
    if (isSubmitting) {
      return "Processing...";
    }
    if (isRecording) {
      return "Stop";
    }
    if (audioSubmitFailed && recordedAudioBlob) {
      return "Retry";
    }
    return "Record";
  }, [audioSubmitFailed, isRecording, isSubmitting, mode, recordedAudioBlob]);

  useEffect(() => {
    transitionAudioLabel(desiredAudioLabel);
  }, [desiredAudioLabel]);

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

        {mode === "chooser" || mode === "chooser-exit" || mode === "audio" ? (
          <section
            className={`mode-switcher ${mode === "chooser-exit" ? "motion-fade-exit" : "motion-fade-enter"} ${
              mode === "audio" ? "audio-mode-switcher" : ""
            }`}
            style={
              {
                ["--motion-delay" as string]: mode === "chooser-exit" ? "0ms" : "80ms",
                ["--motion-duration" as string]: mode === "chooser-exit" ? "180ms" : "220ms"
              } as CSSProperties
            }
          >
            <button
              type="button"
              className={`mode-button selectable ${mode === "audio" ? "audio-text-fade" : ""}`}
              onClick={() => startMode("text")}
              disabled={mode === "audio" || isRecording || isSubmitting}
            >
              Text
            </button>
            <button
              type="button"
              className={`mode-button selectable audio-main-button ${mode === "audio" ? "audio-main-active" : ""} ${
                audioCentered ? "audio-main-centered" : ""
              } ${isRecording ? "audio-main-recording" : ""} ${isSubmitting ? "audio-main-processing" : ""}`}
              onClick={() => {
                if (mode === "chooser") {
                  startMode("audio");
                  return;
                }
                void handleAudioControlClick();
              }}
              disabled={mode === "audio" && isSubmitting}
              aria-label={audioButtonLabel}
            >
              <span className={`audio-main-label audio-main-label-${audioLabelPhase}`}>{audioButtonLabel}</span>
            </button>
          </section>
        ) : (
          <section
            className="conversation-panel motion-fade-enter"
            style={{ ["--motion-delay" as string]: "80ms", ["--motion-duration" as string]: "220ms" }}
          >
            {transcript.length > 0 ? (
              <div className="transcript-panel">
                {transcript.map((entry, index) => (
                  <div
                    key={`${entry.role}-${index}-${entry.content.slice(0, 16)}`}
                    className={`assistant-message transcript-message transcript-message-${entry.role} motion-fade-enter`}
                    style={{
                      ["--motion-delay" as string]: "0ms",
                      ["--motion-duration" as string]: "200ms",
                      ["--motion-from-y" as string]: "6px"
                    }}
                  >
                    {entry.content}
                  </div>
                ))}
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
                onClick={() => void handleTextTurn("submit")}
                disabled={isSubmitting || inputText.trim().length === 0}
              >
                Submit
              </button>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() => void handleTextTurn("skip_current")}
                disabled={isSubmitting}
              >
                Skip
              </button>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() => void handleTextTurn("finish")}
                disabled={isSubmitting || !conversation?.can_finish}
              >
                Finish
              </button>
            </div>

            <p className="edit-later-note">You will be able to edit this information later.</p>
          </section>
        )}

        {mode === "audio" ? (
          <section
            className="conversation-panel audio-conversation-panel motion-fade-enter"
            style={{ ["--motion-delay" as string]: "120ms", ["--motion-duration" as string]: "220ms" }}
          >
            {transcript.length > 0 ? (
              <div className="transcript-panel">
                {transcript.map((entry, index) => (
                  <div
                    key={`${entry.role}-${index}-${entry.content.slice(0, 16)}`}
                    className={`assistant-message transcript-message transcript-message-${entry.role} motion-fade-enter`}
                    style={{
                      ["--motion-delay" as string]: "0ms",
                      ["--motion-duration" as string]: "200ms",
                      ["--motion-from-y" as string]: "6px"
                    }}
                  >
                    {entry.content}
                  </div>
                ))}
              </div>
            ) : null}

            {errorText ? <p className="error-text">{errorText}</p> : null}

            <div className="action-row">
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() => void handleAudioTurn("skip_current")}
                disabled={isSubmitting}
              >
                Skip
              </button>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() => void handleAudioTurn("finish")}
                disabled={isSubmitting || !conversation?.can_finish}
              >
                Finish
              </button>
            </div>

            {recordingFailureCount >= 2 ? (
              <button
                type="button"
                className="secondary-button selectable switch-mode-button"
                onClick={() => {
                  setMode("text");
                  setErrorText(null);
                  setAudioCentered(false);
                  setAudioSubmitFailed(false);
                  setAudioButtonLabel("Audio");
                  setAudioLabelPhase("steady");
                }}
              >
                Switch to Text Input
              </button>
            ) : null}

            <p className="edit-later-note">You will be able to edit this information later.</p>
          </section>
        ) : null}
      </main>
    </div>
  );
}
