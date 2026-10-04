// React
import { Fragment, useMemo, useState } from "react";

// Third Party
import { chordDirected, ribbonArrow } from "d3-chord";
import type { Chord, ChordGroup, ChordSubgroup, Chords } from "d3-chord";
import { schemeTableau10 } from "d3-scale-chromatic";
import { arc } from "d3-shape";

import type { BillboardData } from "@/Api/schema";
import { renderTooltip } from "@/Components/Tables/BaseTable/tableHelper";
import { useAnimationProgress, prefersReducedMotion } from "@/Hooks/useAnimationProgress";
import { buildChordMatrix } from "@/Utils/billboard";
import { formatIsk } from "@/Utils/ledger";

const SIZE = 560;
const LABEL_SPACE = 110;
const OUTER_RADIUS = SIZE / 2 - LABEL_SPACE;
const INNER_RADIUS = OUTER_RADIUS - 10;
const HOVER_POP = 6;
const DIMMED = 0.08;
const BULLET_RADIUS = 5;

type Active = { kind: "group"; index: number } | { kind: "ribbon"; key: string } | null;

const ribbonKey = (chord: Chord) => `${chord.source.index}-${chord.target.index}`;
const color = (index: number) => schemeTableau10[index % schemeTableau10.length];

// d3 measures angles clockwise from 12 o'clock.
const point = (angle: number, radius: number) =>
  [radius * Math.cos(angle - Math.PI / 2), radius * Math.sin(angle - Math.PI / 2)] as const;
const middle = (subgroup: ChordSubgroup) => (subgroup.startAngle + subgroup.endAngle) / 2;

/** Path a bullet follows from the source to the target of a flow, bending through the centre. */
function bulletPath(chord: Chord): string {
  const [sx, sy] = point(middle(chord.source), INNER_RADIUS - 2);
  const [tx, ty] = point(middle(chord.target), INNER_RADIUS - 2);
  return `M${sx},${sy} Q0,0 ${tx},${ty}`;
}

// Deterministic spread so that the bullets do not move in lockstep (2s to 3s per run).
const bulletDuration = (index: number) => 2 + ((index * 37) % 100) / 100;
const bulletOffset = (index: number) => ((index * 53) % 100) / 100;

interface ChordDiagramProps {
  names: string[];
  chords: Chords;
  title?: string;
}

/** Arcs grow, ribbons fade in, bullets flow along the links and hovering highlights the connected flows, like the former amCharts diagram. */
function ChordDiagram({ names, chords, title }: ChordDiagramProps) {
  const progress = useAnimationProgress();
  const [active, setActive] = useState<Active>(null);
  const animateBullets = !prefersReducedMotion();

  const ribbon = ribbonArrow<Chord, ChordSubgroup>().radius(INNER_RADIUS - 2);
  // Without a canvas context the generator returns the SVG path string.
  const ribbonPath = (chord: Chord) => String(ribbon(chord));

  const arcPath = (group: ChordGroup) =>
    arc<{ startAngle: number; endAngle: number }>()
      .innerRadius(INNER_RADIUS)
      .outerRadius(OUTER_RADIUS + (active?.kind === "group" && active.index === group.index ? HOVER_POP : 0))({
      startAngle: group.startAngle,
      // The arc sweeps out from its start angle while the diagram appears.
      endAngle: group.startAngle + (group.endAngle - group.startAngle) * progress,
    }) ?? undefined;

  const ribbonOpacity = (chord: Chord) => {
    if (active === null) return 0.7;
    if (active.kind === "ribbon") return active.key === ribbonKey(chord) ? 0.95 : DIMMED;
    return chord.source.index === active.index || chord.target.index === active.index
      ? 0.95
      : DIMMED;
  };

  const groupOpacity = (group: ChordGroup) => {
    if (active === null) return 1;
    if (active.kind === "group") {
      const connected = chords.some(
        (chord) =>
          (chord.source.index === active.index && chord.target.index === group.index) ||
          (chord.target.index === active.index && chord.source.index === group.index),
      );
      return group.index === active.index || connected ? 1 : DIMMED * 2;
    }
    const chord = chords.find((item) => ribbonKey(item) === active.key);
    return chord && (chord.source.index === group.index || chord.target.index === group.index)
      ? 1
      : DIMMED * 2;
  };

  return (
    <figure className="m-0">
      {title && <figcaption className="fw-bold text-center">{title}</figcaption>}
      <svg
        viewBox={`${-SIZE / 2} ${-SIZE / 2} ${SIZE} ${SIZE}`}
        role="img"
        aria-label={title}
        className="w-100"
        style={{ maxHeight: 460 }}
        onMouseLeave={() => setActive(null)}
      >
        <g>
          {chords.map((chord) => (
            <Fragment key={ribbonKey(chord)}>
              {renderTooltip(
                `${names[chord.source.index]} → ${names[chord.target.index]}: ${formatIsk(chord.source.value)}`,
                <path
                  d={ribbonPath(chord)}
                  fill={color(chord.source.index)}
                  fillOpacity={ribbonOpacity(chord) * progress}
                  style={{ transition: "fill-opacity 200ms ease", cursor: "pointer" }}
                  onMouseEnter={() => setActive({ kind: "ribbon", key: ribbonKey(chord) })}
                />,
              )}
            </Fragment>
          ))}
        </g>
        {animateBullets && (
          <g aria-hidden="true" pointerEvents="none">
            {chords.map((chord, index) => (
              <circle
                key={ribbonKey(chord)}
                data-testid="chord-bullet"
                r={BULLET_RADIUS}
                fill={color(chord.source.index)}
                opacity={Math.min(1, ribbonOpacity(chord) / 0.7) * progress}
              >
                <animateMotion
                  path={bulletPath(chord)}
                  dur={`${bulletDuration(index)}s`}
                  begin={`-${bulletOffset(index) * bulletDuration(index)}s`}
                  repeatCount="indefinite"
                />
              </circle>
            ))}
          </g>
        )}
        {chords.groups.map((group) => {
          const angle = (group.startAngle + group.endAngle) / 2;
          const flip = angle > Math.PI;
          return (
            <g
              key={group.index}
              opacity={groupOpacity(group)}
              style={{ transition: "opacity 200ms ease", cursor: "pointer" }}
              onMouseEnter={() => setActive({ kind: "group", index: group.index })}
            >
              {renderTooltip(
                `${names[group.index]}: ${formatIsk(group.value)}`,
                <path d={arcPath(group)} fill={color(group.index)} />,
              )}
              <text
                transform={`rotate(${(angle * 180) / Math.PI - 90}) translate(${OUTER_RADIUS + 8}) ${flip ? "rotate(180)" : ""}`}
                textAnchor={flip ? "end" : "start"}
                dominantBaseline="middle"
                fontSize={11}
                fill="currentColor"
                fillOpacity={progress}
              >
                {names[group.index]}
              </text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}

export interface ChordChartProps {
  billboard?: BillboardData | null;
  title?: string;
}

/** Flow from sources (e.g. characters) to ledger categories. */
function ChordChart({ billboard, title }: ChordChartProps) {
  const model = useMemo(() => {
    const { names, matrix } = buildChordMatrix(billboard);
    if (names.length === 0) return null;

    const chords = chordDirected().padAngle(0.04).sortSubgroups((a, b) => b - a)(matrix);
    const total = matrix.flat().reduce((sum, value) => sum + value, 0);
    return { names, chords, signature: `${names.join("|")}:${total}` };
  }, [billboard]);

  if (!model) return null;

  // A new signature remounts the diagram and plays the animation again.
  return (
    <ChordDiagram key={model.signature} names={model.names} chords={model.chords} title={title} />
  );
}

export default ChordChart;
