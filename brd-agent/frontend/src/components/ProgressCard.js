import React from "react";

export default function ProgressCard({ progress, message, title }) {
  return (
    <div className="card" style={{ textAlign: "center", padding: "48px 32px" }}>
      <div className="spinner" style={{ margin: "0 auto 18px", width: 28, height: 28, borderWidth: 3 }} />
      <div className="card-title" style={{ fontSize: "1rem", marginBottom: 5 }}>{title || "Processing..."}</div>
      <div className="text-muted text-sm" style={{ marginBottom: 20 }}>{message}</div>
      <div className="progress-bar-track" style={{ maxWidth: 380, margin: "0 auto" }}>
        <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
      </div>
      <div className="text-xs text-muted mt-2">{progress}% complete</div>
    </div>
  );
}
