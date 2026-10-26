// React
import type React from "react";

// Third Party
import { Badge, Button, ButtonGroup } from "react-bootstrap";

export interface FilterOption<T extends string = string> {
  value: T;
  label: string;
  /** Optional icon shown before the label. */
  icon?: React.ReactNode;
  /** Optional counter shown as a badge after the label. */
  count?: number;
}

export interface FilterButtonGroupProps<T extends string = string> {
  options: FilterOption<T>[];
  value: T;
  onChange: (value: T) => void;
  ariaLabel: string;
}

/** Button group to pick one filter value, with optional icons and counters. */
export function FilterButtonGroup<T extends string = string>({
  options,
  value,
  onChange,
  ariaLabel,
}: FilterButtonGroupProps<T>) {
  return (
    <div className="mw-100 overflow-x-auto">
      <ButtonGroup size="sm" aria-label={ariaLabel} className="border border-black">
        {options.map((option) => {
          const isActive = value === option.value;
          return (
            <Button
              key={option.value}
              variant={isActive ? "primary" : "secondary"}
              aria-pressed={isActive}
              className="d-inline-flex align-items-center gap-1"
              onClick={() => onChange(option.value)}
            >
              {option.icon}
              {option.label}
              {option.count !== undefined && (
                <>
                  {" "}
                  <Badge bg="secondary" className="ms-1">
                    {option.count}
                  </Badge>
                </>
              )}
            </Button>
          );
        })}
      </ButtonGroup>
    </div>
  );
}

export default FilterButtonGroup;
