// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA Ledger
import { OwnerFilterBar } from "@/Components/Base/BaseSettings/FilterBar";

const counts = { all: 3, character: 2, corporation: 1, alliance: 0 };

describe("OwnerFilterBar", () => {
  it("should hide type buttons without owners", () => {
    // Test Data
    const props = {
      search: "",
      onSearchChange: vi.fn(),
      typeFilter: "all" as const,
      onTypeChange: vi.fn(),
      counts,
    };

    // Test Action
    render(<OwnerFilterBar {...props} />);

    // Expected Result
    expect(screen.getByRole("button", { name: /All \(3\)/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Characters \(2\)/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Alliances/ })).not.toBeInTheDocument();
  });

  it("should call callbacks on type click and typing", async () => {
    // Test Data
    const user = userEvent.setup();
    const onTypeChange = vi.fn();
    const onSearchChange = vi.fn();

    // Test Action
    render(
      <OwnerFilterBar
        search=""
        onSearchChange={onSearchChange}
        typeFilter="all"
        onTypeChange={onTypeChange}
        counts={counts}
      />,
    );
    await user.click(screen.getByRole("button", { name: /Corporations/ }));
    await user.type(screen.getByRole("searchbox"), "a");

    // Expected Result
    expect(onTypeChange).toHaveBeenCalledWith("corporation");
    expect(onSearchChange).toHaveBeenCalledWith("a");
  });
});
