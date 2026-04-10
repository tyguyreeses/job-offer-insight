import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { AddEntryPage } from "./AddEntryPage";
import { createBrowserAudioRecorder } from "../services/audioRecorder";
import { sendAudioTurn, sendTextTurn } from "../services/offersApi";

vi.mock("../services/offersApi", () => ({
  sendTextTurn: vi.fn(),
  sendAudioTurn: vi.fn()
}));

vi.mock("../services/audioRecorder", () => ({
  createBrowserAudioRecorder: vi.fn()
}));

const mockedSendTextTurn = vi.mocked(sendTextTurn);
const mockedSendAudioTurn = vi.mocked(sendAudioTurn);
const mockedCreateBrowserAudioRecorder = vi.mocked(createBrowserAudioRecorder);

describe("AddEntryPage", () => {
  beforeEach(() => {
    mockedSendTextTurn.mockReset();
    mockedSendAudioTurn.mockReset();
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

  it("shows assistant message above input after submit", async () => {
    mockedSendTextTurn.mockResolvedValueOnce({
      session_id: "session-1",
      status: "in_progress",
      assistant_message: "Please share the remaining required information: company_name.",
      step: "collect_required",
      can_finish: false,
      missing_required_fields: ["company_name"],
      current_prompt_key: "required_fields_bundle",
      errors: [],
      warnings: [],
      offer: null
    });

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
  });

  it("transitions from mode buttons to audio recorder controls", async () => {
    render(<AddEntryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Audio" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Start Recording" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Stop Recording" })).toBeInTheDocument();
    });
  });

  it("shows recording indicator while audio capture is running", async () => {
    mockedCreateBrowserAudioRecorder.mockResolvedValue({
      start: vi.fn().mockResolvedValue(undefined),
      stop: vi.fn().mockResolvedValue(new Blob(["audio"], { type: "audio/webm" }))
    });

    render(<AddEntryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Audio" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Start Recording" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Start Recording" }));

    await waitFor(() => {
      expect(screen.getByText("Recording...")).toBeInTheDocument();
    });
  });

  it("submits recorded audio and shows assistant message", async () => {
    mockedCreateBrowserAudioRecorder.mockResolvedValue({
      start: vi.fn().mockResolvedValue(undefined),
      stop: vi.fn().mockResolvedValue(new Blob(["audio"], { type: "audio/webm" }))
    });
    mockedSendAudioTurn.mockResolvedValueOnce({
      session_id: "audio-session-1",
      status: "in_progress",
      assistant_message: "Please share the remaining required information: company_name.",
      step: "collect_required",
      can_finish: false,
      missing_required_fields: ["company_name"],
      current_prompt_key: "required_fields_bundle",
      errors: [],
      warnings: [],
      offer: null
    });

    render(<AddEntryPage />);
    fireEvent.click(screen.getByRole("button", { name: "Audio" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Start Recording" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Start Recording" }));
    await waitFor(() => {
      expect(screen.getByText("Recording...")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Stop Recording" }));

    await waitFor(() => {
      expect(screen.getByText("Recording captured and ready to submit.")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(mockedSendAudioTurn).toHaveBeenCalledTimes(1);
      expect(
        screen.getByText("Please share the remaining required information: company_name.")
      ).toBeInTheDocument();
    });
  });

  it("shows switch-to-text option after repeated recording failures", async () => {
    mockedCreateBrowserAudioRecorder.mockRejectedValue(new Error("Microphone unavailable"));

    render(<AddEntryPage />);
    fireEvent.click(screen.getByRole("button", { name: "Audio" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Start Recording" })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: "Start Recording" }));
    fireEvent.click(screen.getByRole("button", { name: "Start Recording" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Switch to Text Input" })).toBeInTheDocument();
    });
  });

  it("uses shared fade utility classes for initial reveal", () => {
    const { container } = render(<AddEntryPage />);

    const heading = screen.getByRole("heading", { name: "Create a Job Entry" });
    expect(heading).toHaveClass("motion-fade-enter");

    const animatedSections = container.querySelectorAll(".motion-fade-enter, .motion-fade-exit");
    expect(animatedSections.length).toBeGreaterThan(0);
  });
});
