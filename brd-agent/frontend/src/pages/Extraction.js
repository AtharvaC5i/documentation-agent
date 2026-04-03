import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getProjectStatus, getRequirements } from "../utils/api";
import { usePolling } from "../hooks/usePolling";
import StepIndicator from "../components/StepIndicator";
import ProgressCard from "../components/ProgressCard";

const TYPE_COLORS = {
  functional: "badge-blue",
  non_functional: "badge-orange",
  business_rule: "badge-green",
  assumption: "badge-grey",
  constraint: "badge-red",
  stakeholder: "badge-blue",
};

export default function Extraction() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState({ status: "extracting", progress: 0, progress_message: "Starting..." });
  const [requirements, setRequirements] = useState([]);
  const [glossary, setGlossary] = useState({});
  const [done, setDone] = useState(false);

  const poll = async () => {
    try {
      const s = await getProjectStatus(projectId);
      setStatus(s.data);
      if (s.data.status === "extracted") {
        setDone(true);
        const r = await getRequirements(projectId);
        setRequirements(r.data.requirements || []);
        setGlossary(r.data.glossary || {});
      }
      if (s.data.status === "error") setDone(true);
    } catch {}
  };

  usePolling(poll, 2000, !done);

  const typeCounts = requirements.reduce((acc, r) => {
    acc[r.type] = (acc[r.type] || 0) + 1; return acc;
  }, {});

  return (
    <div>
      <StepIndicator current="extraction" />
      <div className="page-header">
        <h2>Requirements Extraction</h2>
        <p>Normalizing transcript, parsing user stories, building Requirements Pool.</p>
      </div>

      {!done && <ProgressCard title="Extracting requirements..." message={status.progress_message} progress={status.progress} />}

      {status.status === "error" && (
        <div className="alert alert-error mb-4">{status.progress_message}</div>
      )}

      {done && status.status === "extracted" && (
        <>
          <div className="grid-3 mb-6">
            {[
              { label: "Total Requirements", value: requirements.length, color: "#2563eb" },
              { label: "Glossary Terms", value: Object.keys(glossary).length, color: "#06b6d4" },
              { label: "Source Files", value: 2, color: "#10b981" },
            ].map((stat) => (
              <div key={stat.label} className="card" style={{ textAlign: "center" }}>
                <div style={{ fontSize: "2rem", fontWeight: 700, color: stat.color }}>{stat.value}</div>
                <div className="text-sm text-muted mt-1">{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Type breakdown */}
          <div className="card mb-6">
            <div className="card-title mb-4">Requirements by Type</div>
            <div className="flex gap-3" style={{ flexWrap: "wrap" }}>
              {Object.entries(typeCounts).map(([type, count]) => (
                <div key={type} className="flex items-center gap-2">
                  <span className={`badge ${TYPE_COLORS[type] || "badge-grey"}`}>{count}</span>
                  <span className="text-sm" style={{ textTransform: "capitalize" }}>{type.replace("_", " ")}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Requirements pool preview */}
          <div className="card mb-6">
            <div className="card-title mb-4">Requirements Pool Preview</div>
            <div style={{ maxHeight: 360, overflowY: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr><th>ID</th><th>Type</th><th>Description</th><th>Source</th><th>Priority</th></tr>
                </thead>
                <tbody>
                  {requirements.slice(0, 30).map((r) => (
                    <tr key={r.req_id}>
                      <td><code style={{ fontSize: ".8rem" }}>{r.req_id}</code></td>
                      <td><span className={`badge ${TYPE_COLORS[r.type] || "badge-grey"}`} style={{ fontSize: ".7rem" }}>{r.type.replace("_", " ")}</span></td>
                      <td style={{ maxWidth: 400, fontSize: ".85rem" }}>{r.description}</td>
                      <td className="text-xs text-muted">{r.source}</td>
                      <td>{r.priority && <span className="badge badge-grey" style={{ fontSize: ".7rem" }}>{r.priority}</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {requirements.length > 30 && <div className="text-xs text-muted mt-2">Showing 30 of {requirements.length} requirements</div>}
          </div>

          {/* Glossary */}
          {Object.keys(glossary).length > 0 && (
            <div className="card mb-6">
              <div className="card-title mb-4">Project Glossary ({Object.keys(glossary).length} terms)</div>
              <div style={{ columns: 2, gap: 24 }}>
                {Object.entries(glossary).map(([term, def]) => (
                  <div key={term} style={{ breakInside: "avoid", marginBottom: 10 }}>
                    <div className="font-semibold text-sm">{term}</div>
                    <div className="text-xs text-muted">{def}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button className="btn btn-primary btn-lg" onClick={() => navigate(`/project/${projectId}/conflicts`)}>
            Continue to Conflict Review →
          </button>
        </>
      )}
    </div>
  );
}
