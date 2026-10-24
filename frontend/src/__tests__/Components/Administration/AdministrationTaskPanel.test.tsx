// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA Ledger
import { AdministrationTaskPanel } from "@/Components/Administration/AdministrationTaskPanel";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("AdministrationTaskPanel", () => {
  it("should toggle panel open and trigger action callbacks", async () => {
    // Test Data
    const user = userEvent.setup();
    const onToggleTaskPanel = vi.fn();
    const onToggleForceRefresh = vi.fn();
    const onUpdateTarget = vi.fn();

    // Test Action
    const { rerender } = render(
      <AdministrationTaskPanel
        showTaskPanel={false}
        onToggleTaskPanel={onToggleTaskPanel}
        forceRefreshGlobal={false}
        onToggleForceRefresh={onToggleForceRefresh}
        isPending={false}
        onUpdateTarget={onUpdateTarget}
      />,
    );

    // Expected Result - when collapsed
    expect(screen.getByText("Global Task Administration")).toBeInTheDocument();
    expect(screen.queryByTestId("update-all-characters-btn")).not.toBeInTheDocument();

    // Test Action - click toggle
    await user.click(screen.getByTestId("toggle-task-panel"));
    expect(onToggleTaskPanel).toHaveBeenCalledTimes(1);

    // Test Action - rerender open
    rerender(
      <AdministrationTaskPanel
        showTaskPanel={true}
        onToggleTaskPanel={onToggleTaskPanel}
        forceRefreshGlobal={false}
        onToggleForceRefresh={onToggleForceRefresh}
        isPending={false}
        onUpdateTarget={onUpdateTarget}
      />,
    );

    // Expected Result - when expanded
    const charBtn = screen.getByTestId("update-all-characters-btn");
    const corpBtn = screen.getByTestId("update-all-corporations-btn");
    expect(charBtn).toBeInTheDocument();
    expect(corpBtn).toBeInTheDocument();

    await user.click(charBtn);
    expect(onUpdateTarget).toHaveBeenCalledWith("characters");

    await user.click(corpBtn);
    expect(onUpdateTarget).toHaveBeenCalledWith("corporations");

    const switchEl = screen.getByTestId("force-refresh-switch");
    await user.click(switchEl);
    expect(onToggleForceRefresh).toHaveBeenCalledWith(true);
  });

  it("should disable buttons when isPending is true", () => {
    // Test Data
    const onToggleTaskPanel = vi.fn();
    const onToggleForceRefresh = vi.fn();
    const onUpdateTarget = vi.fn();

    // Test Action
    render(
      <AdministrationTaskPanel
        showTaskPanel={true}
        onToggleTaskPanel={onToggleTaskPanel}
        forceRefreshGlobal={true}
        onToggleForceRefresh={onToggleForceRefresh}
        isPending={true}
        onUpdateTarget={onUpdateTarget}
      />,
    );

    // Expected Result
    expect(screen.getByTestId("update-all-characters-btn")).toBeDisabled();
    expect(screen.getByTestId("update-all-corporations-btn")).toBeDisabled();
  });
});
