// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// AA Ledger
import type { LedgerOverviewOwnerSchema } from "@/Api/schema";
import { OverviewOwnerCard } from "@/Components/Overview/OverviewOwnerCard";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

describe("OverviewOwnerCard", () => {
  it("should render character owner with portrait and links correctly", () => {
    // Test Data
    const characterOwner: LedgerOverviewOwnerSchema = {
      id: 12345,
      name: "Pilot Alpha",
      type: "character",
      type_display: "Character",
      active: true,
      portrait_url: "https://images.evetech.net/characters/12345/portrait",
      subtitle: "Federal Defense Union",
      has_planetary: true,
      can_manage: true,
      has_errors: false,
    };

    // Test Action
    render(
      <MemoryRouter>
        <OverviewOwnerCard owner={characterOwner} />
      </MemoryRouter>,
    );

    // Expected Result
    expect(screen.getByText("Pilot Alpha")).toBeInTheDocument();
    expect(screen.getByText("Federal Defense Union")).toBeInTheDocument();
    expect(screen.getByText("Character")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Planetary")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Ledger/i })).toHaveAttribute(
      "href",
      "/character/12345/",
    );
    expect(screen.getByRole("link", { name: /View Planetary/i })).toHaveAttribute(
      "href",
      "/planetary/12345/",
    );
  });

  it("should render corporation owner without planetary link and fallback icon if portrait missing", () => {
    // Test Data
    const corpOwner: LedgerOverviewOwnerSchema = {
      id: 67890,
      name: "Acme Mining Corp",
      type: "corporation",
      type_display: "Corporation",
      active: false,
      portrait_url: "",
      subtitle: "Highsec Mining",
      has_planetary: false,
      can_manage: false,
      has_errors: false,
    };

    // Test Action
    render(
      <MemoryRouter>
        <OverviewOwnerCard owner={corpOwner} />
      </MemoryRouter>,
    );

    // Expected Result
    expect(screen.getByText("Acme Mining Corp")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
    expect(screen.getByText("Corporation")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Ledger/i })).toHaveAttribute(
      "href",
      "/corporation/67890/",
    );
    expect(screen.queryByRole("link", { name: /View Planetary/i })).not.toBeInTheDocument();
  });
});
