// Third Party
import { FilterButtonGroup } from "aa-geuthur-react";
import { Building2, Shield, User, Users } from "lucide-react";

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
    <FilterButtonGroup
      options={options}
      value={ownerType}
      onChange={setOwnerType}
      ariaLabel={t("Filter owners by type")}
    />
  );
}

export default OwnerTypeFilter;
