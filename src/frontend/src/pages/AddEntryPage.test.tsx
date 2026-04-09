import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { AddEntryPage } from "./AddEntryPage";
import { sendTextTurn } from "../services/offersApi";

vi.mock("../services/offersApi", () => ({
  sendTextTurn: vi.fn()
}));

const mockedSendTextTurn = vi.mocked(sendTextTurn);

describe("AddEntryPage", () => {
  beforeEach(() => {
    mockedSendTextTurn.mockReset();
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

  it("keeps audio as a no-op in this stage", () => {
    render(<AddEntryPage />);

    fireEvent.click(screen.getByRole("button", { name: "Audio" }));

    expect(screen.getByRole("button", { name: "Text" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Audio" })).toBeInTheDocument();
  });

  it("uses shared fade utility classes for initial reveal", () => {
    const { container } = render(<AddEntryPage />);

    const heading = screen.getByRole("heading", { name: "Create a Job Entry" });
    expect(heading).toHaveClass("motion-fade-enter");

    const animatedSections = container.querySelectorAll(".motion-fade-enter, .motion-fade-exit");
    expect(animatedSections.length).toBeGreaterThan(0);
  });
});
