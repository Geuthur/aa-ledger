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
  registered: [{ owner_id: 1, name: "Alice", icon: "a.png", status: "ok" }],
  missing: [{ owner_id: 2, name: "Alice Alt", icon: "b.png" }],
  members: [],
};

const renderView = (onDelete = vi.fn().mockResolvedValue({ message: "Alice successfully deleted" })) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AdministrationView
          title="Character Administration"
          data={data}
          isLoading={false}
          error={null}
          entryLabel="Character"
          queryKey={["admin"]}
          ledgerPath={(id) => `/ledger/character/${id}/`}
          onDelete={onDelete}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return onDelete;
};

describe("AdministrationView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows statistics, issues and missing entries", () => {
    // Test Action
    renderView();

    // Expected Result
    expect(screen.getByText("Character Administration - Alice")).toBeInTheDocument();
    expect(screen.getByText(/Alice$/, { selector: ".alert" })).toBeInTheDocument();
    expect(screen.getByText("Alice Alt")).toBeInTheDocument();
    expect(screen.getByText("Character is not registered in Ledger.")).toBeInTheDocument();
  });

  it("deletes an entry after confirmation", async () => {
    // Test Data
    const user = userEvent.setup();
    const onDelete = renderView();

    // Test Action
    await user.click(screen.getByRole("button", { name: "Delete" }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));

    // Expected Result
    await waitFor(() => expect(onDelete).toHaveBeenCalledWith(1));
    expect(await screen.findByText("Alice successfully deleted")).toBeInTheDocument();
  });
});
