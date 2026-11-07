// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { formatIsk } from "aa-geuthur-react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LedgerTable, { SHOW_TOTALS_STORAGE_KEY } from "@/Components/Ledger/LedgerView/LedgerTable";
import type { LedgerRow } from "@/Utils/ledger";

const row = (id: number, bounty: number, costs: number): LedgerRow => ({
  id,
  name: `Pilot ${id}`,
  alts: [],
  bounty,
  ess: 0,
  mining: 0,
  miscellaneous: 0,
  costs,
  total: bounty + costs,
});

const renderTable = (rows: LedgerRow[]) =>
  render(
    <MemoryRouter>
      <LedgerTable rows={rows} nameLabel="Character" onDetails={vi.fn()} />
    </MemoryRouter>,
  );

describe("LedgerTable", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("hides the totals row by default", () => {
    // Test Action
    const { container } = renderTable([row(1, 1000, -200)]);

    // Expected Result
    expect(screen.getByLabelText("Show totals row")).not.toBeChecked();
    expect(container.querySelector("tfoot")).not.toBeInTheDocument();
  });

  it("shows the totals of all rows and remembers the choice", async () => {
    // Test Data
    const user = userEvent.setup();
    const rows = Array.from({ length: 20 }, (_, index) => row(index + 1, 1000, -100));

    // Test Action
    const { container } = renderTable(rows);
    await user.click(screen.getByLabelText("Show totals row"));

    // Expected Result
    const footer = container.querySelector("tfoot") as HTMLElement;
    expect(footer).toBeInTheDocument();
    expect(within(footer).getByText(formatIsk(20000))).toBeInTheDocument();
    expect(within(footer).getByText(formatIsk(-2000))).toBeInTheDocument();
    expect(within(footer).getByText(formatIsk(18000))).toBeInTheDocument();
    expect(window.localStorage.getItem(SHOW_TOTALS_STORAGE_KEY)).toBe("true");
  });

  it("restores the stored choice", () => {
    // Test Data
    window.localStorage.setItem(SHOW_TOTALS_STORAGE_KEY, "true");

    // Test Action
    const { container } = renderTable([row(1, 1000, -200)]);

    // Expected Result
    expect(screen.getByLabelText("Show totals row")).toBeChecked();
    expect(container.querySelector("tfoot")).toBeInTheDocument();
  });
});
