/**
 * render a Link with given URL and text optional children
 * @param url The URL to link to
 * @param text The text to display for the link
 * @param children Optional React children to include inside the link
 * @param external Whether the link should open in a new tab (external link)
 * @returns A JSX element representing the link
 */
export const renderLink = ({
        url,
        text,
        children,
        external,
        className
    }: {url: string, text: string, children?: React.ReactNode, external?: boolean, className?: string}) => {
    return (
        <a href={url} className={`${className ?? ''}`} target={external ? '_blank' : undefined} rel={external ? 'noopener noreferrer' : undefined}>
            {text}
            {children}
        </a>
    );
};

/**
 * render a ship image with a fallback to the icon if the render image fails
 * @param shipId The ID of the ship
 * @param shipName The name of the ship
 * @returns A JSX element representing the ship image
 */
export const renderShipImage = (shipId: number, shipName: string, className?: string) => {
    return (
        <img
            src={`https://images.evetech.net/types/${shipId}/render?size=128`}
            alt={shipName}
            className={`${className ?? ''}`}
            loading="lazy"
            onError={(e) => {
                (e.target as HTMLImageElement).src = `https://images.evetech.net/types/${shipId}/icon?size=64`;
            }}
        />
    );
};
