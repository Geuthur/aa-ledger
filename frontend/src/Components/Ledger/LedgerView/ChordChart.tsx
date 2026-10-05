// React
import { Fragment, useMemo, useState } from "react";

// Third Party
import { chordDirected, ribbonArrow } from "d3-chord";
import type { Chord, ChordGroup, ChordSubgroup, Chords } from "d3-chord";
import { schemeTableau10 } from "d3-scale-chromatic";
import { arc } from "d3-shape";
import { Eye, EyeOff, Info } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { BillboardData } from "@/Api/schema";
import { renderTooltip } from "@/Components/Base/BaseTable/tableHelper";
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
  // Colour per name, so that hiding a node does not recolour the others.
  colors: string[];
  chords: Chords;
  title?: string;
  onSelect: (index: number) => void;
}

/** Arcs grow, ribbons fade in, bullets flow along the links and hovering highlights the connected flows, like the former amCharts diagram. */
function ChordDiagram({ names, colors, chords, title, onSelect }: ChordDiagramProps) {
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
                  fill={colors[chord.source.index]}
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
                fill={colors[chord.source.index]}
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
              onClick={() => onSelect(group.index)}
            >
              {renderTooltip(
                `${names[group.index]}: ${formatIsk(group.value)}`,
                <path d={arcPath(group)} fill={colors[group.index]} />,
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
  const { t } = useTranslation();
  const [hidden, setHidden] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  const full = useMemo(() => buildChordMatrix(billboard), [billboard]);
  const signature = `${full.names.join("|")}:${full.matrix.flat().reduce((sum, value) => sum + value, 0)}`;

  const model = useMemo(() => {
    const visible = full.names.map((_, index) => index).filter((index) => !hidden.includes(full.names[index]));
    const matrix = visible.map((row) => visible.map((column) => full.matrix[row][column]));
    if (!matrix.flat().some((value) => value > 0)) return null;

    return {
      names: visible.map((index) => full.names[index]),
      colors: visible.map(color),
      chords: chordDirected().padAngle(0.04).sortSubgroups((a, b) => b - a)(matrix),
    };
  }, [full, hidden]);

  const details = useMemo(() => {
    const index = selected === null ? -1 : full.names.indexOf(selected);
    if (index < 0) return null;

    const flows = [
      ...full.names.map((name, other) => ({ name, other, value: full.matrix[index][other], outgoing: true })),
      ...full.names.map((name, other) => ({ name, other, value: full.matrix[other][index], outgoing: false })),
    ]
      .filter((flow) => flow.value > 0)
      .sort((a, b) => b.value - a.value);
    const total = flows.reduce((sum, flow) => sum + flow.value, 0);
    return { index, flows, total };
  }, [full, selected]);

  if (full.names.length === 0) return null;

  const toggleHidden = (name: string) =>
    setHidden((current) => (current.includes(name) ? current.filter((item) => item !== name) : [...current, name]));
  const toggleSelected = (name: string) => setSelected((current) => (current === name ? null : name));

  return (
    <>
      {model ? (
        // A new signature remounts the diagram and plays the animation again.
        <ChordDiagram
          key={signature}
          names={model.names}
          colors={model.colors}
          chords={model.chords}
          title={title}
          onSelect={(index) => toggleSelected(model.names[index])}
        />
      ) : (
        <p className="text-center text-muted my-5">{t("No flows to display")}</p>
      )}

      <div className="lg-chord-legend">
        {full.names.map((name, index) => {
          const isHidden = hidden.includes(name);
          const toggleLabel = isHidden ? t("Show {{name}}", { name }) : t("Hide {{name}}", { name });
          const detailsLabel = t("Details for {{name}}", { name });
          return (
            <span key={name} className="lg-chord-chip" data-hidden={isHidden}>
              {renderTooltip(
                toggleLabel,
                <button
                  type="button"
                  className="lg-chord-toggle"
                  aria-label={toggleLabel}
                  aria-pressed={!isHidden}
                  onClick={() => toggleHidden(name)}
                >
                  <span className="lg-chord-dot" style={{ background: color(index) }} />
                  <span>{name}</span>
                  {isHidden ? <EyeOff size={12} /> : <Eye size={12} />}
                </button>,
              )}
              {renderTooltip(
                detailsLabel,
                <button
                  type="button"
                  className="lg-chord-toggle"
                  aria-label={detailsLabel}
                  aria-pressed={selected === name}
                  onClick={() => toggleSelected(name)}
                >
                  <Info size={12} />
                </button>,
              )}
            </span>
          );
        })}
        {hidden.length > 0 && (
          <button type="button" className="lg-btn lg-btn-secondary lg-btn-sm" onClick={() => setHidden([])}>
            {t("Show all")}
          </button>
        )}
      </div>

      {details && (
        <div className="lg-chord-details" role="region" aria-label={t("Details for {{name}}", { name: selected })}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <strong>{selected}</strong>
            <span>{formatIsk(details.total)}</span>
          </div>
          <ul className="list-unstyled m-0">
            {details.flows.map((flow) => (
              <li key={`${flow.outgoing}-${flow.other}`} className="lg-chord-flow">
                <span className="lg-chord-dot" style={{ background: color(flow.other) }} />
                <span className="flex-grow-1">
                  {flow.outgoing ? `→ ${flow.name}` : `← ${flow.name}`}
                </span>
                <span>{formatIsk(flow.value)}</span>
                <span className="text-muted lg-chord-share">
                  {((flow.value / details.total) * 100).toFixed(1)}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}

export default ChordChart;
