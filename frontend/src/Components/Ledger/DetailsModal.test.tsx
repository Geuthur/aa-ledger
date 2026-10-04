// React
import { MemoryRouter } from "react-router";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { LedgerDetailsResponse } from "@/Api/schema";
import DetailsModal from "@/Components/Ledger/DetailsModal";

const category = (name: string, refTypes: [string, number][]) => ({
  name,
  amount: refTypes.reduce((sum, [, amount]) => sum + amount, 0),
  average: 0,
  average_tick: 0,
  ref_types: refTypes.map(([ref_type, amount]) => ({ ref_type, amount })),
});

const many = Array.from({ length: 12 }, (_, index): [string, number] => [`type_${index}`, 100 - index]);

const response = {
  summary: [
    category("Income from Market", [
      ["market_transaction", 300],
      ["brokers_fee", 100],
    ]),
    category("Cost from Market", [["market_transaction", -40]]),
    category("Income from Contract", many),
  ],
  daily: [],
  hourly: [],
  total: { summary: 0, daily: 0, hourly: 0 },
} as LedgerDetailsResponse;

const renderModal = () =>
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter>
        <DetailsModal
          entityId={1}
          title="Details"
          queryKey={["details"]}
          queryFn={vi.fn().mockResolvedValue(response)}
          onHide={vi.fn()}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );

describe("DetailsModal", () => {
  it("shows at most ten reference type badges and offers the rest in a modal", async () => {
    // Test Data
    renderModal();
    const row = (await screen.findByText("Income from Contract")).closest("tr") as HTMLElement;

    // Expected Result
    expect(within(row).queryByText("Type 10")).not.toBeInTheDocument();

    // Test Action
    fireEvent.click(within(row).getByRole("button", { name: "+2 more" }));

    // Expected Result
    const dialog = (await screen.findAllByRole("dialog")).at(-1) as HTMLElement;
    expect(within(dialog).getByText("Type 11")).toBeInTheDocument();
  });

  it("filters the categories by reference type and sums up the matches", async () => {
    // Test Data
    renderModal();
    await screen.findByText("Income from Contract");

    // Test Action
    fireEvent.change(screen.getByRole("searchbox", { name: "Search reference type" }), {
      target: { value: "market trans" },
    });

    // Expected Result
    expect(screen.queryByText("Income from Contract")).not.toBeInTheDocument();
    expect(screen.getByText("Cost from Market")).toBeInTheDocument();
    const matches = screen.getByRole("region", { name: "Matching reference types" });
    expect(matches).toHaveTextContent("Market Transaction");
    expect(matches).toHaveTextContent("260 ISK");
  });

  it("says so when no reference type matches", async () => {
    // Test Data
    renderModal();
    await screen.findByText("Income from Contract");

    // Test Action
    fireEvent.change(screen.getByRole("searchbox", { name: "Search reference type" }), {
      target: { value: "nothing" },
    });

    // Expected Result
    expect(screen.getByRole("region", { name: "Matching reference types" })).toHaveTextContent(
      "No matching reference types",
    );
  });
});
