// React
import ReactDOM from "react-dom";

import AuthRightMenu from "@/Menu/AuthRightMenu";
import { useMenu } from "@/Menu/Hooks";

const AuthRightMenuAsync = () => {
  const menuRoot = typeof document !== "undefined" ? document.getElementById("nav-right") : null;
  const { isLoading, error, data } = useMenu();

  if (!menuRoot || !data?.right_links) {
    return <></>;
  }

  return ReactDOM.createPortal(
    <AuthRightMenu error={error ? true : false} isLoading={isLoading} data={data.right_links} />,
    menuRoot,
  );
};

export default AuthRightMenuAsync;
