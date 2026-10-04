// Third Party
import { useTranslation } from "react-i18next";

import { useDateFilter } from "@/Hooks/useDateFilter";

const MONTHS = Array.from({ length: 12 }, (_, index) => index + 1);
const DAYS = Array.from({ length: 31 }, (_, index) => index + 1);

export interface DateFilterBarProps {
  /** Years that have journal entries, as returned by the ledger endpoints. */
  years: number[];
  /** Additional filters, e.g. the corporation division. */
  children?: React.ReactNode;
}

function DateFilterBar({ years, children }: DateFilterBarProps) {
  const { t, i18n } = useTranslation();
  const { year, month, day, setYear, setMonth, setDay } = useDateFilter();

  const monthName = (value: number) =>
    new Intl.DateTimeFormat(i18n.language, { month: "long" }).format(new Date(2000, value - 1, 1));

  // The selected year stays selectable even if it has no entries (e.g. the current year).
  const yearOptions = [...new Set([...years, year])].sort((a, b) => b - a);

  return (
    <>
      <select
        aria-label={t("Year")}
        className="lg-select"
        value={year}
        onChange={(event) => setYear(Number(event.target.value))}
      >
        {yearOptions.map((value) => (
          <option key={value} value={value}>
            {value}
          </option>
        ))}
      </select>

      <select
        aria-label={t("Month")}
        className="lg-select"
        value={month ?? ""}
        onChange={(event) => setMonth(event.target.value ? Number(event.target.value) : null)}
      >
        <option value="">{t("All Months")}</option>
        {MONTHS.map((value) => (
          <option key={value} value={value}>
            {monthName(value)}
          </option>
        ))}
      </select>

      <select
        aria-label={t("Day")}
        className="lg-select"
        value={day ?? ""}
        disabled={month === null}
        onChange={(event) => setDay(event.target.value ? Number(event.target.value) : null)}
      >
        <option value="">{t("All Days")}</option>
        {DAYS.map((value) => (
          <option key={value} value={value}>
            {value}
          </option>
        ))}
      </select>

      {children}
    </>
  );
}

export default DateFilterBar;
