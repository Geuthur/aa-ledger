// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA Ledger
import * as ApiCalls from "@/Api/ApiCalls";
import type { AdministrationOwnerSchema } from "@/Api/schema";
import AdministrationPage from "@/Pages/AdministrationPage";

vi.mock("react-apexcharts", () => ({ default: () => <div data-testid="chart" /> }));

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return {
    ...actual,
    loadAdministrationOwners: vi.fn(),
    loadUserData: vi.fn(),
    triggerAdministrationOwnerUpdate: vi.fn(),
    deleteAdministrationOwner: vi.fn(),
    loadAdministrationOwnerInspect: vi.fn(),
    loadSettingsUnregistered: vi.fn(),
    fetchCharacterLedger: vi.fn(),
    fetchCorporationLedger: vi.fn(),
    fetchAllianceLedger: vi.fn(),
    queueUpdate: vi.fn(),
  };
});

const mockOwners: AdministrationOwnerSchema[] = [
  {
    id: 1,
    owner_id: 1001,
    owner_type: "character",
    name: "John Doe",
    ticker: "CORP",
    user_id: 1,
    user_name: "johndoe",
    status: "ok",
    is_active: true,
    last_sync: "2026-10-18T12:00:00Z",
    alts: [
      {
        character_id: 1002,
        character_name: "Jane Alt",
        icon: null,
        is_registered: true,
      },
    ],
  },
  {
    id: 2,
    owner_id: 2001,
    owner_type: "corporation",
    name: "Mega Corp",
    ticker: "MEGA",
    status: "ok",
    is_active: true,
    last_sync: "2026-10-18T12:00:00Z",
    alts: [],
    unregistered_count: 3,
  },
  {
    id: 3,
    owner_id: 3001,
    owner_type: "alliance",
    name: "Northern Coalition",
    ticker: "NC",
    status: "ok",
    is_active: true,
    last_sync: "2026-10-18T12:00:00Z",
    alts: [],
    unregistered_count: 2,
  },
];

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <NuqsTestingAdapter hasMemory>
          <AdministrationPage />
        </NuqsTestingAdapter>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe("AdministrationPage in aa-ledger", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(ApiCalls.loadUserData).mockResolvedValue({
      user: {
        user_id: 1,
        character_id: 1001,
        character_name: "Test User",
        corporation_id: 2001,
        corporation_name: "Test Corp",
        is_superuser: true,
        can_manage: true,
        has_advanced_access: true,
      },
    });
  });

  it("renders administration page with metrics and table", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Administration")).toBeInTheDocument();
    expect(await screen.findByText("John Doe")).toBeInTheDocument();
    expect(await screen.findByText("Mega Corp")).toBeInTheDocument();
    expect(screen.getByText("Total Owners")).toBeInTheDocument();
  });

  it("triggers update for a specific owner", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.triggerAdministrationOwnerUpdate).mockResolvedValue({
      message: "Queued update for John Doe",
    });
    renderPage();

    // Test Action
    await screen.findByText("John Doe");
    const updateBtn = screen.getByTestId("update-btn-character-1001");
    await user.click(updateBtn);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.triggerAdministrationOwnerUpdate).toHaveBeenCalledWith(
        "character",
        1001,
        { force_refresh: false }
      );
    });
    expect(await screen.findByTestId("task-feedback-message")).toHaveTextContent("Queued update for John Doe");
  });

  it("deletes an owner via confirmation modal", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.deleteAdministrationOwner).mockResolvedValue({
      message: "John Doe successfully deleted",
    });
    renderPage();

    // Test Action
    await screen.findByText("John Doe");
    const deleteBtn = screen.getByTestId("delete-btn-character-1001");
    await user.click(deleteBtn);

    expect(await screen.findByText("Confirm Deletion")).toBeInTheDocument();
    const confirmBtn = screen.getByTestId("confirm-delete-btn");
    await user.click(confirmBtn);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.deleteAdministrationOwner).toHaveBeenCalledWith("character", 1001);
    });
    expect(await screen.findByTestId("task-feedback-message")).toHaveTextContent("John Doe successfully deleted");
  });

  it("switches to inspection view on inspect click and returns back via button", async () => {
    // Test Data
    const user = userEvent.setup();
    const mockCharacterLedger = {
      owner: { character_id: 1001, character_name: "John Doe", icon: "johndoe.png" },
      years: [2026],
      billboard: {},
      characters: [
        {
          character: { character_id: 1001, character_name: "John Doe", icon: "johndoe.png" },
          ledger: { bounty: 1000, ess: 0, costs: -200, miscellaneous: 0, total: 800, mining: 0 },
          update_status: { status: "ok" },
        },
      ],
    };
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.fetchCharacterLedger).mockResolvedValue(mockCharacterLedger as never);
    renderPage();

    // Test Action
    await screen.findByText("John Doe");
    const inspectBtn = screen.getByTestId("inspect-btn-character-1001");
    await user.click(inspectBtn);

    // Expected Result
    expect(
      await screen.findByTestId("back-to-administration-btn")
    ).toBeInTheDocument();
    expect(ApiCalls.fetchCharacterLedger).toHaveBeenCalledWith(1001, expect.any(Object));

    // Test Action - Back button
    const backBtn = screen.getByTestId("back-to-administration-btn");
    await user.click(backBtn);

    // Expected Result
    expect(await screen.findByText("Total Owners")).toBeInTheDocument();
  });

  it("queues global update all characters", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.queueUpdate).mockResolvedValue({
      message: "Queued Update All Characters",
    });
    renderPage();

    // Test Action
    await screen.findByText("Total Owners");
    expect(screen.getByText("Sync Issues")).toBeInTheDocument();

    const togglePanelBtn = await screen.findByTestId("toggle-task-panel");
    await user.click(togglePanelBtn);

    const updateAllBtn = await screen.findByTestId("update-all-characters-btn");
    await user.click(updateAllBtn);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.queueUpdate).toHaveBeenCalledWith({
        target: "characters",
        eve_id: null,
        force_refresh: false,
      });
    });
    expect(await screen.findByTestId("task-feedback-message")).toHaveTextContent("Queued Update All Characters");
  });

  it("filters table when searching by alt character name and opens alts modal", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);
    renderPage();

    // Test Action - Search by alt name
    await screen.findByText("John Doe");
    expect(screen.getByText("Mega Corp")).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText("Search owners…");
    await user.type(searchInput, "Jane Alt");

    // Expected Result - Only John Doe should remain
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.queryByText("Mega Corp")).not.toBeInTheDocument();

    // Test Action - Click Alts button
    const altsBtn = screen.getByTestId("alts-btn-character-1001");
    expect(altsBtn).toHaveTextContent("1 Alts");
    await user.click(altsBtn);

    // Expected Result - Modal opens with Jane Alt
    expect(await screen.findByText("Jane Alt")).toBeInTheDocument();

    // Verify Update All Alts button exists in modal
    expect(screen.getByTestId("update-all-alts-btn-1001")).toBeInTheDocument();
  });

  it("triggers update all alts from the modal", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.triggerAdministrationOwnerUpdate).mockResolvedValue({
      message: "Queued update for John Doe",
    });
    renderPage();

    // Test Action - Open Alts Modal
    await screen.findByText("John Doe");
    const altsBtn = screen.getByTestId("alts-btn-character-1001");
    await user.click(altsBtn);
    expect(await screen.findByText("Jane Alt")).toBeInTheDocument();

    // Test Action - Click Update All Alts
    const updateAllAltsBtn = screen.getByTestId("update-all-alts-btn-1001");
    await user.click(updateAllAltsBtn);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.triggerAdministrationOwnerUpdate).toHaveBeenCalledWith(
        "character",
        1001,
        { force_refresh: false }
      );
    });
  });

  it("does not render global task administration panel for non-superuser", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadUserData).mockResolvedValue({
      user: {
        user_id: 2,
        character_id: 1002,
        character_name: "Non Admin",
        corporation_id: 2002,
        corporation_name: "Other Corp",
        is_superuser: false,
        can_manage: true,
        has_advanced_access: false,
      },
    });
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);

    // Test Action
    renderPage();

    // Expected Result
    await screen.findByText("Administration");
    expect(screen.queryByTestId("toggle-task-panel")).not.toBeInTheDocument();
  });

  it("offers force refresh in the update menu for superusers", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);
    renderPage();
    await screen.findByText("John Doe");

    // Test Action
    await user.click(screen.getAllByRole("button", { name: "More update options" })[0]);

    // Expected Result
    expect(await screen.findByText("Normal Update")).toBeInTheDocument();
    expect(screen.getByText("Force Refresh (Bypass Cache)")).toBeInTheDocument();
  });

  it("hides force refresh in the update menu for non-superuser", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadUserData).mockResolvedValue({
      user: {
        user_id: 2,
        character_id: 1002,
        character_name: "Non Admin",
        corporation_id: 2002,
        corporation_name: "Other Corp",
        is_superuser: false,
        can_manage: true,
        has_advanced_access: false,
      },
    });
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);
    renderPage();
    await screen.findByText("John Doe");

    // Test Action
    await user.click(screen.getAllByRole("button", { name: "More update options" })[0]);

    // Expected Result
    expect(await screen.findByText("Normal Update")).toBeInTheDocument();
    expect(screen.queryByText("Force Refresh (Bypass Cache)")).not.toBeInTheDocument();
  });

  it("renders alliance owner with inspect button and unregistered button, but no update or delete", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);

    // Test Action
    renderPage();

    // Expected Result
    await screen.findByText("Northern Coalition");
    expect(screen.getByTestId("inspect-btn-alliance-3001")).toBeInTheDocument();
    expect(screen.queryByTestId("update-btn-alliance-3001")).not.toBeInTheDocument();
    expect(screen.queryByTestId("delete-btn-alliance-3001")).not.toBeInTheDocument();
    expect(screen.getByTestId("unregistered-btn-alliance-3001")).toBeInTheDocument();

    // Clicking inspect navigates to inspection view
    await user.click(screen.getByTestId("inspect-btn-alliance-3001"));
    expect(await screen.findByTestId("back-to-administration-btn")).toBeInTheDocument();
  });

  it("opens unregistered modal when clicking unregistered button on corporation or alliance", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadAdministrationOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.loadSettingsUnregistered).mockResolvedValue({
      owner_type: "corporation",
      owner_id: 2001,
      items: [
        {
          id: 5001,
          name: "Unregistered Pilot",
          owner_type: "character",
          avatar_url: null,
          subtitle: "Mega Corp",
        },
      ],
    });

    // Test Action
    renderPage();
    const unregBtn = await screen.findByTestId("unregistered-btn-corporation-2001");
    await user.click(unregBtn);

    // Expected Result
    expect(await screen.findByText("Unregistered Pilot")).toBeInTheDocument();
  });
});

