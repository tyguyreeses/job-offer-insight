import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { AddEntryPage } from "./AddEntryPage";
import { createBrowserAudioRecorder } from "../services/audioRecorder";
import { finalizeIntakeSession, sendAudioTurn, sendTextTurn } from "../services/offersApi";

vi.mock("../services/offersApi", () => ({
  sendTextTurn: vi.fn(),
  sendAudioTurn: vi.fn(),
  finalizeIntakeSession: vi.fn()
}));

vi.mock("../services/audioRecorder", () => ({
  createBrowserAudioRecorder: vi.fn()
}));

const mockedSendTextTurn = vi.mocked(sendTextTurn);
const mockedSendAudioTurn = vi.mocked(sendAudioTurn);
const mockedFinalizeIntakeSession = vi.mocked(finalizeIntakeSession);
const mockedCreateBrowserAudioRecorder = vi.mocked(createBrowserAudioRecorder);

const inProgressResponse = {
  session_id: "session-1",
  status: "in_progress" as const,
  assistant_message: "Please share the remaining required information: company_name.",
  step: "collect_required" as const,
  can_finish: false,
  missing_required_fields: ["company_name"],
  current_prompt_key: "required_fields_bundle",
  errors: [],
  warnings: [],
  messages: [
    {
      role: "assistant" as const,
      content: "Please share the remaining required information: company_name."
    }
  ],
  offer: null
};

const readyToFinishResponse = {
  ...inProgressResponse,
  step: "anything_else" as const,
  can_finish: true,
  missing_required_fields: [],
  current_prompt_key: "anything_else"
};

const savedResponse = {
  ...inProgressResponse,
  status: "saved" as const,
  step: "completed" as const,
  can_finish: true,
  missing_required_fields: [],
  current_prompt_key: null,
  offer: {
    id: "offer-1",
    company_name: "Acme",
    role_title: "Engineer"
  }
};

describe("AddEntryPage", () => {
  beforeEach(() => {
    mockedSendTextTurn.mockReset();
    mockedSendAudioTurn.mockReset();
    mockedFinalizeIntakeSession.mockReset();
    mockedCreateBrowserAudioRecorder.mockReset();
  });

  it("renders title and both mode buttons", () => {
    render(<AddEntryPage />);

    expect(screen.getByRole("heading", { name: "Create a Job Entry" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Text" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Audio" })).toBeInTheDocument();
  });

  it("transitions from mode buttons to text input when text is clicked", async () => {
    render(<AddEntryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Text" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Add details")).toBeInTheDocument();
    });
  });

  it("shows transcript messages above text input after submit", async () => {
    mockedSendTextTurn.mockResolvedValueOnce(inProgressResponse);

    render(<AddEntryPage />);
    fireEvent.click(screen.getByRole("button", { name: "Text" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Add details")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Add details"), {
      target: {
        value: "Role title and salary"
      }
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(
        screen.getByText("Please share the remaining required information: company_name.")
      ).toBeInTheDocument();
    });
    expect(screen.getByText("Please share the remaining required information: company_name.")).toHaveClass(
      "transcript-message-assistant"
    );
  });

  it("replaces Skip with switch-to-audio in text mode", async () => {
    render(<AddEntryPage />);
    fireEvent.click(screen.getByRole("button", { name: "Text" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Add details")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Switch to Audio Input" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Skip" })).not.toBeInTheDocument();
  });

  it("shows text processing indicator and disables textarea while submit is in flight", async () => {
    const resolveRequestRef: { current: ((value: typeof inProgressResponse) => void) | null } = {
      current: null
    };
    mockedSendTextTurn.mockImplementation(
      () =>
        new Promise<typeof inProgressResponse>((resolve) => {
          resolveRequestRef.current = resolve;
        })
    );

    render(<AddEntryPage />);
    fireEvent.click(screen.getByRole("button", { name: "Text" }));

    const input = await screen.findByLabelText("Add details");
    fireEvent.change(input, { target: { value: "Role title and salary" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByRole("status")).toHaveTextContent("Processing your input...");
    expect(input).toBeDisabled();

    if (resolveRequestRef.current !== null) {
      resolveRequestRef.current(inProgressResponse);
    }
    await waitFor(() => {
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });
  });

  it("fades text button, centers audio button, and relabels it to Record", async () => {
    render(<AddEntryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Audio" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Record" })).toBeInTheDocument();
    });

    const textButton = screen.getByRole("button", { name: "Text" });
    const recordButton = screen.getByRole("button", { name: "Record" });

    expect(textButton).toHaveClass("audio-text-fade");
    expect(recordButton).toHaveClass("audio-main-centered");
  });

  it("changes Record to Stop with label transition and recording pulse", async () => {
    mockedCreateBrowserAudioRecorder.mockResolvedValue({
      start: vi.fn().mockResolvedValue(undefined),
      stop: vi.fn().mockResolvedValue(new Blob(["audio"], { type: "audio/webm" }))
    });

    render(<AddEntryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Audio" }));

    const recordButton = await screen.findByRole("button", { name: "Record" });
    fireEvent.click(recordButton);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument();
    });

    const stopButton = screen.getByRole("button", { name: "Stop" });
    expect(stopButton).toHaveClass("audio-main-recording");

    const stopLabel = screen.getByText("Stop");
    expect(stopLabel).toHaveClass("audio-main-label-fade-in");
  });

  it("auto-submits audio when Stop is clicked", async () => {
    mockedCreateBrowserAudioRecorder.mockResolvedValue({
      start: vi.fn().mockResolvedValue(undefined),
      stop: vi.fn().mockResolvedValue(new Blob(["audio"], { type: "audio/webm" }))
    });
    mockedSendAudioTurn.mockResolvedValueOnce(inProgressResponse);

    render(<AddEntryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Audio" }));

    fireEvent.click(await screen.findByRole("button", { name: "Record" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Stop" }));

    await waitFor(() => {
      expect(mockedSendAudioTurn).toHaveBeenCalledTimes(1);
      expect(
        screen.getByText("Please share the remaining required information: company_name.")
      ).toBeInTheDocument();
    });

    const requestPayload = mockedSendAudioTurn.mock.calls[0][0];
    expect(requestPayload.get("action")).toBe("submit");
  });

  it("shows Processing while auto-submit is in flight and disables the centered button", async () => {
    mockedCreateBrowserAudioRecorder.mockResolvedValue({
      start: vi.fn().mockResolvedValue(undefined),
      stop: vi.fn().mockResolvedValue(new Blob(["audio"], { type: "audio/webm" }))
    });

    const resolveRequestRef: { current: ((value: typeof inProgressResponse) => void) | null } = {
      current: null
    };
    mockedSendAudioTurn.mockImplementation(
      () =>
        new Promise<typeof inProgressResponse>((resolve) => {
          resolveRequestRef.current = resolve;
        })
    );

    render(<AddEntryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Audio" }));
    fireEvent.click(await screen.findByRole("button", { name: "Record" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Stop" }));

    const processingButton = await screen.findByRole("button", { name: "Processing..." });
    expect(processingButton).toBeDisabled();

    if (resolveRequestRef.current !== null) {
      resolveRequestRef.current(inProgressResponse);
    }
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Record" })).toBeInTheDocument();
    });
  });

  it("shows Retry after auto-submit failure and retries with one tap", async () => {
    mockedCreateBrowserAudioRecorder.mockResolvedValue({
      start: vi.fn().mockResolvedValue(undefined),
      stop: vi.fn().mockResolvedValue(new Blob(["audio"], { type: "audio/webm" }))
    });

    mockedSendAudioTurn
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(inProgressResponse);

    render(<AddEntryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Audio" }));
    fireEvent.click(await screen.findByRole("button", { name: "Record" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Stop" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Stop" }));

    const retryButton = await screen.findByRole("button", { name: "Retry" });
    expect(retryButton).toBeInTheDocument();

    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(mockedSendAudioTurn).toHaveBeenCalledTimes(2);
      expect(screen.getByRole("button", { name: "Record" })).toBeInTheDocument();
    });
  });

  it("shows switch-to-text option in audio mode and preserves transcript", async () => {
    mockedSendTextTurn.mockResolvedValueOnce(inProgressResponse);

    render(<AddEntryPage />);
    fireEvent.click(screen.getByRole("button", { name: "Text" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Add details")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Add details"), {
      target: {
        value: "Role title and salary"
      }
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(
        screen.getByText("Please share the remaining required information: company_name.")
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Switch to Audio Input" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Switch to Text Input" })).toBeInTheDocument();
    });

    expect(
      screen.getByText("Please share the remaining required information: company_name.")
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Skip" })).not.toBeInTheDocument();
  });

  it("uses shared fade utility classes for initial reveal", () => {
    const { container } = render(<AddEntryPage />);

    const heading = screen.getByRole("heading", { name: "Create a Job Entry" });
    expect(heading).toHaveClass("motion-fade-enter");

    const animatedSections = container.querySelectorAll(".motion-fade-enter, .motion-fade-exit");
    expect(animatedSections.length).toBeGreaterThan(0);
  });

  it("calls onOfferSaved after successful Finish save", async () => {
    const onOfferSaved = vi.fn();
    mockedSendTextTurn.mockResolvedValueOnce(readyToFinishResponse);
    mockedFinalizeIntakeSession.mockResolvedValueOnce(savedResponse);

    render(<AddEntryPage onOfferSaved={onOfferSaved} />);
    fireEvent.click(screen.getByRole("button", { name: "Text" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Add details")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Add details"), {
      target: {
        value: "Ready to finish"
      }
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByRole("button", { name: "Finish" });

    fireEvent.click(screen.getByRole("button", { name: "Finish" }));

    await waitFor(() => {
      expect(onOfferSaved).toHaveBeenCalledTimes(1);
    });
    expect(mockedFinalizeIntakeSession).toHaveBeenCalledWith("session-1");
  });

  it("blocks Finish and shows required field message when required fields are missing", async () => {
    mockedSendTextTurn.mockResolvedValueOnce(inProgressResponse);

    render(<AddEntryPage />);
    fireEvent.click(screen.getByRole("button", { name: "Text" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Add details")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Add details"), {
      target: {
        value: "Partial info"
      }
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByRole("button", { name: "Finish" });

    fireEvent.click(screen.getByRole("button", { name: "Finish" }));

    await waitFor(() => {
      expect(screen.getByText("Please fill required fields: company_name.")).toBeInTheDocument();
    });
    expect(mockedFinalizeIntakeSession).not.toHaveBeenCalled();
  });

  it("calls onOfferSaved when submit response is already saved", async () => {
    const onOfferSaved = vi.fn();
    mockedSendTextTurn.mockResolvedValueOnce(savedResponse);

    render(<AddEntryPage onOfferSaved={onOfferSaved} />);
    fireEvent.click(screen.getByRole("button", { name: "Text" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Add details")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Add details"), {
      target: {
        value: "Submit and save now"
      }
    });
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(onOfferSaved).toHaveBeenCalledTimes(1);
    });
  });
});
