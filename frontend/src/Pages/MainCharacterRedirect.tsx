// React
import { Navigate } from "react-router";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { loadUserData } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import ErrorLoader from "@/Components/Loader/ErrorLoader";
import FetchingLoader from "@/Components/Loader/FetchingLoader";

export interface MainCharacterRedirectProps {
  /** Route of the main character, e.g. `character` for `/ledger/character/{id}/`. */
  to: "character" | "planetary";
}

/** Sends the user to the page of their main character. */
function MainCharacterRedirect({ to }: MainCharacterRedirectProps) {
  const { t } = useTranslation();
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.User,
    queryFn: loadUserData,
    staleTime: 5 * 60 * 1000,
  });

  if (isLoading) return <FetchingLoader message={t("Loading...")} />;
  if (error || !data || !data.user.character_id) {
    return (
      <ErrorLoader
        title={t("Error")}
        message={error?.message ?? t("No main character found.")}
      />
    );
  }
  return <Navigate to={`/ledger/${to}/${data.user.character_id}/`} replace />;
}

export default MainCharacterRedirect;
