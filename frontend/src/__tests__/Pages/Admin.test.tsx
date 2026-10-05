// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as ApiCalls from "@/Api/ApiCalls";
import Admin from "@/Pages/Admin";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return { ...actual, queueUpdate: vi.fn() };
});

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <Admin />
    </QueryClientProvider>,
  );
};

describe("Admin", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("queues the update of all characters", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.queueUpdate).mockResolvedValue({ message: "Queued Update All Characters" });
    renderPage();

    // Test Action
    await user.click(screen.getAllByRole("button", { name: "Queue Update" })[0]);

    // Expected Result
    expect(await screen.findByText("Queued Update All Characters")).toBeInTheDocument();
    expect(ApiCalls.queueUpdate).toHaveBeenCalledWith({
      target: "characters",
      eve_id: null,
      force_refresh: false,
    });
  });

  it("queues a single corporation with force refresh", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.queueUpdate).mockResolvedValue({ message: "Queued" });
    renderPage();

    // Test Action
    await user.click(screen.getByLabelText("Mark all tasks as Force Refresh"));
    await user.type(screen.getByLabelText("Corporation ID (optional)"), "2001");
    await user.click(screen.getAllByRole("button", { name: "Queue Update" })[1]);

    // Expected Result
    await waitFor(() =>
      expect(ApiCalls.queueUpdate).toHaveBeenCalledWith({
        target: "corporations",
        eve_id: 2001,
        force_refresh: true,
      }),
    );
  });

  it("shows the error of the API", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.queueUpdate).mockRejectedValue(new Error("Character not found."));
    renderPage();

    // Test Action
    await user.type(screen.getByLabelText("Character ID (optional)"), "1");
    await user.click(screen.getAllByRole("button", { name: "Queue Update" })[0]);

    // Expected Result
    expect(await screen.findByText("Character not found.")).toBeInTheDocument();
  });
});
