// React
import { useMemo } from "react";

// Third Party
import type { ApexOptions } from "apexcharts";
import Chart from "react-apexcharts";
import { useTranslation } from "react-i18next";

import type { BillboardSchema } from "@/Api/schema";
import ChordChart from "@/Components/Ledger/LedgerView/ChordChart";
import { buildTimelineChart } from "@/Utils/billboard";
import { formatNumber } from "@/Utils/eveOnline";
import { formatIsk } from "@/Utils/ledger";

export interface LedgerChartsProps {
  billboard?: BillboardSchema;
}

function LedgerCharts({ billboard }: LedgerChartsProps) {
  const { t } = useTranslation();

  const timeline = useMemo(() => buildTimelineChart(billboard?.xy_chart), [billboard?.xy_chart]);

  const timelineOptions = useMemo<ApexOptions>(
    () => ({
      chart: { type: "bar", stacked: true, toolbar: { show: false }, background: "transparent" },
      title: { text: t("Income over time") },
      xaxis: { categories: timeline.categories },
      yaxis: { labels: { formatter: (value: number) => formatNumber(value, "") } },
      tooltip: { y: { formatter: (value: number) => formatIsk(value) } },
      dataLabels: { enabled: false },
      theme: { mode: "dark" },
    }),
    [timeline.categories, t],
  );

  const hasChord = (billboard?.chord_chart?.series.length ?? 0) > 0;
  if (timeline.series.length === 0 && !hasChord) {
    return null;
  }

  const singleChart = (timeline.series.length > 0 && !hasChord) || (hasChord && timeline.series.length === 0);
  const colClass = singleChart ? "col-12" : "col-12 col-xl-6";

  return (
    <div className="row g-3 align-items-end">
      {timeline.series.length > 0 && (
        <div className={colClass}>
          <div className="aa-panel">
            <Chart options={timelineOptions} series={timeline.series} type="bar" height={380} />
          </div>
        </div>
      )}
      {hasChord && (
        <div className={colClass}>
          <div className="aa-panel">
            <ChordChart billboard={billboard?.chord_chart} title={t("Distribution")} />
          </div>
        </div>
      )}
    </div>
  );
}

export default LedgerCharts;
