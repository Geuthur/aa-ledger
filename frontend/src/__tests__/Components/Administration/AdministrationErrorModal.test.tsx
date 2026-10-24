// React
import { MemoryRouter } from "react-router";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { describe, expect, it, vi } from "vitest";

// AA Ledger
import type { AdministrationOwnerSchema } from "@/Api/schema";
import { AdministrationErrorModal } from "@/Components/Administration/AdministrationErrorModal";
import { AdministrationOwnersTable } from "@/Components/Administration/AdministrationOwnersTable";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, options?: Record<string, string>) =>
      key.replace(/\{\{(\w+)\}\}/g, (_, name) => options?.[name] ?? ""),
  }),
}));

const buildOwner = (overrides: Partial<AdministrationOwnerSchema>): AdministrationOwnerSchema => ({
  id: 1,
  owner_id: 1001,
  owner_type: "character",
  name: "John Doe",
  ticker: null,
  status: "ok",
  is_active: true,
  last_sync: "2026-10-18T12:00:00Z",
  alts: [],
  ...overrides,
});

const renderTable = (owners: AdministrationOwnerSchema[]) => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <NuqsTestingAdapter hasMemory>
          <AdministrationOwnersTable
            owners={owners}
            isLoading={false}
            isError={false}
            updatingKey={null}
            onInspect={vi.fn()}
            onTriggerUpdate={vi.fn()}
            onDelete={vi.fn()}
          />
        </NuqsTestingAdapter>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("AdministrationErrorModal", () => {
  it("should render owner name, status and full message when shown", () => {
    // Test Data
    const props = {
      show: true,
      onHide: vi.fn(),
      ownerName: "John Doe",
      status: "error",
      errorMessage: "ESI returned 500 for /characters/1001/",
    };

    // Test Action
    render(<AdministrationErrorModal {...props} />);

    // Expected Result
    expect(screen.getByTestId("error-modal-message")).toHaveTextContent(
      "ESI returned 500 for /characters/1001/",
    );
    expect(screen.getByTestId("error-modal-status")).toHaveTextContent("error");
    expect(screen.getByText("Error details of John Doe")).toBeInTheDocument();
  });

  it("should show default text when status is token_error without message", () => {
    // Test Data
    const props = {
      show: true,
      onHide: vi.fn(),
      ownerName: "John Doe",
      status: "token_error",
      errorMessage: null,
    };

    // Test Action
    render(<AdministrationErrorModal {...props} />);

    // Expected Result
    expect(screen.getByTestId("error-modal-message")).toHaveTextContent(
      "The ESI token is invalid or expired. Re-add the character or corporation.",
    );
  });
});

describe("AdministrationOwnersTable status badge", () => {
  it("should open the error modal when the badge is clicked", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable([buildOwner({ status: "error", error_message: "Sync failed badly" })]);

    // Test Action
    await user.click(screen.getByRole("button", { name: "Show error details of John Doe" }));

    // Expected Result
    expect(await screen.findByTestId("error-modal-message")).toHaveTextContent("Sync failed badly");
  });

  it("should open the error modal via keyboard when the badge is focused", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable([buildOwner({ status: "error", error_message: "Keyboard message" })]);
    const badge = screen.getByRole("button", { name: "Show error details of John Doe" });

    // Test Action
    badge.focus();
    await user.keyboard("{Enter}");

    // Expected Result
    expect(badge).toHaveAttribute("tabindex", "0");
    expect(await screen.findByTestId("error-modal-message")).toHaveTextContent("Keyboard message");
  });

  it("should not render the message inline in the table row", () => {
    // Test Data
    renderTable([buildOwner({ status: "error", error_message: "Hidden until clicked" })]);

    // Test Action
    const inline = screen.queryByText("Hidden until clicked");

    // Expected Result
    expect(inline).not.toBeInTheDocument();
  });

  it("should not make the badge clickable when there is no error", () => {
    // Test Data
    renderTable([buildOwner({ status: "ok", error_message: null })]);

    // Test Action
    const badge = screen.getByText("ok");

    // Expected Result
    expect(badge).not.toHaveAttribute("role", "button");
    expect(screen.queryByRole("button", { name: /Show error details/ })).not.toBeInTheDocument();
  });

  it("should open the modal with default text for token_error without message", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable([buildOwner({ status: "token_error", error_message: null })]);

    // Test Action
    await user.click(screen.getByRole("button", { name: "Show error details of John Doe" }));

    // Expected Result
    expect(await screen.findByTestId("error-modal-message")).toHaveTextContent(
      "The ESI token is invalid or expired.",
    );
  });
});
