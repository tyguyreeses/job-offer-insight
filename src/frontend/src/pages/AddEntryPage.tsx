import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import { createBrowserAudioRecorder, type AudioRecorderController } from "../services/audioRecorder";
import { finalizeIntakeSession, sendAudioTurn, sendTextTurn } from "../services/offersApi";
import type { IntakeAction, TextTurnResponse } from "../types/intake";

type ModeState = "chooser" | "chooser-exit" | "text" | "audio";
type AudioLabelPhase = "steady" | "fade-out" | "fade-in";

function ProcessingLabel({ label }: { label: string }): JSX.Element {
  return (
    <span className="processing-label">
      {label.split("").map((character, index) => (
        <span
          key={`processing-char-${index}-${character === " " ? "space" : character}`}
          className="processing-label-char"
          style={{ ["--processing-index" as string]: index } as CSSProperties}
        >
          {character}
        </span>
      ))}
    </span>
  );
}

function AssistantMessagePanel({ message }: { message: string }): JSX.Element | null {
  if (!message) {
    return null;
  }
  return (
    <div className="transcript-panel">
      <div
        className="assistant-message transcript-message transcript-message-assistant motion-fade-enter"
        style={
          {
            ["--motion-delay" as string]: "0ms",
            ["--motion-duration" as string]: "200ms",
            ["--motion-from-y" as string]: "6px"
          } as CSSProperties
        }
      >
        {message}
      </div>
    </div>
  );
}

interface AddEntryPageProps {
  onOfferSaved?: () => void;
  onProcessingStateChange?: (isProcessing: boolean) => void;
}

export function AddEntryPage({ onOfferSaved, onProcessingStateChange }: AddEntryPageProps): JSX.Element {
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

  const latestAssistantMessage = useMemo(() => {
    return conversation?.assistant_message?.trim() ?? "";
  }, [conversation?.assistant_message]);

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

  const enterAudioMode = (): void => {
    setMode("audio");
    setAudioCentered(false);
    if (audioCenteringTimeoutRef.current !== null) {
      window.clearTimeout(audioCenteringTimeoutRef.current);
    }
    audioCenteringTimeoutRef.current = window.setTimeout(() => {
      setAudioCentered(true);
      transitionAudioLabel("Record");
    }, 20);
  };

  const handleSwitchToAudio = (): void => {
    if (isSubmitting || isRecording) {
      return;
    }
    enterAudioMode();
  };

  const handleSwitchToText = (): void => {
    if (isSubmitting || isRecording) {
      return;
    }
    setMode("text");
    setAudioCentered(false);
    setAudioSubmitFailed(false);
    setRecordedAudioBlob(null);
    setRecordingFailureCount(0);
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
      if (response.status === "saved") {
        onOfferSaved?.();
      }
      if (action === "submit") {
        setInputText("");
      }
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unable to process your request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinalize = async (): Promise<void> => {
    if (!sessionId) {
      setErrorText("Unable to finish: missing session.");
      return;
    }
    const missingRequiredFields = conversation?.missing_required_fields ?? [];
    if (missingRequiredFields.length > 0) {
      setErrorText(`Please fill required fields: ${missingRequiredFields.join(", ")}.`);
      return;
    }

    setIsSubmitting(true);
    setErrorText(null);
    try {
      const response = await finalizeIntakeSession(sessionId);
      setConversation(response);
      setSessionId(response.session_id);
      if (response.status === "saved") {
        onOfferSaved?.();
      } else if (response.status === "blocked_required_fields" && response.missing_required_fields.length > 0) {
        setErrorText(`Please fill required fields: ${response.missing_required_fields.join(", ")}.`);
      }
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Unable to finish your entry.");
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
      if (response.status === "saved") {
        onOfferSaved?.();
      }
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

  useEffect(() => {
    onProcessingStateChange?.(isSubmitting);
    return () => {
      onProcessingStateChange?.(false);
    };
  }, [isSubmitting, onProcessingStateChange]);

  const isProcessingLabel = audioButtonLabel === "Processing...";

  return (
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
              <span
                className={`audio-main-label audio-main-label-${audioLabelPhase} ${
                  isProcessingLabel ? "audio-main-label-processing" : ""
                }`}
              >
                {isProcessingLabel ? <ProcessingLabel label={audioButtonLabel} /> : audioButtonLabel}
              </span>
            </button>
          </section>
        ) : (
          <section
            className="conversation-panel motion-fade-enter"
            style={{ ["--motion-delay" as string]: "80ms", ["--motion-duration" as string]: "220ms" }}
          >
            <AssistantMessagePanel message={latestAssistantMessage} />

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
              disabled={isSubmitting}
            />

            {isSubmitting ? (
              <p className="text-processing-indicator motion-fade-enter" role="status" aria-live="polite">
                <ProcessingLabel label="Processing your input..." />
              </p>
            ) : null}

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
                onClick={handleSwitchToAudio}
                disabled={isSubmitting || isRecording}
              >
                Switch to Audio Input
              </button>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() => void handleFinalize()}
                disabled={isSubmitting || !sessionId}
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
            <AssistantMessagePanel message={latestAssistantMessage} />

            {errorText ? <p className="error-text">{errorText}</p> : null}

            <div className="action-row">
              <button
                type="button"
                className="secondary-button selectable"
                onClick={handleSwitchToText}
                disabled={isSubmitting || isRecording}
              >
                Switch to Text Input
              </button>
              <button
                type="button"
                className="secondary-button selectable"
                onClick={() => void handleFinalize()}
                disabled={isSubmitting || !sessionId}
              >
                Finish
              </button>
            </div>

            <p className="edit-later-note">You will be able to edit this information later.</p>
          </section>
        ) : null}
    </main>
  );
}
