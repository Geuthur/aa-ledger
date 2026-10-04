// React
import { Link } from "react-router";

// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { useTranslation } from "react-i18next";

import ErrorLoader from "@/Components/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Loader/FetchingLoader";
import BaseSectionHeader from "@/Components/Sections/BaseHeader";
import { BaseTable } from "@/Components/Tables/BaseTable";

export interface OverviewItem {
  id: number;
  name: string;
  subtitle?: string;
  icon: string;
  /** Absolute app route of the ledger of this item. */
  to: string;
}

const columnHelper = createColumnHelper<OverviewItem>();

export interface OverviewPageProps {
  title: string;
  nameLabel: string;
  subtitleLabel?: string;
  items: OverviewItem[];
  isLoading: boolean;
  error: Error | null;
}

/** A searchable list of owners that links to their ledger. */
function OverviewPage({
  title,
  nameLabel,
  subtitleLabel,
  items,
  isLoading,
  error,
}: OverviewPageProps) {
  const { t } = useTranslation();

  const columns = [
    columnHelper.accessor("name", {
      header: nameLabel,
      cell: ({ row }) => (
        <Link to={row.original.to} className="d-inline-flex align-items-center gap-2">
          <img src={row.original.icon} alt="" width={32} height={32} className="rounded-circle" />
          {row.original.name}
        </Link>
      ),
    }),
    ...(subtitleLabel
      ? [columnHelper.accessor("subtitle", { header: subtitleLabel })]
      : []),
  ] as ColumnDef<OverviewItem, unknown>[];

  return (
    <main>
      <BaseSectionHeader name={title} />
      <section className="mt-3">
        {isLoading && <FetchingLoader message={t("Loading...")} />}
        {error && <ErrorLoader title={t("Error")} message={error.message} />}
        {!isLoading && !error && (
          <BaseTable
            columns={columns}
            data={items}
            emptyText={t("Nothing to show")}
            initialState={{ sorting: [{ id: "name", desc: false }] }}
            exportFileName="overview.csv"
          />
        )}
      </section>
    </main>
  );
}

export default OverviewPage;
