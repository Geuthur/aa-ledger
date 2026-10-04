// React
import { useParams } from "react-router";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { deleteCorporation, fetchCorporationAdministration } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import AdministrationView from "@/Components/Administration/AdministrationView";

function CorporationAdministration() {
  const { t } = useTranslation();
  const corporationId = Number(useParams().corporationId);
  const queryKey = queryKeys.CorporationAdministration(corporationId);

  const { data, isLoading, error } = useQuery({
    queryKey,
    queryFn: () => fetchCorporationAdministration(corporationId),
  });

  return (
    <AdministrationView
      title={t("Corporation Administration")}
      entryLabel={t("Corporation")}
      data={data}
      isLoading={isLoading}
      error={error}
      queryKey={queryKey}
      ledgerPath={(ownerId) => `/ledger/corporation/${ownerId}/`}
      onDelete={deleteCorporation}
    />
  );
}

export default CorporationAdministration;
