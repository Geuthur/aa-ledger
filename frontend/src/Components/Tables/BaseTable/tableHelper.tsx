// Third Party
import type {
  Header,
  HeaderGroup,
  Table as ReactTable,
} from "@tanstack/react-table";
import i18n from "i18next";
import { OverlayTrigger } from "react-bootstrap";
import Tooltip from "react-bootstrap/esm/Tooltip";

// Styles
import styles from "./tableHelper.module.css";

/**
 * Helper functions for formatting dates and rendering HTML safely in React components
 * @param value The date string to format (optional)
 * @param options Optional Intl.DateTimeFormatOptions for customizing the output
 * @returns A formatted date string or "N/A" if the value is not provided
 */
export function formatDate(value?: string | null, options?: Intl.DateTimeFormatOptions): string {
  // Return "N/A" if the value is not provided
  if (!value) {
    return "N/A";
  }

	const locale = i18n.language || "en";
	const hasExplicitTimeFields =
		options && (
			"hour" in options ||
			"minute" in options ||
			"second" in options ||
			"timeStyle" in options
		);
	const hasExplicitDateFields =
		options && (
			"year" in options ||
			"month" in options ||
			"day" in options ||
			"dateStyle" in options
		);

	const formatterOptions: Intl.DateTimeFormatOptions = {
		...(hasExplicitTimeFields || hasExplicitDateFields ? {} : { dateStyle: 'medium', timeStyle: 'short' }),
		...(options ?? {}),
	};

	return new Intl.DateTimeFormat(locale, formatterOptions).format(new Date(value));
}

/**
 * Formats a date relative to now (e.g. "in 15 Minuten", "vor 2 Stunden", "gestern")
 * using the native browser API Intl.RelativeTimeFormat.
 *
 * @param value The date string, timestamp or Date object to format
 * @returns Formatted relative time or "N/A" if value is missing/invalid
 */
export function formatRelativeTime(value?: string | Date | null): string {
  if (!value) {
    return "N/A";
  }

  const date = value instanceof Date ? value : new Date(value);
  if (isNaN(date.getTime())) {
    return "N/A";
  }

  const diffInSeconds = Math.round((date.getTime() - Date.now()) / 1000);

  // Define intervals in seconds
  const intervals = [
    { unit: 'year', seconds: 31536000 },
    { unit: 'month', seconds: 2592000 },
    { unit: 'day', seconds: 86400 },
    { unit: 'hour', seconds: 3600 },
    { unit: 'minute', seconds: 60 },
    { unit: 'second', seconds: 1 },
  ] as const;

  const interval = intervals.find((i) => Math.abs(diffInSeconds) >= i.seconds) ?? intervals[intervals.length - 1];
  const count = Math.round(diffInSeconds / interval.seconds);

  const locale = i18n.language || "en";
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

  return rtf.format(count, interval.unit);
}

/**
 * Formats an ETA date: returns doneLabel (e.g. "Done") if the date has passed,
 * otherwise formats the relative time until that date (e.g. "in 15 Minuten").
 *
 * @param value The date string, timestamp or Date object
 * @param doneLabel The label to return when the ETA has already passed (default: "Done")
 * @returns Formatted ETA string or "N/A" if value is missing/invalid
 */
export function formatEta(value?: string | Date | null, doneLabel = "Done"): string {
  if (!value) {
    return "N/A";
  }

  const date = value instanceof Date ? value : new Date(value);
  if (isNaN(date.getTime())) {
    return "N/A";
  }

  if (date.getTime() <= Date.now()) {
    return doneLabel;
  }

  return formatRelativeTime(date);
}

/**
 * Helper function for rendering pre-rendered HTML safely in React components
 * @param value The HTML string to render
 */
export function renderHtml(value: string) {
	return <span dangerouslySetInnerHTML={{ __html: value }} />
}

/**
 * Helper function for rendering tooltips in a fixed position
 * @param message The message to display inside the tooltip
 * @param children The React element that triggers the tooltip
 */
export function renderTooltip(
  message: string,
  children: React.ComponentProps<typeof OverlayTrigger>["children"],
) {
  return (
    <OverlayTrigger
      trigger={["hover", "focus"]}
      overlay={
        <Tooltip id="aa-example-tooltip" className={styles["tooltip-fixed"]}>
          {message}
        </Tooltip>
      }
    >
      {children}
    </OverlayTrigger>
  );
}

/**
 * Helper function for locateString number formatting
 * @param value The number to format
 * @param locale Optional locale string (defaults to the current i18n language)
 * @param options Optional Intl.NumberFormatOptions for custom formatting
 */
export function formatNumber(value: number, locale?: string, options?: Intl.NumberFormatOptions) {
  const effectiveLocale = locale || i18n.language || "en";
  return new Intl.NumberFormat(effectiveLocale, options).format(value);
}

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
