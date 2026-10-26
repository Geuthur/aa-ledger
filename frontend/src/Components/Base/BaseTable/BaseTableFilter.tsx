// React
import { useState, type MouseEventHandler } from "react";

// Third Party
import type { Column, Table as ReactTable } from "@tanstack/react-table";
import { ChevronDown, Search, SlidersHorizontal, X } from "lucide-react";
import { Button, Dropdown, Form, OverlayTrigger, Popover } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import Styles from "@/Styles/modules/BaseTableFilter.module.css";

// Lets a column supply a nicer label for its own SelectFilter options than
// the raw underlying value (e.g. the wallet table's ref_type column, whose
// raw values are ESI machine keys like "bounty_prizes" - see RefTypeLabel).
// Falls back to SelectFilter's own value.replaceAll("_", " ") when unset, so
// every other column's filter is unaffected.
declare module "@tanstack/react-table" {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- must match the original interface's arity, not just what this augmentation itself uses
  interface ColumnMeta<TData, TValue> {
    filterOptionLabel?: (value: string) => string;
    align?: "left" | "right" | "center";
  }
}

const searchWrapperClass = "position-relative w-100";
const searchIconClass = "position-absolute top-50 end-0 translate-middle-y me-2 pe-none text-muted";

/** Small "x" button inside a filter field that clears the current value. */
const ClearButton = ({ onClick }: { onClick: MouseEventHandler<HTMLButtonElement> }) => {
  const { t } = useTranslation();
  return (
    <button
      type="button"
      className={`${Styles.clearbutton} position-absolute top-50 end-0 translate-middle-y me-1 d-flex align-items-center justify-content-center border-0 bg-transparent p-0`}
      onClick={onClick}
      title={t("Clear")}
    >
      <X size={12} />
    </button>
  );
};

const isHTML = RegExp.prototype.test.bind(/(<([^>]+)>)/i);

export const NumberFilter = <TData,>({ column }: { column: Column<TData, unknown> }) => {
  const { t } = useTranslation();
  const columnFilterValue = column.getFilterValue();
  const fromToNumber = columnFilterValue as [string, string];
  const hasValue =
    (typeof fromToNumber?.[0] !== "undefined" && fromToNumber?.[0] !== "") ||
    (typeof fromToNumber?.[1] !== "undefined" && fromToNumber?.[1] !== "");

  const popoverNumber = (
    <Popover id="popover-number-range" className={Styles.popover}>
      <Popover.Body className="p-3">
        <div className="d-flex flex-column gap-2">
          <div>
            <Form.Label className="small text-muted mb-1">{t("Min")}</Form.Label>
            <Form.Control
              size="sm"
              type="number"
              value={fromToNumber?.[0] ?? ""}
              onChange={(e) =>
                column.setFilterValue((old: [number, number]) => [e.target.value, old?.[1]])
              }
              placeholder={t("Min")}
              className={Styles.searchinput}
            />
          </div>
          <div>
            <Form.Label className="small text-muted mb-1">{t("Max")}</Form.Label>
            <Form.Control
              size="sm"
              type="number"
              value={fromToNumber?.[1] ?? ""}
              onChange={(e) =>
                column.setFilterValue((old: [number, number]) => [old?.[0], e.target.value])
              }
              placeholder={t("Max")}
              className={Styles.searchinput}
            />
          </div>
          <div className="d-flex gap-2 mt-2">
            <Button
              variant="outline-secondary"
              size="sm"
              className="w-50"
              onClick={() => {
                column.setFilterValue(() => [undefined, undefined]);
                document.body.click();
              }}
            >
              {t("Reset")}
            </Button>
            <Button
              variant="primary"
              size="sm"
              className="w-50"
              onClick={() => document.body.click()}
            >
              {t("Done")}
            </Button>
          </div>
        </div>
      </Popover.Body>
    </Popover>
  );

  return (
    <OverlayTrigger trigger="click" placement="bottom" rootClose={true} overlay={popoverNumber}>
      <div className={searchWrapperClass}>
        <Form.Control
          size="sm"
          className={Styles.searchinput}
          readOnly={true}
          type="text"
          placeholder={t("Range…")}
          value={
            hasValue
              ? `${fromToNumber?.[0] || "Min"} → ${fromToNumber?.[1] || "Max"}`
              : ""
          }
        />
        {hasValue ? (
          <ClearButton onClick={(e) => {
              e.stopPropagation();
              column.setFilterValue(() => [undefined, undefined]);
            }} />
        ) : (
          <SlidersHorizontal size={12} className={searchIconClass} />
        )}
      </div>
    </OverlayTrigger>
  );
};

export const BoolFilter = <TData,>({ column }: { column: Column<TData, unknown> }) => {
  const { t } = useTranslation();
  const passFail = column.getFilterValue();
  const hasValue = typeof passFail !== "undefined";

  return (
    <OverlayTrigger
      trigger="click"
      placement="bottom-start"
      rootClose={true}
      overlay={
        <Dropdown show drop="down-centered">
          <Dropdown.Menu className={`overflow-y-auto ${Styles.dropdown}`}>
            <Dropdown.Item
              onClick={() => {
                column.setFilterValue(true);
                document.body.click();
              }}
            >
              {t("True")}
            </Dropdown.Item>
            <Dropdown.Item
              onClick={() => {
                column.setFilterValue(false);
                document.body.click();
              }}
            >
              {t("False")}
            </Dropdown.Item>
            <Dropdown.Divider />
            <Dropdown.Item
              onClick={() => {
                column.setFilterValue(undefined);
                document.body.click();
              }}
            >
              {t("All")}
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
      }
    >
      <div className={searchWrapperClass}>
        <Form.Control
          size="sm"
          className={Styles.searchinput}
          readOnly={true}
          type="text"
          placeholder={t("All")}
          value={hasValue ? (passFail ? t("True") : t("False")) : ""}
        />
        {hasValue ? (
          <ClearButton onClick={(e) => {
              e.stopPropagation();
              column.setFilterValue(() => undefined);
            }} />
        ) : (
          <ChevronDown size={12} className={searchIconClass} />
        )}
      </div>
    </OverlayTrigger>
  );
};

export const TextFilter = <TData,>({ column }: { column: Column<TData, unknown> }) => {
  const { t } = useTranslation();
  const value = (column.getFilterValue() as string) ?? "";
  return (
    <div className={searchWrapperClass}>
      <Form.Control
        size="sm"
        className={Styles.searchinput}
        type="text"
        placeholder={t("Filter…")}
        value={value}
        onChange={(event) => {
          column.setFilterValue(event.target.value ? event.target.value : "");
        }}
      />
      {value ? (
        <ClearButton onClick={() => column.setFilterValue("")} />
      ) : (
        <Search size={12} className={searchIconClass} />
      )}
    </div>
  );
};

export const SelectFilter = <TData,>({ column }: { column: Column<TData, unknown> }) => {
  const { t } = useTranslation();
  const [isEditing, setIsEditing] = useState(false);
  const sortedUniqueValues = Array.from(column.getFacetedUniqueValues().keys())
    .filter((v) => v !== null && v !== undefined)
    .sort();
  const currentFilterValue = column.getFilterValue() as string;
  const isObjectorHTML =
    isHTML(sortedUniqueValues?.[0]) || typeof sortedUniqueValues?.[0] === "object";

  const labelFor =
    column.columnDef.meta?.filterOptionLabel ?? ((v: string) => v?.replaceAll("_", " ") ?? v);

  const selectOptions = (sortedUniqueValues as string[]).reduce(
    (previousValue: { value: string; label: string }[], currentValue) => {
      if (currentValue !== undefined && currentValue !== null) {
        if (!isObjectorHTML) {
          if (
            currentFilterValue === undefined ||
            currentValue?.toLowerCase().includes(currentFilterValue?.toLowerCase())
          ) {
            previousValue.push({ value: currentValue, label: labelFor(currentValue) });
          }
        }
      }
      return previousValue;
    },
    [],
  );

  return (
    <OverlayTrigger
      trigger="click"
      placement="bottom-start"
      rootClose={true}
      overlay={
        <Dropdown show drop="down-centered">
          <Dropdown.Menu className={`overflow-y-auto ${Styles.dropdown}`}>
            {selectOptions.length > 0 ? (
              selectOptions.map((item) => (
                <Dropdown.Item
                  key={item.value}
                  className="text-capitalize"
                  onClick={() => {
                    column.setFilterValue(item.value ? item.value : "");
                    document.body.click();
                  }}
                >
                  {item.label}
                </Dropdown.Item>
              ))
            ) : (
              <Dropdown.Item disabled>{t("No matching options")}</Dropdown.Item>
            )}
          </Dropdown.Menu>
        </Dropdown>
      }
    >
      <div className={searchWrapperClass}>
        <Form.Control
          size="sm"
          className={Styles.searchinput}
          type="text"
          placeholder={t("Filter…")}
          value={
            typeof currentFilterValue === "undefined"
              ? ""
              : isEditing
                ? currentFilterValue
                : labelFor(currentFilterValue)
          }
          onFocus={(event) => {
            setIsEditing(true);
            event.target.select();
          }}
          onBlur={() => setIsEditing(false)}
          onChange={(event) => {
            column.setFilterValue(event.target.value ? event.target.value : "");
          }}
        />
        {currentFilterValue ? (
          <ClearButton onClick={(event) => {
              event.stopPropagation();
              setIsEditing(false);
              column.setFilterValue(() => undefined);
            }} />
        ) : (
          <ChevronDown size={12} className={searchIconClass} />
        )}
      </div>
    </OverlayTrigger>
  );
};

export const Filter = <TData,>({
  column,
  table,
}: {
  column: Column<TData, unknown>;
  table: ReactTable<TData>;
}) => {
  const firstValue: unknown = table.getPreFilteredRowModel().flatRows[0]?.getValue(column.id);
  if (typeof firstValue === "number") {
    return <NumberFilter {...{ column }} />;
  } else if (typeof firstValue === "boolean") {
    return <BoolFilter {...{ column }} />;
  } else if (typeof firstValue === "object") {
    return <TextFilter {...{ column }} />;
  } else {
    return <SelectFilter {...{ column }} />;
  }
};

export default Filter;
