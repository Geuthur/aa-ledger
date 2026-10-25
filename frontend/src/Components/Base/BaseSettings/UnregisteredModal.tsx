// React
import { useMemo, useState } from "react";

// Third Party
import { Search } from "lucide-react";
import { Form, InputGroup } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Components/Base/BaseSettings/Settings.module.css";

// AA Base
import { BaseModal } from "@/Components/Base/BaseModal";
import type { BaseMissingOwner } from "@/Components/Base/BaseSettings/types";
import { OwnerPortrait } from "@/Components/Base/OwnerPortrait";

export interface UnregisteredModalProps {
  show: boolean;
  onHide: () => void;
  title: string;
  description?: string;
  items?: BaseMissingOwner[];
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
  emptyMessage?: string;
}

/** Modal listing entities (members or corporations) that are not registered in the app. */
export function UnregisteredModal({
  show,
  onHide,
  title,
  description,
  items = [],
  isLoading = false,
  isError = false,
  errorMessage,
  emptyMessage,
}: UnregisteredModalProps) {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (i) => i.name.toLowerCase().includes(q) || (i.subtitle ?? "").toLowerCase().includes(q),
    );
  }, [items, search]);

  return (
    <BaseModal
      show={show}
      onHide={onHide}
      onExited={() => setSearch("")}
      size="lg"
      centered
      scrollable
      title={title}
    >
      {description && <p className="small text-muted">{description}</p>}

      {isLoading && (
        <div className="aa-loader-container">
          <span className="spinner-border" />
          <span>{t("Loading…")}</span>
        </div>
      )}

      {isError && (
        <div className={styles["error-banner"]} role="alert">
          {errorMessage ?? t("Failed to load data.")}
        </div>
      )}

      {!isLoading && !isError && items.length === 0 && (
        <div className={styles["empty-state"]}>{emptyMessage ?? t("Nothing to show.")}</div>
      )}

      {!isLoading && !isError && items.length > 0 && (
        <>
          <InputGroup size="sm" className="mb-3">
            <InputGroup.Text>
              <Search size={14} aria-hidden="true" />
            </InputGroup.Text>
            <Form.Control
              type="search"
              value={search}
              placeholder={t("Search owners…")}
              aria-label={t("Search owners")}
              onChange={(e) => setSearch(e.target.value)}
            />
          </InputGroup>

          <p className="small text-muted mb-2">
            {t("{{count}} unregistered", { count: filtered.length })}
          </p>

          {filtered.length === 0 ? (
            <div className={styles["empty-state"]}>{t("No matching owners found.")}</div>
          ) : (
            <ul className="list-unstyled d-flex flex-column gap-2 mb-0">
              {filtered.map((item) => (
                <li
                  key={`${item.owner_type ?? "character"}-${item.id}`}
                  className="d-flex align-items-center gap-3"
                >
                  {item.avatar_url && (
                    <OwnerPortrait
                      src={item.avatar_url}
                      alt={item.name}
                      type={item.owner_type}
                      size="sm"
                      shape={item.owner_type === "corporation" ? "rounded" : "circle"}
                      bordered
                    />
                  )}
                  <div className="min-w-0">
                    <div className="fw-semibold">{item.name}</div>
                    {item.subtitle && <div className="small text-muted">{item.subtitle}</div>}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </BaseModal>
  );
}
