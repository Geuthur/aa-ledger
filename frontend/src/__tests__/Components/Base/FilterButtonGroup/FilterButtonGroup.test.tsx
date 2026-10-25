// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA Ledger
import { FilterButtonGroup } from "@/Components/Base/FilterButtonGroup";

const options = [
  { value: "all", label: "All", count: 5 },
  { value: "character", label: "Characters", count: 3 },
  { value: "issues", label: "Issues" },
];

describe("FilterButtonGroup", () => {
  it("should render every option and mark the active one as pressed", () => {
    // Test Data
    // (options above)

    // Test Action
    render(<FilterButtonGroup options={options} value="character" onChange={vi.fn()} ariaLabel="Filter" />);

    // Expected Result
    expect(screen.getByRole("group", { name: "Filter" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Characters 3/ })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: /All 5/ })).toHaveAttribute("aria-pressed", "false");
  });

  it("should show a counter only for options that have one", () => {
    // Test Data
    // (the "Issues" option has no count)

    // Test Action
    render(<FilterButtonGroup options={options} value="all" onChange={vi.fn()} ariaLabel="Filter" />);

    // Expected Result
    expect(screen.getByRole("button", { name: "Issues" })).toBeInTheDocument();
  });

  it("should call onChange with the value of the clicked option", async () => {
    // Test Data
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<FilterButtonGroup options={options} value="all" onChange={onChange} ariaLabel="Filter" />);

    // Test Action
    await user.click(screen.getByRole("button", { name: "Issues" }));

    // Expected Result
    expect(onChange).toHaveBeenCalledWith("issues");
  });
});
