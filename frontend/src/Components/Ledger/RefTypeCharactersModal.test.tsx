// React
import { MemoryRouter } from "react-router";

// Third Party
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { RefTypeAmountSchema } from "@/Api/schema";
import RefTypeCharactersModal from "@/Components/Ledger/RefTypeCharactersModal";

const refTypeData: RefTypeAmountSchema = {
  ref_type: "bounty_prizes",
  amount: 1500,
  characters: [
    {
      character_id: 1,
      character_name: "Pilot One",
      amount: 1000,
      icon: "https://images.evetech.net/characters/1/portrait?size=32",
    },
    {
      character_id: 2,
      character_name: "Pilot Two",
      amount: 500,
      icon: "https://images.evetech.net/characters/2/portrait?size=32",
    },
  ],
};

const renderModal = (refType: RefTypeAmountSchema | null, onHide = vi.fn()) =>
  render(
    <MemoryRouter>
      <RefTypeCharactersModal refType={refType} onHide={onHide} />
    </MemoryRouter>,
  );

describe("RefTypeCharactersModal", () => {
  it("renders the characters with amounts and shares", () => {
    // Test Action
    renderModal(refTypeData);

    // Expected Result
    expect(screen.getByText("Bounty Prizes")).toBeInTheDocument();
    expect(screen.getByText("Pilot One")).toBeInTheDocument();
    expect(screen.getByText("Pilot Two")).toBeInTheDocument();
    expect(screen.getByText("1,000 ISK")).toBeInTheDocument();
    expect(screen.getByText("500 ISK")).toBeInTheDocument();
    expect(screen.getByText("66.7%")).toBeInTheDocument();
    expect(screen.getByText("33.3%")).toBeInTheDocument();
  });

  it("stays closed when refType is null", () => {
    // Test Action
    renderModal(null);

    // Expected Result
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("calls onHide when Close button is clicked", () => {
    // Test Data
    const onHide = vi.fn();
    renderModal(refTypeData, onHide);

    // Test Action
    fireEvent.click(screen.getAllByRole("button", { name: "Close" })[0]);

    // Expected Result
    expect(onHide).toHaveBeenCalledOnce();
  });
});
