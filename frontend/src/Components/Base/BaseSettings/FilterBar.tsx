// Third Party
import { Search } from "lucide-react";
import { Button, ButtonGroup, Form, InputGroup } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// Styles
import styles from "@/Components/Base/BaseSettings/Settings.module.css";

export type OwnerTypeFilter = "all" | "character" | "corporation" | "alliance";

export interface OwnerFilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  typeFilter: OwnerTypeFilter;
  onTypeChange: (value: OwnerTypeFilter) => void;
  counts: Record<OwnerTypeFilter, number>;
  searchPlaceholder?: string;
}

/**
 * Type filter (All / Character / Corporation / Alliance) and name search for owner lists.
 * Only types that actually exist (count > 0) are shown, "All" is always visible.
 */
export function OwnerFilterBar({
  search,
  onSearchChange,
  typeFilter,
  onTypeChange,
  counts,
  searchPlaceholder,
}: OwnerFilterBarProps) {
  const { t } = useTranslation();

  const options: { value: OwnerTypeFilter; label: string }[] = [
    { value: "all", label: t("All") },
    { value: "character", label: t("Characters") },
    { value: "corporation", label: t("Corporations") },
    { value: "alliance", label: t("Alliances") },
  ];

  const visibleOptions = options.filter(
    (o) => o.value === "all" || counts[o.value] > 0 || o.value === typeFilter,
  );

  return (
    <div className={styles["filter-bar"]}>
      <ButtonGroup className="border border-black" aria-label={t("Filter by owner type")}>
        {visibleOptions.map((o) => (
          <Button
            key={o.value}
            size="sm"
            variant={typeFilter === o.value ? "primary" : "secondary"}
            aria-pressed={typeFilter === o.value}
            onClick={() => onTypeChange(o.value)}
          >
            {o.label} ({counts[o.value]})
          </Button>
        ))}
      </ButtonGroup>

      <InputGroup size="sm" className={styles["filter-search"]}>
        <InputGroup.Text>
          <Search size={14} aria-hidden="true" />
        </InputGroup.Text>
        <Form.Control
          type="search"
          value={search}
          placeholder={searchPlaceholder ?? t("Search owners…")}
          aria-label={t("Search owners")}
          onChange={(e) => onSearchChange(e.target.value)}
        />
      </InputGroup>
    </div>
  );
}
