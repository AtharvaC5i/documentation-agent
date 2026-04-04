export default function MetricCard({ label, value, sub, className = "" }) {
  return (
    <div
      className={`bg-surface border border-border rounded-xl px-5 py-4 ${className}`}
    >
      <div className="stat-value">{value}</div>
      <div className="text-xs font-semibold text-text mt-1">{label}</div>
      {sub && <div className="text-[11px] text-text-faint mt-0.5">{sub}</div>}
    </div>
  );
}
