// React
import { MemoryRouter } from "react-router";

// Third Party
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import MembersModal from "@/Components/Ledger/MembersModal";
import type { LedgerRow } from "@/Utils/ledger";

const renderModal = (row: LedgerRow | null, onHide = vi.fn()) =>
  render(
    <MemoryRouter>
      <MembersModal row={row} onHide={onHide} />
    </MemoryRouter>,
  );

const ledger = (bounty: number) => ({ bounty, ess: 0, miscellaneous: 0, costs: 0, total: bounty });

const row: LedgerRow = {
  id: 1,
  name: "Main Pilot",
  alts: [],
  bounty: 1300,
  ess: 0,
  miscellaneous: 0,
  costs: 0,
  total: 1300,
  members: [
    { character_id: 1, character_name: "Main Pilot", icon: null, is_registered: true, ledger: ledger(1000) },
    { character_id: 2, character_name: "Alt Pilot", icon: null, is_registered: false, ledger: ledger(300) },
  ],
};

describe("MembersModal", () => {
  it("lists every character with its contribution and share", () => {
    // Test Action
    renderModal(row);

    // Expected Result
    const alt = screen.getByRole("row", { name: /Alt Pilot/ });
    expect(within(alt).getByText("23.1%")).toBeInTheDocument();
    expect(within(screen.getByRole("row", { name: /Main Pilot/ })).getByText("76.9%")).toBeInTheDocument();
  });

  it("stays closed without an entity", () => {
    // Test Action
    renderModal(null);

    // Expected Result
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("calls onHide when closed", async () => {
    // Test Data
    const onHide = vi.fn();
    renderModal(row, onHide);

    // Test Action
    await userEvent.click(screen.getAllByRole("button", { name: "Close" })[0]);

    // Expected Result
    expect(onHide).toHaveBeenCalled();
  });
});
