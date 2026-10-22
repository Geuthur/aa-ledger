// React
import { MemoryRouter, Route, Routes } from "react-router";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as ApiCalls from "@/Api/ApiCalls";
import type { LedgerOverviewResponse } from "@/Api/schema";
import OverviewPage from "@/Pages/OverviewPage";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return { ...actual, fetchOverview: vi.fn() };
});

const mockOverview: LedgerOverviewResponse = {
  owners: [
    {
      id: 101,
      name: "Pilot Alpha",
      type: "character",
      type_display: "Character",
      portrait_url: "https://images.evetech.net/characters/101/portrait",
      subtitle: "Federal Navy Academy",
      active: true,
      has_planetary: true,
      can_manage: true,
      has_errors: false,
    },
    {
      id: 201,
      name: "Omega Corp",
      type: "corporation",
      type_display: "Corporation",
      portrait_url: "https://images.evetech.net/corporations/201/logo",
      subtitle: "Omega Conglomerate",
      active: true,
      has_planetary: false,
      can_manage: true,
      has_errors: false,
    },
    {
      id: 301,
      name: "Alpha Alliance",
      type: "alliance",
      type_display: "Alliance",
      portrait_url: "https://images.evetech.net/alliances/301/logo",
      subtitle: null,
      active: false,
      has_planetary: false,
      can_manage: false,
      has_errors: false,
    },
  ],
};

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/ledger/"]}>
        <Routes>
          <Route path="/ledger/" element={<OverviewPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("OverviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders overview cards with characters, corporations, and alliances", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchOverview).mockResolvedValue(mockOverview);

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Pilot Alpha")).toBeInTheDocument();
    expect(screen.getByText("Omega Corp")).toBeInTheDocument();
    expect(screen.getByText("Alpha Alliance")).toBeInTheDocument();
    expect(screen.getByText("3 Owners")).toBeInTheDocument();
    expect(screen.getByText("View Planetary")).toBeInTheDocument();
  });

  it("filters owners by search term", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchOverview).mockResolvedValue(mockOverview);
    const user = userEvent.setup();

    // Test Action
    renderPage();
    await screen.findByText("Pilot Alpha");
    const searchInput = screen.getByPlaceholderText(/search characters/i);
    await user.type(searchInput, "Omega");

    // Expected Result
    expect(screen.getByText("Omega Corp")).toBeInTheDocument();
    expect(screen.queryByText("Pilot Alpha")).not.toBeInTheDocument();
    expect(screen.queryByText("Alpha Alliance")).not.toBeInTheDocument();
  });

  it("filters owners by type filter buttons", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchOverview).mockResolvedValue(mockOverview);
    const user = userEvent.setup();

    // Test Action
    renderPage();
    await screen.findByText("Pilot Alpha");
    const corpFilterBtn = screen.getByRole("button", { name: /corporations/i });
    await user.click(corpFilterBtn);

    // Expected Result
    expect(screen.getByText("Omega Corp")).toBeInTheDocument();
    expect(screen.queryByText("Pilot Alpha")).not.toBeInTheDocument();
    expect(screen.queryByText("Alpha Alliance")).not.toBeInTheDocument();
  });

  it("displays View Planetary button only for characters", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchOverview).mockResolvedValue(mockOverview);

    // Test Action
    renderPage();
    await screen.findByText("Pilot Alpha");

    // Expected Result
    const planetaryLinks = screen.getAllByRole("link", { name: /view planetary/i });
    expect(planetaryLinks).toHaveLength(1);
    expect(planetaryLinks[0]).toHaveAttribute("href", "/ledger/planetary/101/");
  });

  it("does not render manage button (moved to settings)", async () => {
    // Test Data
    const overviewWithErrors: LedgerOverviewResponse = {
      owners: [
        {
          ...mockOverview.owners[0],
          has_errors: true,
          can_manage: true,
        },
      ],
    };
    vi.mocked(ApiCalls.fetchOverview).mockResolvedValue(overviewWithErrors);

    // Test Action
    renderPage();
    await screen.findByText("Pilot Alpha");

    // Expected Result
    expect(screen.queryByRole("link", { name: /manage/i })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /ledger/i })).toBeInTheDocument();
  });
});

