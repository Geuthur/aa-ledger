// React
import { Link, useLocation } from "react-router";

// Third Party
import { Nav } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import type { components } from "@/Api/OpenApi";

export type MenuLinkItem = components["schemas"]["MenuLink"];

export interface MenuCategory {
  name: string;
  link?: string;
  links?: MenuLinkItem[];
}

export interface MenuProps {
  isLoading: boolean;
  data: Array<MenuCategory | MenuLinkItem>;
  error: boolean;
}

export interface ToPath {
    toPath: (link: string) => string;
}

export const MenuItem = ({ link, toPath }: { link: MenuLinkItem } & ToPath) => {
    const { t } = useTranslation();
    const path = useLocation();
    const isExternal = Boolean(
        link.is_external ||
        link.link?.startsWith("http://") ||
        link.link?.startsWith("https://")
    );

    if (isExternal) {
        return (
            <Nav.Item as="li">
                <Nav.Link
                    href={link.link ?? "#"}
                    id={link.name}
                    key={link.name}
                >
                    {t(link.name)}
                </Nav.Link>
            </Nav.Item>
        );
    }

    const target = toPath(link.link ?? "");
    const root = toPath("");
    // The root link redirects to the character ledger, so both highlight it.
    const hit = target === root
        ? path.pathname === root || path.pathname.startsWith(`${root}character/`)
        : path.pathname.startsWith(target);

    return (
        <Nav.Item as="li">
            <Nav.Link
                as={Link}
                to={{ pathname: target }}
                id={link.name}
                key={link.name}
                active={hit}
            >
                {t(link.name)}
                {link.badge ? <span className="badge bg-warning ms-1">{link.badge}</span> : null}
            </Nav.Link>
        </Nav.Item>
    );
};
