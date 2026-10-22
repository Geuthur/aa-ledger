// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// AA Ledger
import {
  SuperuserKpiCards,
  type SuperuserMetrics,
} from "@/Components/Superuser/SuperuserKpiCards";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("SuperuserKpiCards", () => {
  it("should render metric values correctly when no sync issues exist", () => {
    // Test Data
    const metrics: SuperuserMetrics = {
      total: 42,
      characters: 30,
      corporations: 12,
      issues: 0,
    };

    // Test Action
    render(<SuperuserKpiCards metrics={metrics} />);

    // Expected Result
    expect(screen.getByText("Total Owners")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("Characters")).toBeInTheDocument();
    expect(screen.getByText("30")).toBeInTheDocument();
    expect(screen.getByText("Corporations")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Sync Issues")).toBeInTheDocument();
    const issueElement = screen.getByText("0");
    expect(issueElement).toHaveClass("text-success");
  });

  it("should highlight sync issues with text-danger when issues > 0", () => {
    // Test Data
    const metrics: SuperuserMetrics = {
      total: 10,
      characters: 8,
      corporations: 2,
      issues: 3,
    };

    // Test Action
    render(<SuperuserKpiCards metrics={metrics} />);

    // Expected Result
    const issueElement = screen.getByText("3");
    expect(issueElement).toHaveClass("text-danger");
  });
});
