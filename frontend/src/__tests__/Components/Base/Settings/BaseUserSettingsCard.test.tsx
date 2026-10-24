// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA Ledger
import { BaseUserSettingsCard } from "@/Components/Base/BaseSettings/UserSettingsCard";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("BaseUserSettingsCard", () => {
  it("should render title, description, and toggle switch when clicked", async () => {
    // Test Data
    const user = userEvent.setup();
    const onToggle = vi.fn();

    // Test Action
    render(
      <BaseUserSettingsCard
        disableNotifications={false}
        isPending={false}
        isError={false}
        onToggleNotifications={onToggle}
        title="Notification Settings"
        description="Manage your notification preferences"
      />,
    );

    // Expected Result
    expect(screen.getByText("Notification Settings")).toBeInTheDocument();
    expect(screen.getByText("Manage your notification preferences")).toBeInTheDocument();

    const switchEl = screen.getByRole("switch");
    expect(switchEl).not.toBeChecked();

    await user.click(switchEl);
    expect(onToggle).toHaveBeenCalledWith(true);
  });

  it("should render error message when isError is true", () => {
    // Test Data
    const onToggle = vi.fn();

    // Test Action
    render(
      <BaseUserSettingsCard
        disableNotifications={true}
        isPending={false}
        isError={true}
        onToggleNotifications={onToggle}
      />,
    );

    // Expected Result
    expect(
      screen.getByText("Could not save this setting. Your previous preference was restored."),
    ).toBeInTheDocument();
    const switchEl = screen.getByRole("switch");
    expect(switchEl).toBeChecked();
  });

  it("should disable switch and display saving status when isPending is true", () => {
    // Test Data
    const onToggle = vi.fn();

    // Test Action
    render(
      <BaseUserSettingsCard
        disableNotifications={false}
        isPending={true}
        isError={false}
        onToggleNotifications={onToggle}
      />,
    );

    // Expected Result
    expect(screen.getByText("Saving…")).toBeInTheDocument();
    expect(screen.getByRole("switch")).toBeDisabled();
  });
});
