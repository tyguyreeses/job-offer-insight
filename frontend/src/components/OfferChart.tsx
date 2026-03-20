import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { CompareOffer, Metric } from "../types";

const chartLabels: Record<Metric, string> = {
  total_comp_annual: "Annual total compensation",
  total_comp_year1: "Year 1 total compensation",
  total_comp_col_adjusted: "COL-adjusted total compensation",
};

type Props = {
  offers: CompareOffer[];
  metric: Metric;
};

export function OfferChart({ offers, metric }: Props) {
  const chartData = offers.map((offer) => ({
    name: offer.company,
    value: offer[metric],
  }));

  return (
    <section className="panel chart-panel">
      <h2>{chartLabels[metric]}</h2>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="4 4" vertical={false} />
            <XAxis dataKey="name" tickLine={false} axisLine={false} />
            <YAxis tickFormatter={(value) => `$${Math.round(value / 1000)}k`} tickLine={false} axisLine={false} />
            <Tooltip formatter={(value: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value)} />
            <Bar dataKey="value" fill="#ff7043" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
