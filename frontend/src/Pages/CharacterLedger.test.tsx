// React
import { MemoryRouter, Route, Routes } from "react-router";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as ApiCalls from "@/Api/ApiCalls";
import CharacterLedger from "@/Pages/CharacterLedger";

vi.mock("react-apexcharts", () => ({ default: () => <div data-testid="chart" /> }));

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return { ...actual, fetchCharacterLedger: vi.fn(), fetchCharacterDetails: vi.fn() };
});

const ledger = {
  owner: { character_id: 1, character_name: "Alice", icon: "a.png" },
  years: [2026, 2025],
  billboard: {},
  characters: [
    {
      character: { character_id: 1, character_name: "Alice", icon: "a.png" },
      ledger: { bounty: 1000, ess: 0, costs: -200, miscellaneous: 0, total: 800, mining: 0 },
      update_status: { status: "ok" },
    },
  ],
};

const renderPage = (searchParams = "?year=2026&month=10") => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <NuqsTestingAdapter searchParams={searchParams}>
        <MemoryRouter initialEntries={["/ledger/character/1/"]}>
          <Routes>
            <Route path="/ledger/character/:characterId/" element={<CharacterLedger />} />
          </Routes>
        </MemoryRouter>
      </NuqsTestingAdapter>
    </QueryClientProvider>,
  );
};

describe("CharacterLedger", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("requests the ledger for the date in the URL", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchCharacterLedger).mockResolvedValue(ledger as never);

    // Test Action
    renderPage("?year=2025&month=3&day=4");

    // Expected Result
    expect(await screen.findByText("Character Ledger - Alice")).toBeInTheDocument();
    expect(ApiCalls.fetchCharacterLedger).toHaveBeenCalledWith(1, {
      year: 2025,
      month: 3,
      day: 4,
    });
  });

  it("shows the totals and the character row", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchCharacterLedger).mockResolvedValue(ledger as never);

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findAllByText(/800 ISK/)).not.toHaveLength(0);
    expect(screen.getByText("Alice", { selector: "td span" })).toBeInTheDocument();
  });

  it("shows the API error", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchCharacterLedger).mockRejectedValue(
      new Error("You do not have permission to view this character."),
    );

    // Test Action
    renderPage();

    // Expected Result
    expect(
      await screen.findByText("You do not have permission to view this character."),
    ).toBeInTheDocument();
  });

  it("opens the details of a character from the table", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.fetchCharacterLedger).mockResolvedValue(ledger as never);
    vi.mocked(ApiCalls.fetchCharacterDetails).mockResolvedValue({
      summary: [
        { name: "Income from Bounty", amount: 1000, average: 1, average_tick: 1, ref_types: ["bounty_prizes"] },
      ],
      daily: [],
      hourly: [],
      total: { summary: 1000, daily: 0, hourly: 0 },
    } as never);
    renderPage();

    // Test Action
    const buttons = await screen.findAllByRole("button", { name: "View Details" });
    await user.click(buttons[buttons.length - 1]);

    // Expected Result
    await waitFor(() =>
      expect(ApiCalls.fetchCharacterDetails).toHaveBeenCalledWith(
        1,
        { year: 2026, month: 10 },
        "single",
      ),
    );
    expect(await screen.findAllByText("Income from Bounty")).not.toHaveLength(0);
  });
});
