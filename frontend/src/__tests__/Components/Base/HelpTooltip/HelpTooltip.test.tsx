// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

// AA Ledger
import { HelpTooltip } from "@/Components/Base/HelpTooltip";

describe("HelpTooltip", () => {
  it("should show the text when the icon is hovered", async () => {
    // Test Data
    const user = userEvent.setup();
    const { container } = render(<HelpTooltip text="Explains the value" />);

    // Test Action
    await user.hover(container.firstElementChild as Element);

    // Expected Result
    expect(await screen.findByText("Explains the value")).toBeInTheDocument();
  });

  it("should apply the given class instead of the muted default", () => {
    // Test Data
    // (custom class)

    // Test Action
    const { container } = render(<HelpTooltip text="Info" className="text-info" />);

    // Expected Result
    expect(container.firstElementChild).toHaveClass("text-info", "cursor-help");
    expect(container.firstElementChild).not.toHaveClass("text-muted");
  });
});
