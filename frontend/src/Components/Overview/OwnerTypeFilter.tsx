// Third Party
import { Building2, Shield, User, Users } from "lucide-react";
import { Button, ButtonGroup } from "react-bootstrap";

export interface OwnerTypeFilterProps {
  ownerType: string;
  setOwnerType: (ownerType: string) => void;
  t: (key: string) => string;
}

export function OwnerTypeFilter({
  ownerType,
  setOwnerType,
  t,
}: OwnerTypeFilterProps) {
  const options = [
    { value: "all", label: t("All"), icon: <Users size={14} /> },
    { value: "character", label: t("Characters"), icon: <User size={14} /> },
    { value: "corporation", label: t("Corporations"), icon: <Building2 size={14} /> },
    { value: "alliance", label: t("Alliances"), icon: <Shield size={14} /> },
  ];

  return (
    <ButtonGroup size="sm" aria-label={t("Filter owners by type")} className="border border-black">
      {options.map((opt) => {
        const isActive = ownerType === opt.value;
        return (
          <Button
            key={opt.value}
            variant={isActive ? "primary" : "secondary"}
            className="d-inline-flex align-items-center gap-1"
            onClick={() => setOwnerType(opt.value)}
          >
            {opt.icon}
            <span>{opt.label}</span>
          </Button>
        );
      })}
    </ButtonGroup>
  );
}

export default OwnerTypeFilter;
