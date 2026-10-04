// React
import { useMemo } from "react";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import { Modal } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { fetchPlanetDetails } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import ErrorLoader from "@/Components/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Loader/FetchingLoader";
import ExtractorProgress from "@/Components/Planetary/ExtractorProgress";
import { BaseTable } from "@/Components/Tables/BaseTable";
import { formatDate, formatNumber } from "@/Components/Tables/BaseTable/tableHelper";

type Product = components["schemas"]["ProductSchema"];
type Extractor = components["schemas"]["ExtractorSchema"];
type Factory = components["schemas"]["ProduceSchema"];
type Storage = components["schemas"]["StorageSchema"];

const extractorColumn = createColumnHelper<Extractor>();
const factoryColumn = createColumnHelper<Factory>();
const storageColumn = createColumnHelper<Storage>();

const ProductLabel = ({ product }: { product: Pick<Product, "item_name" | "icon"> }) => (
  <span className="d-inline-flex align-items-center gap-2">
    {product.icon && <img src={product.icon} alt="" width={24} height={24} />}
    {product.item_name}
  </span>
);

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <section className="aa-panel d-flex flex-column gap-2">
    <h5 className="aa-section-title mb-0">{title}</h5>
    {children}
  </section>
);

export interface PlanetModalProps {
  ownerId: number | null;
  planetId: number | null;
  onHide: () => void;
}

function PlanetModal({ ownerId, planetId, onHide }: PlanetModalProps) {
  const { t } = useTranslation();
  const open = ownerId !== null && planetId !== null;

  const { data, isFetching, error } = useQuery({
    queryKey: queryKeys.PlanetDetails(ownerId ?? 0, planetId ?? 0),
    queryFn: () => fetchPlanetDetails(ownerId ?? 0, planetId ?? 0),
    enabled: open,
  });

  const extractorColumns = useMemo(
    () =>
      [
        extractorColumn.accessor("item_name", {
          header: t("Product"),
          cell: ({ row }) => <ProductLabel product={row.original} />,
        }),
        extractorColumn.accessor("install_time", {
          header: t("Install Time"),
          cell: ({ getValue }) => formatDate(getValue()),
        }),
        extractorColumn.accessor("expiry_time", {
          header: t("Expiry Time"),
          cell: ({ getValue }) => formatDate(getValue()),
        }),
        extractorColumn.accessor("progress", {
          header: t("Progress"),
          cell: ({ getValue }) => <ExtractorProgress progress={getValue()} />,
        }),
      ] as ColumnDef<Extractor, unknown>[],
    [t],
  );

  const factoryColumns = useMemo(
    () =>
      [
        factoryColumn.accessor("factory_name", { header: t("Facility") }),
        factoryColumn.display({
          id: "input",
          header: t("Input"),
          cell: ({ row }) => (
            <span className="d-flex flex-wrap gap-3">
              {row.original.input_products.map((product) => (
                <ProductLabel key={product.item_id} product={product} />
              ))}
            </span>
          ),
        }),
        factoryColumn.display({
          id: "output",
          header: t("Output"),
          cell: ({ row }) =>
            row.original.output_product ? <ProductLabel product={row.original.output_product} /> : "-",
        }),
        factoryColumn.accessor("is_active", {
          header: t("Active"),
          cell: ({ getValue }) => (
            <span className={`badge ${getValue() ? "bg-success" : "bg-danger"}`}>
              {getValue() ? t("Active") : t("Inactive")}
            </span>
          ),
        }),
      ] as ColumnDef<Factory, unknown>[],
    [t],
  );

  const storageColumns = useMemo(
    () =>
      [
        storageColumn.accessor((row) => row.product.item_name, {
          id: "product",
          header: t("Product"),
          cell: ({ row }) => <ProductLabel product={row.original.product} />,
        }),
        storageColumn.accessor("factory_name", { header: t("Facility") }),
        storageColumn.accessor((row) => row.product.item_quantity ?? 0, {
          id: "amount",
          header: t("Amount"),
          meta: { align: "right" },
          cell: ({ getValue }) => (
            <span className="text-end d-block">{formatNumber(getValue())}</span>
          ),
        }),
      ] as ColumnDef<Storage, unknown>[],
    [t],
  );

  return (
    <Modal show={open} onHide={onHide} size="xl" centered restoreFocus={false}>
      <Modal.Header closeButton>
        <Modal.Title className="d-flex align-items-center gap-2">
          {data?.planet.type.icon && (
            <img src={data.planet.type.icon} alt="" width={32} height={32} />
          )}
          {data ? data.planet.name : t("Planet")}
          {data && <small className="text-muted">{data.owner.character_name}</small>}
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {isFetching && <FetchingLoader message={t("Loading...")} />}
        {error && <ErrorLoader title={t("Error")} message={error.message} />}
        {!isFetching && !error && data && (
          <div className="d-flex flex-column gap-3">
            <Section title={t("Extractors")}>
              <BaseTable
                columns={extractorColumns}
                data={data.extractors}
                emptyText={t("No active extractors")}
                pageSizeOptions={[10, 25]}
              />
            </Section>
            <Section title={t("Factories")}>
              <BaseTable
                columns={factoryColumns}
                data={data.factories}
                emptyText={t("No factories")}
                pageSizeOptions={[10, 25]}
              />
            </Section>
            <Section title={t("Storage")}>
              <BaseTable
                columns={storageColumns}
                data={data.storage}
                emptyText={t("Nothing stored")}
                pageSizeOptions={[10, 25]}
              />
            </Section>
            <span className="text-muted small">
              {t(
                "Note: Planetary information is only recalculated when the colony is viewed through the client. Information will not update until this criteria is met.",
              )}
            </span>
          </div>
        )}
      </Modal.Body>
      <Modal.Footer>
        <button type="button" className="lg-btn lg-btn-secondary" onClick={onHide}>
          {t("Close")}
        </button>
      </Modal.Footer>
    </Modal>
  );
}

export default PlanetModal;
