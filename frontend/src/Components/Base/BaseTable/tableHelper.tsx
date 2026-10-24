// Third Party
import type {
  Header,
  HeaderGroup,
  Table as ReactTable,
} from "@tanstack/react-table";

/**
 * Helper function for exporting table data to CSV
 * @param table The React Table instance containing the data
 * @param exportFileName Optional file name for the exported CSV
 */
export const exportToCSV = <TData,>(table: ReactTable<TData>, exportFileName?: string) => {
  const { rows } = table.getFilteredRowModel();
  const safeFileName = exportFileName ?? "ExportedData.csv";

  const headerRows = table.getHeaderGroups().map((headerGroup: HeaderGroup<TData>) =>
    headerGroup.headers.map((header: Header<TData, unknown>) => {
      if (typeof header.column.columnDef.header === "function") {
        return (header.column.columnDef as { accessorKey?: string }).accessorKey;
      }
      return header.column.columnDef.header;
    }),
  );

  const csvData = rows.map((row) => row.getVisibleCells().map((cell) => cell.getValue()));

  const formatCsvField = (val: unknown): string => {
    if (val === null || val === undefined) return "";
    const str = String(val);
    if (str.includes(",") || str.includes('"') || str.includes("\n") || str.includes("\r")) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const csv = [...headerRows, ...csvData]
    .map((row) => row.map(formatCsvField).join(","))
    .join("\r\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf8;" });

  const link = document.createElement("a");
  link.download = safeFileName;
  link.href = URL.createObjectURL(blob);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
