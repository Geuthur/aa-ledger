// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import BaseTable from "@/Components/Base/BaseTable/BaseTable";

interface TestRow {
  id: number;
  name: string;
  role: string;
}

const columnHelper = createColumnHelper<TestRow>();

const testColumns = [
  columnHelper.accessor("name", {
    header: "Name",
    enableColumnFilter: true,
  }),
  columnHelper.accessor("role", {
    header: "Role",
    enableColumnFilter: true,
  }),
];

const testData: TestRow[] = [
  { id: 1, name: "Alice", role: "Pilot" },
  { id: 2, name: "Bob", role: "Miner" },
  { id: 3, name: "Charlie", role: "Industrialist" },
];

const renderTable = (props?: Partial<React.ComponentProps<typeof BaseTable<TestRow>>>) => {
  return render(
    <MemoryRouter>
      <BaseTable
        columns={testColumns}
        data={testData}
        {...props}
      />
    </MemoryRouter>,
  );
};

describe("BaseTable", () => {
  it("test_render_should_display_aa_table_with_data", () => {
    // Test Data
    const data = testData;

    // Test Action
    const { container } = renderTable({ data });

    // Expected Result
    expect(container.querySelector(".aa-table-shell")).toBeInTheDocument();
    expect(container.querySelector(".aa-table")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("Charlie")).toBeInTheDocument();
  });

  it("test_render_should_display_empty_text_when_no_data", () => {
    // Test Data
    const emptyText = "No pilot records available";

    // Test Action
    renderTable({ data: [], emptyText });

    // Expected Result
    expect(screen.getByText(emptyText)).toBeInTheDocument();
  });

  it("test_sort_should_toggle_sorting_direction_on_header_click", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable();

    // Test Action: Click sort header
    const nameHeader = screen.getByText("Name");
    await user.click(nameHeader);

    // Expected Result: Alice is first in ascending order
    const cells = screen.getAllByRole("cell");
    expect(cells[0]).toHaveTextContent("Alice");

    // Test Action: Click sort header again for descending
    await user.click(nameHeader);

    // Expected Result: Charlie is first in descending order
    const cellsDesc = screen.getAllByRole("cell");
    expect(cellsDesc[0]).toHaveTextContent("Charlie");
  });

  it("test_filter_should_render_filter_inputs_when_enabled", () => {
    // Test Data & Test Action
    const { container } = renderTable({ enableFilters: true });

    // Expected Result
    expect(container.querySelector(".aa-table-filter-row")).toBeInTheDocument();
    expect(container.querySelectorAll(".aa-table-filter-cell").length).toBe(2);
  });

  it("test_filter_should_omit_filter_row_when_disabled", () => {
    // Test Data & Test Action
    const { container } = renderTable({ enableFilters: false });

    // Expected Result
    expect(container.querySelector(".aa-table-filter-row")).not.toBeInTheDocument();
  });

  it("test_pagination_should_navigate_pages_when_page_size_exceeded", async () => {
    // Test Data
    const user = userEvent.setup();
    const lotsOfData: TestRow[] = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      name: `Pilot ${i + 1}`,
      role: "Member",
    }));

    // Test Action
    renderTable({
      data: lotsOfData,
      initialState: { pagination: { pageSize: 10 } },
      pageSizeOptions: [10, 25],
    });

    // Expected Result: Page 1 shows first 10
    expect(screen.getByText("Pilot 1")).toBeInTheDocument();
    expect(screen.queryByText("Pilot 15")).not.toBeInTheDocument();

    // Test Action: Click Next Page
    const nextBtn = screen.getByTitle("Next Page");
    await user.click(nextBtn);

    // Expected Result: Page 2 shows next 10
    expect(screen.getByText("Pilot 15")).toBeInTheDocument();
    expect(screen.queryByText("Pilot 1")).not.toBeInTheDocument();
  });

  it("test_row_click_should_call_on_row_click_with_row", async () => {
    // Test Data
    const user = userEvent.setup();
    const onRowClick = vi.fn();
    renderTable({ onRowClick });

    // Test Action
    await user.click(screen.getByText("Bob"));

    // Expected Result
    expect(onRowClick).toHaveBeenCalledTimes(1);
    expect(onRowClick.mock.calls[0][0].original).toEqual(testData[1]);
  });

  it("test_row_selection_should_report_selected_rows_by_row_id", async () => {
    // Test Data
    const user = userEvent.setup();
    const onRowSelectionChange = vi.fn();
    const selectColumn = columnHelper.display({
      id: "select",
      cell: ({ row }) => (
        <input
          type="checkbox"
          aria-label={`select-${row.original.id}`}
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
        />
      ),
    });
    renderTable({
      columns: [selectColumn, ...testColumns] as typeof testColumns,
      getRowId: (row) => String(row.id),
      rowSelection: {},
      onRowSelectionChange,
      enableRowSelection: true,
    });

    // Test Action
    await user.click(screen.getByLabelText("select-2"));

    // Expected Result
    expect(onRowSelectionChange).toHaveBeenCalledTimes(1);
    const updater = onRowSelectionChange.mock.calls[0][0];
    expect(typeof updater === "function" ? updater({}) : updater).toEqual({ "2": true });
  });
});
