// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import * as ApiCalls from "@/Api/ApiCalls";
import { SettingsPage } from "@/Pages/SettingsPage";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return {
    ...actual,
    loadUserSettings: vi.fn(),
    updateUserSettings: vi.fn(),
  };
});

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/ledger/settings/"]}>
        <SettingsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should load the saved global notification preference", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadUserSettings).mockResolvedValueOnce({
      disable_notifications: true,
    });

    // Test Action
    renderPage();

    // Expected Result
    expect(
      await screen.findByRole("switch", { name: "Disable all notifications" }),
    ).toBeChecked();
  });

  it("should save the global preference when the switch is enabled", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.updateUserSettings).mockResolvedValue({
      disable_notifications: true,
    });

    // Test Action
    renderPage();
    const toggle = await screen.findByRole("switch", {
      name: "Disable all notifications",
    });
    await user.click(toggle);

    // Expected Result
    expect(ApiCalls.updateUserSettings).toHaveBeenCalledWith(
      { disable_notifications: true },
      expect.any(Object),
    );
    await waitFor(() => expect(toggle).toBeChecked());
  });
});
