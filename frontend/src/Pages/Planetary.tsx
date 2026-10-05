// React
import { useMemo } from "react";
import { Link, useParams } from "react-router";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Bell, BellOff, Info } from "lucide-react";
import { parseAsInteger, useQueryStates } from "nuqs";
import { useTranslation } from "react-i18next";

import { fetchPlanets, togglePlanetNotification } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { PlanetaryDetails } from "@/Api/schema";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { BaseTable } from "@/Components/Base/BaseTable";
import { formatRelativeTime, renderTooltip } from "@/Components/Base/BaseTable/tableHelper";
import ErrorLoader from "@/Components/Base/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Base/Loader/FetchingLoader";
import ExtractorProgress from "@/Components/Planetary/ExtractorProgress";
import PlanetModal from "@/Components/Planetary/PlanetModal";

const columnHelper = createColumnHelper<PlanetaryDetails>();

function Planetary() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const characterId = Number(useParams().characterId);

  // The planet of the open modal; the owner is needed because alts are listed too.
  const [modal, setModal] = useQueryStates({
    planet: parseAsInteger,
    owner: parseAsInteger,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.Planets(characterId),
    queryFn: () => fetchPlanets(characterId),
  });

  const toggle = useMutation({
    mutationFn: ({ ownerId, planetId }: { ownerId: number; planetId?: number }) =>
      togglePlanetNotification(ownerId, planetId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.Planets(characterId) }),
  });

  const columns = useMemo(
    () =>
      [
        columnHelper.accessor((row) => row.owner.character_name, {
          id: "owner",
          header: t("Character"),
          cell: ({ row }) => (
            <span className="d-inline-flex align-items-center gap-2">
              {row.original.owner.icon && (
                <img
                  src={row.original.owner.icon}
                  alt=""
                  width={24}
                  height={24}
                  className="rounded-circle"
                />
              )}
              {row.original.owner.character_name}
            </span>
          ),
        }),
        columnHelper.accessor((row) => row.planet.name, {
          id: "planet",
          header: t("Planet"),
          cell: ({ row }) => (
            <span className="d-inline-flex align-items-center gap-2">
              {row.original.planet.type.icon && (
                <img src={row.original.planet.type.icon} alt="" width={24} height={24} />
              )}
              {row.original.planet.name}
            </span>
          ),
        }),
        columnHelper.accessor((row) => row.planet.upgrade_level, {
          id: "upgrade_level",
          header: t("Upgrade Level"),
        }),
        columnHelper.accessor((row) => row.planet.num_pins, {
          id: "num_pins",
          header: t("Pins"),
        }),
        columnHelper.accessor("expired", {
          header: t("Status"),
          cell: ({ getValue }) => (
            <span className={`badge ${getValue() ? "bg-danger" : "bg-success"}`}>
              {getValue() ? t("Inactive") : t("Active")}
            </span>
          ),
        }),
        columnHelper.accessor((row) => row.progress ?? -1, {
          id: "progress",
          header: t("Extractor Progress"),
          cell: ({ row }) =>
            row.original.progress === null || row.original.progress === undefined ? (
              <span className="text-muted">{t("No active extractors")}</span>
            ) : (
              <ExtractorProgress progress={row.original.progress} />
            ),
        }),
        columnHelper.accessor((row) => row.planet.last_update ?? "", {
          id: "last_update",
          header: t("Last Update"),
          cell: ({ getValue }) => (getValue() ? formatRelativeTime(getValue()) : "-"),
        }),
        columnHelper.display({
          id: "actions",
          header: "",
          cell: ({ row }) => (
            <span className="d-inline-flex gap-1">
              {renderTooltip(
                t("View Planet"),
                <button
                  type="button"
                  className="lg-btn lg-btn-primary lg-btn-sm"
                  aria-label={t("View Planet")}
                  onClick={() =>
                    setModal({ planet: row.original.id, owner: row.original.owner.character_id })
                  }
                >
                  <Info size={14} />
                </button>,
              )}
              {renderTooltip(
                t("Toggle Notification"),
                <button
                  type="button"
                  className={`lg-btn lg-btn-sm ${row.original.alarm ? "lg-btn-success" : "lg-btn-secondary"}`}
                  aria-label={t("Toggle Notification")}
                  disabled={toggle.isPending}
                  onClick={() =>
                    toggle.mutate({
                      ownerId: row.original.owner.character_id,
                      planetId: row.original.id,
                    })
                  }
                >
                  {row.original.alarm ? <Bell size={14} /> : <BellOff size={14} />}
                </button>,
              )}
            </span>
          ),
        }),
      ] as ColumnDef<PlanetaryDetails, unknown>[],
    [t, setModal, toggle],
  );

  return (
    <main>
      <BaseSectionHeader name={t("Planetary Ledger")}>
        <button
          type="button"
          className="lg-btn lg-btn-secondary"
          disabled={toggle.isPending}
          onClick={() => toggle.mutate({ ownerId: characterId })}
        >
          {t("Toggle all notifications")}
        </button>
        <Link className="lg-btn lg-btn-secondary" to="/ledger/planetary/overview/">
          {t("Overview")}
        </Link>
      </BaseSectionHeader>

      <section className="mt-3">
        {isLoading && <FetchingLoader message={t("Loading planets...")} />}
        {error && <ErrorLoader title={t("Error")} message={error.message} />}
        {!isLoading && !error && (
          <BaseTable
            columns={columns}
            data={data ?? []}
            emptyText={t("No planets found")}
            exportFileName="planets.csv"
          />
        )}
      </section>

      <PlanetModal
        ownerId={modal.owner}
        planetId={modal.planet}
        onHide={() => setModal({ planet: null, owner: null })}
      />
    </main>
  );
}

export default Planetary;
