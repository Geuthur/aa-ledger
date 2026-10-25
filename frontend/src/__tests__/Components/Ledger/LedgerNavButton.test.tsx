// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA Ledger
import { LedgerNavButton } from "@/Components/Ledger/LedgerNavButton";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("LedgerNavButton", () => {
  it("should link to the overview when no back handler is given", () => {
    // Test Data
    // (no onBack)

    // Test Action
    render(
      <MemoryRouter>
        <LedgerNavButton />
      </MemoryRouter>,
    );

    // Expected Result
    expect(screen.getByRole("link", { name: "Overview" })).toHaveAttribute("href", "/ledger/");
  });

  it("should call the back handler when opened from the Administration", async () => {
    // Test Data
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(
      <MemoryRouter>
        <LedgerNavButton onBack={onBack} />
      </MemoryRouter>,
    );

    // Test Action
    await user.click(screen.getByRole("button", { name: "Back to Administration Overview" }));

    // Expected Result
    expect(onBack).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("link", { name: "Overview" })).not.toBeInTheDocument();
  });
});
