import React from "react";

export default function QualityBadge({ score }) {
  const pct = Math.round(score * 100);
  const cls = pct >= 80 ? "quality-high" : pct >= 60 ? "quality-mid" : "quality-low";
  const label = pct >= 80 ? "Good" : pct >= 60 ? "Fair" : "Low";
  return <span className={`quality-pill ${cls}`}>{pct}% {label}</span>;
}
