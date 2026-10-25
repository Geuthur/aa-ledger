// Third Party
import i18n from "i18next";

/**
 * Formats a date string with Intl.DateTimeFormat
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
 * Helper function for locale aware number formatting
 * @param value The number to format
 * @param locale Optional locale string (defaults to the current i18n language)
 * @param options Optional Intl.NumberFormatOptions for custom formatting
 */
export function formatNumber(value: number, locale?: string, options?: Intl.NumberFormatOptions) {
  const effectiveLocale = locale || i18n.language || "en";
  return new Intl.NumberFormat(effectiveLocale, options).format(value);
}

/**
 * Formats a number compactly with K, M or B suffix (e.g. 2.50B, 12.4M, 5.2K)
 * @param value The number to format
 * @param unit Optional unit suffix (defaults to none)
 * @param locale Optional locale string (defaults to the current i18n language)
 * @param options Optional Intl.NumberFormatOptions used for values below 1000
 */
export function formatCompactNumber(
  value: number,
  unit: string = "",
  locale?: string,
  options?: Intl.NumberFormatOptions,
) {
  const suffix = unit ? ` ${unit}` : "";
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B${suffix}`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M${suffix}`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K${suffix}`;
  return `${formatNumber(value, locale, options)}${suffix}`;
}

/**
 * Formats an ISK amount rounded to whole ISK (e.g. "1,234,567 ISK")
 * @param value The ISK amount
 */
export function formatIsk(value: number): string {
  return `${formatNumber(Math.round(value), undefined, { maximumFractionDigits: 0 })} ISK`;
}
