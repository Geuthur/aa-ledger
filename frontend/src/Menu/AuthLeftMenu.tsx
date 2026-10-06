import { ProjectName } from "@/App";
import { MenuItem } from "@/Menu/BaseMenu";
import type { MenuLinkItem, MenuProps } from "@/Menu/BaseMenu";

const AuthLeftMenu = ({ data }: MenuProps) => {
  const toPath = (link: string) => {
    const cleanLink = link.replace(/^\/+|\/+$/g, "");
    return cleanLink ? `/${ProjectName}/${cleanLink}/` : `/${ProjectName}/`;
  };

  const menuItems = Array.isArray(data)
    ? data.filter((item): item is MenuLinkItem => !!item.link)
    : [];

  return (
    <>
      {menuItems.map((item) => {
        return <MenuItem key={item.link} link={item} {...{ toPath }} />;
      })}
    </>
  );
};

export default AuthLeftMenu;
