// Third Party
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import RefTypeBadges from "@/Components/Ledger/DetailsModal/RefTypeBadges";

const refTypes = (count: number) =>
  Array.from({ length: count }, (_, index) => ({
    ref_type: `type_${index}`,
    amount: 100 - index,
    characters: [],
  }));

describe("RefTypeBadges", () => {
  it("shows a badge for every reference type up to ten", () => {
    // Test Action
    render(<RefTypeBadges refTypes={refTypes(10)} onShowAll={vi.fn()} />);

    // Expected Result
    expect(screen.getByText("Type 0")).toBeInTheDocument();
    expect(screen.getByText("Type 9")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("moves the rest behind a button", () => {
    // Test Data
    const onShowAll = vi.fn();
    render(<RefTypeBadges refTypes={refTypes(13)} onShowAll={onShowAll} />);

    // Test Action
    fireEvent.click(screen.getByRole("button", { name: "+3 more" }));

    // Expected Result
    expect(screen.queryByText("Type 10")).not.toBeInTheDocument();
    expect(onShowAll).toHaveBeenCalledOnce();
  });

  it("prints the amount into the badge when asked to", () => {
    // Test Action
    render(<RefTypeBadges refTypes={refTypes(1)} showAmounts onShowAll={vi.fn()} />);

    // Expected Result
    expect(screen.getByText("Type 0: 100 ISK")).toBeInTheDocument();
  });

  it("calls onSelectRefType when clicking a badge with characters", () => {
    // Test Data
    const onSelectRefType = vi.fn();
    const item = {
      ref_type: "bounty_prizes",
      amount: 1000,
      characters: [{ character_id: 1, character_name: "Pilot Alpha", amount: 1000 }],
    };

    // Test Action
    render(<RefTypeBadges refTypes={[item]} onShowAll={vi.fn()} onSelectRefType={onSelectRefType} />);
    fireEvent.click(screen.getByRole("button", { name: "Bounty Prizes" }));

    // Expected Result
    expect(onSelectRefType).toHaveBeenCalledWith(item);
  });
});
