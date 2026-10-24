// Third Party
import { ExternalLink } from 'lucide-react';

import { renderTooltip } from '@/Utils/bootsTrap';

/**
 * Returns the URL for the image of a given ship type.
 * @param shipTypeId The ID of the ship type
 * @returns URL of the ship image
 */
export function shipImageUrl(shipTypeId: number, size: number = 512): string {
    return `https://images.evetech.net/types/${shipTypeId}/render?size=${size}`;
}

/**
 * Returns the URL for the image of a given character.
 * @param characterId The ID of the character
 * @param size The size of the portrait in pixels (defaults to 512)
 * @returns URL of the character image
 */
export function characterImageUrl(characterId: number, size: number = 512): string {
    return `https://images.evetech.net/characters/${characterId}/portrait?size=${size}`;
}

/**
 * Returns the URL for the image of a given corporation.
 * @param corporationId The ID of the corporation
 * @param size The size of the logo in pixels (defaults to 128)
 * @returns URL of the corporation logo
 */
export function corporationImageUrl(corporationId: number, size: number = 128): string {
    return `https://images.evetech.net/corporations/${corporationId}/logo?size=${size}`;
}

/**
 * Returns the URL for the image of a given alliance.
 * @param allianceId The ID of the alliance
 * @param size The size of the logo in pixels (defaults to 128)
 * @returns URL of the alliance logo
 */
export function allianceImageUrl(allianceId: number, size: number = 128): string {
    return `https://images.evetech.net/alliances/${allianceId}/logo?size=${size}`;
}

/**
 * Returns the URL for the image of a given item type.
 * @param typeId The ID of the item type
 * @param size The size of the icon in pixels (defaults to 32)
 * @returns URL of the item image
 */
export function itemImageUrl(typeId: number, size: number = 32): string {
    return `https://images.evetech.net/types/${typeId}/icon?size=${size}`;
}

/**
 * Returns the appropriate CSS classes for a given security status.
 * @param sec The security status of the solar system
 * @returns CSS classes for text color, background color, and border color
 */
export const getSecColor = (sec: number) => {
    if (sec >= 0.5) return 'aa-badge-hisec';
    if (sec > 0.0) return 'aa-badge-lowsec';
    return 'aa-badge-nullsec';
};

/**
 * Formats a Date object into EVE Online time string (HH:MM:SS EVE)
 * @param date The date to format (defaults to current date and time)
 * @returns Formatted EVE Online time string
 */
export const formatEveTime = (date: Date = new Date()): string => {
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}:${pad(date.getUTCSeconds())} EVE`;
};

/**
 * Generates a link to a specific killmail on zKillboard.
 * @param id The ID of the killmail
 * @param name The display name for the link
 * @returns A JSX element containing the link with a tooltip
 */
export function zKillboardLink({
    id,
    name,
    size = 12,
    className = "",
    externalLink = false
}: {id: number, name: string, size?: number, className?: string, externalLink?: boolean}) {
    const url = `https://zkillboard.com/kill/${id}/`;
    return renderTooltip(
        name,
        <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className={className}
        >
            {name}
            {externalLink && <ExternalLink size={size} />}
        </a>
    )
}

/**
 * Generates a finished Portrait for a character react component.
 * @param characterId The ID of the character
 * @param size The size of the image in pixels (defaults to 32)
 * @returns A React node containing the character portrait image
 */
export function renderCharacterPortrait(characterId: number, size: number = 32): React.ReactNode {
    return (
        <img src={characterImageUrl(characterId, size)} className="rounded"/>
    );
}
