// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ExtractorProgress from "@/Components/Planetary/ExtractorProgress";

describe("ExtractorProgress", () => {
  it("shows the progress as bar and label", () => {
    // Test Action
    render(<ExtractorProgress progress={42.5} />);

    // Expected Result
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "42.5");
    expect(screen.getByText("42.5%")).toBeInTheDocument();
  });

  it("keeps the progress within 0 and 100", () => {
    // Test Action
    render(<ExtractorProgress progress={140} />);

    // Expected Result
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "100");
  });
});
