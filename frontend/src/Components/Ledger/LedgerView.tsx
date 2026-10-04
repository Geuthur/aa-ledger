// React
import type { ReactNode } from "react";

// Third Party
import { useTranslation } from "react-i18next";

import type { BillboardSchema, Section } from "@/Api/schema";
import DateFilterBar from "@/Components/Filters/DateFilterBar";
import LedgerCharts from "@/Components/Ledger/LedgerCharts";
import LedgerSummary from "@/Components/Ledger/LedgerSummary";
import LedgerTable from "@/Components/Ledger/LedgerTable";
import ErrorLoader from "@/Components/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Loader/FetchingLoader";
import BaseSectionHeader from "@/Components/Sections/BaseHeader";
import { sumRows } from "@/Utils/ledger";
import type { LedgerRow } from "@/Utils/ledger";

export interface LedgerViewProps {
  title: string;
  /** Label of the first table column, e.g. "Character". */
  nameLabel: string;
  rows: LedgerRow[];
  showMining?: boolean;
  billboard?: BillboardSchema;
  years: number[];
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  /** Extra filters next to the date, e.g. the corporation division. */
  filterExtras?: ReactNode;
  onDetails: (entityId: number, section: Section) => void;
  /** Opens the breakdown of the whole owner. */
  onOwnerDetails: () => void;
  /** The details modal. */
  children?: ReactNode;
}

function LedgerView({
  title,
  nameLabel,
  rows,
  showMining,
  billboard,
  years,
  isLoading,
  isFetching,
  error,
  filterExtras,
  onDetails,
  onOwnerDetails,
  children,
}: LedgerViewProps) {
  const { t } = useTranslation();

  return (
    <main>
      <BaseSectionHeader name={title}>
        <DateFilterBar years={years}>{filterExtras}</DateFilterBar>
      </BaseSectionHeader>

      <section className="mt-3 d-flex flex-column gap-3">
        {isLoading && <FetchingLoader message={t("Loading ledger...")} />}
        {error && (
          <ErrorLoader title={t("Error")} message={error.message || t("Failed to load the ledger")} />
        )}
        {!isLoading && !error && (
          <>
            <LedgerSummary totals={sumRows(rows)} showMining={showMining} onDetails={onOwnerDetails} />
            <LedgerCharts billboard={billboard} />
            <LedgerTable
              rows={rows}
              nameLabel={nameLabel}
              showMining={showMining}
              isFetching={isFetching}
              onDetails={onDetails}
            />
          </>
        )}
      </section>
      {children}
    </main>
  );
}

export default LedgerView;
