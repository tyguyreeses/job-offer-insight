import type { CompareOffer, Metric } from "../types";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

type Props = {
  offers: CompareOffer[];
  sortBy: Metric;
  onSortByChange: (metric: Metric) => void;
  onEdit: (offer: CompareOffer) => void;
  onDelete: (offer: CompareOffer) => void;
};

const metricLabels: Record<Metric, string> = {
  total_comp_annual: "Annual total",
  total_comp_year1: "Year 1 total",
  total_comp_col_adjusted: "COL-adjusted total",
};

export function OfferTable({ offers, sortBy, onSortByChange, onEdit, onDelete }: Props) {
  return (
    <section className="panel">
      <div className="panel__header panel__header--split">
        <h2>Offer comparison</h2>
        <label className="inline-label">
          Rank by
          <select value={sortBy} onChange={(event) => onSortByChange(event.target.value as Metric)}>
            {Object.entries(metricLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {offers.length === 0 ? <p className="empty">No offers yet. Add one to begin comparing.</p> : null}

      {offers.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Location</th>
                <th>Base</th>
                <th>Annual total</th>
                <th>Year 1 total</th>
                <th>COL-adjusted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {offers.map((offer) => (
                <tr key={offer.id}>
                  <td>{offer.company}</td>
                  <td>{offer.role}</td>
                  <td>{offer.location}</td>
                  <td>{currency.format(offer.base_salary)}</td>
                  <td>{currency.format(offer.total_comp_annual)}</td>
                  <td>{currency.format(offer.total_comp_year1)}</td>
                  <td>{currency.format(offer.total_comp_col_adjusted)}</td>
                  <td>
                    <div className="action-row">
                      <button onClick={() => onEdit(offer)}>Edit</button>
                      <button className="danger" onClick={() => onDelete(offer)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}
