// React
import { MemoryRouter } from "react-router";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as ApiCalls from "@/Api/ApiCalls";
import PlanetModal from "@/Components/Planetary/PlanetModal";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return { ...actual, fetchPlanetDetails: vi.fn() };
});

const details = {
  owner: { character_id: 1, character_name: "Alice" },
  planet: {
    id: 5,
    name: "Jita IV",
    type: { id: 11, name: "Temperate", icon: "planet.png" },
    upgrade_level: 5,
    num_pins: 10,
    last_update: null,
  },
  extractors: [
    {
      item_id: 2268,
      item_name: "Aqueous Liquids",
      icon: "liquids.png",
      install_time: "2026-10-01T10:00:00Z",
      expiry_time: "2026-10-05T10:00:00Z",
      progress: 42.5,
    },
  ],
  factories: [
    {
      factory_name: "Basic Industry",
      input_products: [{ item_id: 2268, item_name: "Aqueous Liquids", icon: "liquids.png" }],
      output_product: { item_id: 3645, item_name: "Water", icon: "water.png" },
      is_active: true,
    },
  ],
  storage: [
    {
      factory_name: "Storage Facility",
      product: { item_id: 3645, item_name: "Water", item_quantity: 1500, icon: "water.png" },
    },
  ],
};

const renderModal = (ownerId: number | null = 1, planetId: number | null = 5) => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <PlanetModal ownerId={ownerId} planetId={planetId} onHide={vi.fn()} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("PlanetModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows extractors, factories and storage of the planet", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchPlanetDetails).mockResolvedValue(details as never);

    // Test Action
    renderModal();

    // Expected Result
    expect(await screen.findByText("Jita IV")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Basic Industry")).toBeInTheDocument();
    expect(screen.getByText("Storage Facility")).toBeInTheDocument();
    expect(screen.getByText("1,500")).toBeInTheDocument();
    expect(screen.getAllByText("Aqueous Liquids")).toHaveLength(2);
    expect(ApiCalls.fetchPlanetDetails).toHaveBeenCalledWith(1, 5);
  });

  it("does not request anything while closed", () => {
    // Test Action
    renderModal(null, null);

    // Expected Result
    expect(ApiCalls.fetchPlanetDetails).not.toHaveBeenCalled();
  });

  it("shows the API error", async () => {
    // Test Data
    vi.mocked(ApiCalls.fetchPlanetDetails).mockRejectedValue(new Error("Planet not found."));

    // Test Action
    renderModal();

    // Expected Result
    expect(await screen.findByText("Planet not found.")).toBeInTheDocument();
  });
});
