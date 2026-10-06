// React
import ReactDOM from "react-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";

import { loadMenu } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import AuthRightMenu from "@/Menu/AuthRightMenu";

const AuthRightMenuAsync = () => {
  const menuRoot = typeof document !== "undefined" ? document.getElementById("nav-right") : null;
  const { isLoading, error, data } = useQuery({
    queryKey: queryKeys.Menu,
    queryFn: () => loadMenu(),
    refetchOnWindowFocus: false,
  });

  if (!menuRoot || !data?.right_links) {
    return <></>;
  }

  return ReactDOM.createPortal(
    <AuthRightMenu error={error ? true : false} isLoading={isLoading} data={data.right_links} />,
    menuRoot,
  );
};

export default AuthRightMenuAsync;
