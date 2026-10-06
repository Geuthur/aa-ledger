// React
import { useMemo, useState } from "react";

// Third Party
import { useQuery } from "@tanstack/react-query";
import type { QueryKey } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { CircleHelp } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { CategorySchema, LedgerDetailsResponse, RefTypeAmountSchema } from "@/Api/schema";
import BaseModal, { ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { renderTooltip } from "@/Components/Base/BaseTable/tableHelper";
import ErrorLoader from "@/Components/Base/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Base/Loader/FetchingLoader";
import RefTypeBadges from "@/Components/Ledger/DetailsModal/RefTypeBadges";
import RefTypeCharactersModal from "@/Components/Ledger/DetailsModal/RefTypeCharactersModal";
import RefTypesModal from "@/Components/Ledger/DetailsModal/RefTypesModal";
import { amountClass, formatIsk } from "@/Utils/ledger";
import { filterCategories, filterRefTypes, formatRefType, sumRefTypes } from "@/Utils/refTypes";

type Period = "summary" | "daily" | "hourly";

const columnHelper = createColumnHelper<CategorySchema>();

const isMiningCategory = (category: CategorySchema) =>
    (category.ref_types ?? []).some((r) => r.ref_type === "mining") ||
    category.name.toLowerCase().includes("mining") ||
    category.name.toLowerCase().includes("bergbau");

export interface DetailsModalProps {
    /** Entity whose details are shown; `null` keeps the modal closed. */
    entityId: number | null;
    title: string;
    queryKey: QueryKey;
    queryFn: () => Promise<LedgerDetailsResponse>;
    onHide: () => void;
}

function DetailsModal({ entityId, title, queryKey, queryFn, onHide }: DetailsModalProps) {
    const { t } = useTranslation();
    const [period, setPeriod] = useState<Period>("summary");
    const [search, setSearch] = useState("");
    const [refTypesOf, setRefTypesOf] = useState<CategorySchema | null>(null);
    const [charactersOf, setCharactersOf] = useState<RefTypeAmountSchema | null>(null);

    const { data, isFetching, isError, error } = useQuery({
        queryKey,
        queryFn,
        enabled: entityId !== null,
    });

    const [cachedData, setCachedData] = useState(data);
    if (data && data !== cachedData) {
        setCachedData(data);
    }
    const effectiveData = data ?? cachedData;

    const columns = useMemo(
        () =>
            [
                columnHelper.accessor("name", {
                    header: t("Category"),
                    cell: ({ getValue, row }) => {
                        const name = getValue();
                        const isMining = isMiningCategory(row.original);
                        return (
                            <span
                                className={`d-inline-flex align-items-center gap-1 ${isMining ? "lg-text-mining" : ""
                                    }`}
                            >
                                {name}
                                {isMining &&
                                    renderTooltip(
                                        t("This is only an informational value and is not included in calculations."),
                                        <span
                                            className="d-inline-flex align-items-center"
                                            style={{ cursor: "help" }}
                                        >
                                            <CircleHelp size={14} className="text-info" />
                                        </span>,
                                    )}
                            </span>
                        );
                    },
                }),
                columnHelper.accessor("amount", {
                    header: t("Amount"),
                    meta: { align: "right" },
                    cell: ({ getValue, row }) => {
                        const isMining = isMiningCategory(row.original);
                        return (
                            <span className={`text-end d-block ${amountClass(getValue(), isMining)}`}>
                                {formatIsk(getValue())}
                            </span>
                        );
                    },
                }),
                columnHelper.accessor("average", {
                    header: t("Average"),
                    meta: { align: "right" },
                    cell: ({ getValue }) => (
                        <span className="text-end d-block">{formatIsk(getValue())}</span>
                    ),
                }),
                columnHelper.accessor("average_tick", {
                    header: t("Average per Tick"),
                    meta: { align: "right" },
                    cell: ({ getValue }) => (
                        <span className="text-end d-block">{formatIsk(getValue())}</span>
                    ),
                }),
                columnHelper.display({
                    id: "ref_types",
                    header: t("Reference Types"),
                    cell: ({ row }) => (
                        <RefTypeBadges
                            refTypes={filterRefTypes(row.original.ref_types ?? [], search)}
                            showAmounts={search.trim() !== ""}
                            onShowAll={() => setRefTypesOf(row.original)}
                            onSelectRefType={(refType) => setCharactersOf(refType)}
                        />
                    ),
                }),
            ] as ColumnDef<CategorySchema, unknown>[],
        [t, search],
    );

    const rows = useMemo(() => filterCategories(effectiveData?.[period] ?? [], search), [effectiveData, period, search]);
    const matches = useMemo(() => sumRefTypes(rows, search), [rows, search]);
    const matchTotal = matches.reduce((sum, item) => sum + item.amount, 0);

    const periods: { key: Period; label: string }[] = [
        { key: "summary", label: t("Summary") },
        { key: "daily", label: t("Daily") },
        { key: "hourly", label: t("Hourly") },
    ];

    return (
        <BaseModal
            title={title}
            show={entityId !== null}
            onHide={onHide}
            onExited={() => {
                setSearch("");
                setCachedData(undefined);
            }}
            size={ModalSize.extraLarge}
        >
                {isFetching && <FetchingLoader message={t("Loading...")} />}
                {isError && (
                    <ErrorLoader
                        title={t("Error")}
                        message={error instanceof Error ? error.message : t("Failed to load the details")}
                    />
                )}
                {!isFetching && !isError && effectiveData && (
                    <div className="aa-panel">
                        <div className="d-flex gap-2" role="group">
                            {periods.map(({ key, label }) => (
                                <button
                                    key={key}
                                    type="button"
                                    className={`aa-btn ${period === key ? "aa-btn-primary" : "aa-btn-secondary"}`}
                                    onClick={() => setPeriod(key)}
                                >
                                    {label}
                                </button>
                            ))}
                        </div>
                        <input
                            type="search"
                            className="lg-select lg-input w-100 my-3"
                            placeholder={t("Search reference type")}
                            aria-label={t("Search reference type")}
                            value={search}
                            onChange={(event) => setSearch(event.target.value)}
                        />
                        {search.trim() !== "" && (
                            <div className="aa-panel-light lg-chord-details mb-3" role="region" aria-label={t("Matching reference types")}>
                                {matches.length === 0 ? (
                                    <span className="text-muted">{t("No matching reference types")}</span>
                                ) : (
                                    <>
                                        <ul className="list-unstyled m-0">
                                            {matches.map((item) => {
                                                const isMining = item.ref_type === "mining";
                                                return (
                                                    <li
                                                        key={item.ref_type}
                                                        className={`lg-chord-flow ${isMining ? "lg-text-mining" : ""}`}
                                                    >
                                                        {(item.characters ?? []).length > 0 ? (
                                                            <button
                                                                type="button"
                                                                className="btn btn-link p-0 text-start text-decoration-none text-reset flex-grow-1"
                                                                onClick={() => setCharactersOf(item)}
                                                                title={t("View character breakdown for {{name}}", {
                                                                    name: formatRefType(item.ref_type),
                                                                })}
                                                            >
                                                                {formatRefType(item.ref_type)}
                                                            </button>
                                                        ) : (
                                                            <span className="flex-grow-1">{formatRefType(item.ref_type)}</span>
                                                        )}
                                                        <span className={amountClass(item.amount, isMining)}>
                                                            {formatIsk(item.amount)}
                                                        </span>
                                                    </li>
                                                );
                                            })}
                                        </ul>
                                        <div className="d-flex justify-content-between fw-bold border-top mt-2 pt-2">
                                            <span>{t("Total of the matches")}</span>
                                            <span className={amountClass(matchTotal)}>{formatIsk(matchTotal)}</span>
                                        </div>
                                    </>
                                )}
                            </div>
                        )}
                        <BaseTable
                            variant="vowra-light"
                            columns={columns}
                            data={rows}
                            emptyText={t("No data for the selected period")}
                            exportFileName="ledger-details.csv"
                            getRowClassName={(row) => (isMiningCategory(row.original) ? "lg-table-row-mining" : "")}
                        />
                        <div className="d-flex justify-content-end gap-2 fw-bold mt-2">
                            <span>{t("Total")}</span>
                            <span className={amountClass(effectiveData.total[period])}>
                                {formatIsk(effectiveData.total[period])}
                            </span>
                        </div>
                    </div>
                )}
                <RefTypesModal
                    category={refTypesOf}
                    initialSearch={search}
                    onHide={() => setRefTypesOf(null)}
                    onSelectRefType={(refType) => setCharactersOf(refType)}
                />
                <RefTypeCharactersModal
                    refType={charactersOf}
                    onHide={() => setCharactersOf(null)}
                />
        </BaseModal>
    );
}

export default DetailsModal;
