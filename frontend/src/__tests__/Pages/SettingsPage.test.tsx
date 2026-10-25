// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
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
    loadSettingsOwners: vi.fn(),
    loadSettingsUnregistered: vi.fn(),
    triggerUpdateAllSettingsOwners: vi.fn(),
    triggerSettingsOwnerUpdate: vi.fn(),
    deleteSettingsOwner: vi.fn(),
  };
});

const defaultOwnersResponse = {
  registered: [
    {
      id: 1,
      name: "Alice",
      owner_type: "character" as const,
      avatar_url: "https://example.com/alice.png",
      subtitle: "[CORP]",
      status: "ok",
      has_error: false,
      error_message: null,
      last_sync: "2026-10-20T12:00:00Z",
      sections: [],
    },
    {
      id: 10,
      name: "Awesome Corp",
      owner_type: "corporation" as const,
      avatar_url: "https://example.com/corp.png",
      subtitle: "[AWC]",
      status: "error",
      has_error: true,
      error_message: "ESI 500 error",
      last_sync: "2026-10-20T11:00:00Z",
      sections: [],
    },
  ],
  missing: [
    {
      id: 2,
      name: "Bob (Alt)",
      owner_type: "character" as const,
      avatar_url: "https://example.com/bob.png",
      subtitle: "Some Corp",
    },
  ],
  can_update: true,
  cooldown_seconds: 0,
};

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
    vi.mocked(ApiCalls.loadUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue(defaultOwnersResponse);
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

  it("should render registered owners and missing alts", async () => {
    // Test Data
    // uses defaultOwnersResponse

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Awesome Corp")).toBeInTheDocument();
    expect(screen.getByText("Bob (Alt)")).toBeInTheDocument();
    expect(screen.getByText("Missing in Ledger")).toBeInTheDocument();
  });

  it("should trigger update all owners when update all button is clicked", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.triggerUpdateAllSettingsOwners).mockResolvedValue({
      message: "Update task queued for all owners.",
    });

    // Test Action
    renderPage();
    const updateAllBtn = await screen.findByRole("button", { name: /Update All/i });
    await user.click(updateAllBtn);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.triggerUpdateAllSettingsOwners).toHaveBeenCalled();
    });
  });

  it("should open delete modal and confirm deletion of an owner", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.deleteSettingsOwner).mockResolvedValue({
      message: "Alice successfully deleted",
    });

    // Test Action
    renderPage();
    expect(await screen.findByText("Alice")).toBeInTheDocument();
    const deleteButtons = screen.getAllByRole("button", { name: /Delete/i });
    await user.click(deleteButtons[0]);

    // Expected Result
    expect(await screen.findByText(/Are you sure you want to delete owner 'Alice'\?/i)).toBeInTheDocument();
    const confirmBtn = screen.getByRole("button", { name: /Confirm Delete/i });
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(ApiCalls.deleteSettingsOwner).toHaveBeenCalledWith("character", 1);
    });
  });

  it("should filter owners by search text", async () => {
    // Test Data
    const user = userEvent.setup();

    // Test Action
    renderPage();
    await screen.findByText("Alice");
    await user.type(screen.getByRole("searchbox", { name: "Search owners" }), "awesome");

    // Expected Result
    expect(screen.getByText("Awesome Corp")).toBeInTheDocument();
    expect(screen.queryByText("Alice")).not.toBeInTheDocument();
    expect(screen.queryByText("Bob (Alt)")).not.toBeInTheDocument();
  });

  it("should filter owners by type and hide missing owners for non-character types", async () => {
    // Test Data
    const user = userEvent.setup();

    // Test Action
    renderPage();
    await screen.findByText("Alice");
    await user.click(screen.getByRole("button", { name: /Corporations/i }));

    // Expected Result
    expect(screen.getByText("Awesome Corp")).toBeInTheDocument();
    expect(screen.queryByText("Alice")).not.toBeInTheDocument();
    expect(screen.queryByText("Bob (Alt)")).not.toBeInTheDocument();
  });

  it("should show empty state and reset filters when nothing matches", async () => {
    // Test Data
    const user = userEvent.setup();

    // Test Action
    renderPage();
    await screen.findByText("Alice");
    await user.type(screen.getByRole("searchbox", { name: "Search owners" }), "zzzz");
    expect(screen.getByText("No matching owners found.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Reset filters" }));

    // Expected Result
    expect(await screen.findByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob (Alt)")).toBeInTheDocument();
  });

  it("should show the unregistered button only for corporation and alliance cards", async () => {
    // Test Data
    // uses defaultOwnersResponse (one character, one corporation)

    // Test Action
    renderPage();
    await screen.findByText("Alice");

    // Expected Result
    expect(screen.getAllByRole("button", { name: /Unregistered/i })).toHaveLength(1);
  });

  it("should open the modal and list unregistered members of a corporation", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadSettingsUnregistered).mockResolvedValue({
      owner_type: "corporation",
      owner_id: 10,
      items: [
        { id: 77, name: "Carol", avatar_url: "https://example.com/c.png", subtitle: "Awesome Corp", owner_type: "character" },
      ],
    });

    // Test Action
    renderPage();
    await screen.findByText("Alice");
    await user.click(screen.getByRole("button", { name: /Unregistered/i }));

    // Expected Result
    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByText("Carol")).toBeInTheDocument();
    expect(ApiCalls.loadSettingsUnregistered).toHaveBeenCalledWith("corporation", 10);
  });

  it("should show an empty message when everything is registered", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadSettingsUnregistered).mockResolvedValue({
      owner_type: "corporation",
      owner_id: 10,
      items: [],
    });

    // Test Action
    renderPage();
    await screen.findByText("Alice");
    await user.click(screen.getByRole("button", { name: /Unregistered/i }));

    // Expected Result
    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByText("Everything is registered.")).toBeInTheDocument();
  });

  it("should show an error message when loading unregistered entries fails", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadSettingsUnregistered).mockRejectedValue(new Error("boom"));

    // Test Action
    renderPage();
    await screen.findByText("Alice");
    await user.click(screen.getByRole("button", { name: /Unregistered/i }));

    // Expected Result
    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByText("Failed to load unregistered entries.")).toBeInTheDocument();
  });

  it("should not offer update or delete for alliance cards", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue({
      ...defaultOwnersResponse,
      registered: [
        {
          id: 5,
          name: "Cool Alliance",
          owner_type: "alliance" as const,
          avatar_url: "https://example.com/a.png",
          subtitle: "[COOL]",
          status: "ok",
          has_error: false,
          error_message: null,
          last_sync: null,
          sections: [],
        },
      ],
    });

    // Test Action
    renderPage();
    await screen.findByText("Cool Alliance");

    // Expected Result
    expect(screen.getByRole("button", { name: /Unregistered/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Delete/i })).not.toBeInTheDocument();
  });
});
