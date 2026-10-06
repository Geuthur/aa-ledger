// React
import ReactDOM from "react-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";

import { loadMenu } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import AuthLeftMenu from "@/Menu/AuthLeftMenu";

export const AuthLeftMenuAsync = () => {
  const menuRoot =
    typeof document !== "undefined" ? document.getElementById("nav-left") : null;

  const { data: menuData, isLoading, isError } = useQuery({
    queryKey: queryKeys.Menu,
    queryFn: () => loadMenu(),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  if (!menuRoot || !menuData?.left_links) {
    return <></>;
  }

  if (!menuRoot || !menuData?.left_links) {
    return <></>;
  }

  return ReactDOM.createPortal(
    <AuthLeftMenu
      error={isError}
      isLoading={isLoading}
      data={menuData.left_links}
    />,
    menuRoot,
  );
};

export default AuthLeftMenuAsync;
