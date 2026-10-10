// React
import { MemoryRouter } from "react-router";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AdministrationView from "@/Components/Administration/AdministrationView";

const data = {
  owner: { character_id: 1, character_name: "Alice", icon: "a.png" },
  dashboard: { auth_count: 3, active_count: 1, inactive_count: 0, missing_count: 2, issues: ["Alice"] },
  registered: [{ owner_id: 1, name: "Alice", icon: "a.png", status: "ok", last_sync: "2026-10-10T10:00:00Z" }],
  missing: [{ owner_id: 2, name: "Alice Alt", icon: "b.png" }],
  members: [],
  last_sync: "2026-10-10T10:00:00Z",
  can_update: true,
  cooldown_seconds: 0,
};

const renderView = ({
  onDelete = vi.fn().mockResolvedValue({ message: "Alice successfully deleted" }),
  onUpdate,
  customData,
}: {
  onDelete?: (id: number) => Promise<{ message: string }>;
  onUpdate?: () => Promise<{ message: string }>;
  customData?: typeof data;
} = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AdministrationView
          title="Character Administration"
          data={customData ?? data}
          isLoading={false}
          error={null}
          entryLabel="Character"
          queryKey={["admin"]}
          ledgerPath={(id) => `/ledger/character/${id}/`}
          onDelete={onDelete}
          onUpdate={onUpdate}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { onDelete, onUpdate };
};

describe("AdministrationView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows statistics, issues, missing entries, and last sync", () => {
    // Test Action
    renderView();

    // Expected Result
    expect(screen.getByText("Character Administration - Alice")).toBeInTheDocument();
    expect(screen.getByText(/Alice$/, { selector: ".alert" })).toBeInTheDocument();
    expect(screen.getByText("Alice Alt")).toBeInTheDocument();
    expect(screen.getByText("Character is not registered in Ledger.")).toBeInTheDocument();
    expect(screen.getByText("Last Sync:")).toBeInTheDocument();
  });

  it("deletes an entry after confirmation", async () => {
    // Test Data
    const user = userEvent.setup();
    const { onDelete } = renderView();

    // Test Action
    await user.click(screen.getByRole("button", { name: "Delete" }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));

    // Expected Result
    await waitFor(() => expect(onDelete).toHaveBeenCalledWith(1));
    expect(await screen.findByText("Alice successfully deleted")).toBeInTheDocument();
  });

  it("triggers manual update when update button clicked", async () => {
    // Test Data
    const user = userEvent.setup();
    const onUpdate = vi.fn().mockResolvedValue({ message: "Update queued" });
    renderView({ onUpdate });

    // Test Action
    await user.click(screen.getByRole("button", { name: "Update" }));

    // Expected Result
    await waitFor(() => expect(onUpdate).toHaveBeenCalled());
    expect(await screen.findByText("Update queued")).toBeInTheDocument();
  });

  it("disables update button when cooldown is active", () => {
    // Test Data
    const onUpdate = vi.fn();

    // Test Action
    renderView({
      onUpdate,
      customData: {
        ...data,
        can_update: false,
        cooldown_seconds: 180,
      },
    });

    // Expected Result
    const updateBtn = screen.getByRole("button", { name: "Update" });
    expect(updateBtn).toBeDisabled();
    expect(screen.getByText(/Update \(3:00\)/)).toBeInTheDocument();
  });

  it("does not render header last sync when last_sync is null and onUpdate is not provided", () => {
    // Test Action
    renderView({
      customData: {
        ...data,
        last_sync: null,
      },
    });

    // Expected Result
    expect(screen.queryByText("Last Sync:")).not.toBeInTheDocument();
  });
});
