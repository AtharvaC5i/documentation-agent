import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, CheckCircle, ChevronDown, ChevronRight } from "lucide-react";
import { getConflicts, resolveConflict } from "../utils/api";
import StepIndicator from "../components/StepIndicator";

const COVERAGE_COLORS = { strong: "badge-green", weak: "badge-orange", none: "badge-red" };

export default function ConflictResolution() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState({});
  const [resolving, setResolving] = useState({});

  useEffect(() => {
    getConflicts(projectId)
      .then((r) => { setData(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [projectId]);

  const resolve = async (conflictId, version, customText) => {
    setResolving((r) => ({ ...r, [conflictId]: true }));
    await resolveConflict({ project_id: projectId, conflict_id: conflictId, chosen_version: version, custom_text: customText });
    setData((d) => ({
      ...d,
      conflicts: d.conflicts.map((c) =>
        c.id === conflictId ? { ...c, resolved: true, chosen: version } : c
      )
    }));
    setResolving((r) => ({ ...r, [conflictId]: false }));
  };

  if (loading) return <div className="full-center"><div className="spinner" /></div>;
  if (!data) return <div className="alert alert-error">Failed to load conflict data.</div>;

  const unresolvedConflicts = data.conflicts?.filter((c) => !c.resolved) || [];
  const resolvedConflicts = data.conflicts?.filter((c) => c.resolved) || [];

  return (
    <div>
      <StepIndicator current="conflicts" />
      <div className="page-header">
        <h2>Conflict & Gap Analysis</h2>
        <p>Resolve contradictions before BRD generation. Review coverage gaps to set expectations.</p>
      </div>

      {/* Summary */}
      <div className="grid-3 mb-6">
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: unresolvedConflicts.length > 0 ? "#ef4444" : "#10b981" }}>{unresolvedConflicts.length}</div>
          <div className="text-sm text-muted mt-1">Unresolved Conflicts</div>
        </div>
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#f59e0b" }}>{data.gaps?.length || 0}</div>
          <div className="text-sm text-muted mt-1">Coverage Gaps</div>
        </div>
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#10b981" }}>{resolvedConflicts.length}</div>
          <div className="text-sm text-muted mt-1">Resolved</div>
        </div>
      </div>

      {/* Conflicts */}
      {data.conflicts?.length > 0 && (
        <div className="card mb-6">
          <div className="card-title mb-1">Detected Conflicts</div>
          <div className="card-sub">Two or more sources say contradictory things. Choose which version is correct.</div>
          {data.conflicts.map((c) => (
            <div key={c.id} className="section-review-card" style={{ marginBottom: 10 }}>
              <div className="section-review-header" onClick={() => setOpen((o) => ({ ...o, [c.id]: !o[c.id] }))}>
                <div className="flex items-center gap-3">
                  {c.resolved
                    ? <CheckCircle size={16} color="#10b981" />
                    : <AlertTriangle size={16} color="#f59e0b" />}
                  <span className="font-semibold text-sm">{c.description}</span>
                  <span className={`badge ${c.impact === "high" ? "badge-red" : c.impact === "medium" ? "badge-orange" : "badge-grey"}`}>{c.impact} impact</span>
                  {c.resolved && <span className="badge badge-green">Resolved</span>}
                </div>
                {open[c.id] ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
              </div>
              {open[c.id] && (
                <div style={{ padding: "16px 20px" }}>
                  <div className="grid-2 mb-4">
                    <div style={{ background: "#eff6ff", borderRadius: 8, padding: 14 }}>
                      <div className="text-xs font-semibold text-muted mb-2">VERSION A — {c.version_a?.req_id}</div>
                      <div className="text-sm">{c.version_a?.text}</div>
                      {!c.resolved && (
                        <button className="btn btn-sm btn-primary mt-3" disabled={resolving[c.id]} onClick={() => resolve(c.id, "a")}>
                          Use Version A
                        </button>
                      )}
                    </div>
                    <div style={{ background: "#fef3c7", borderRadius: 8, padding: 14 }}>
                      <div className="text-xs font-semibold text-muted mb-2">VERSION B — {c.version_b?.req_id}</div>
                      <div className="text-sm">{c.version_b?.text}</div>
                      {!c.resolved && (
                        <button className="btn btn-sm btn-secondary mt-3" disabled={resolving[c.id]} onClick={() => resolve(c.id, "b")}>
                          Use Version B
                        </button>
                      )}
                    </div>
                  </div>
                  {c.resolved && <div className="alert alert-success">Resolved: version {c.chosen?.toUpperCase()} chosen.</div>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {data.conflicts?.length === 0 && (
        <div className="alert alert-success mb-6">
          <CheckCircle size={16} />
          No conflicts detected between sources.
        </div>
      )}

      {/* Gaps */}
      {data.gaps?.length > 0 && (
        <div className="card mb-6">
          <div className="card-title mb-1">Coverage Gaps</div>
          <div className="card-sub">These BRD sections have insufficient input coverage. They will be marked TBD or generated with limited context.</div>
          <table className="data-table">
            <thead><tr><th>BRD Section</th><th>Coverage</th><th>Suggested Action</th></tr></thead>
            <tbody>
              {data.gaps.map((g) => (
                <tr key={g.id}>
                  <td className="font-semibold text-sm">{g.section}</td>
                  <td><span className={`badge ${COVERAGE_COLORS[g.coverage_level]}`}>{g.coverage_level}</span></td>
                  <td className="text-sm text-muted">{g.suggested_action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Section coverage overview */}
      {data.coverage && (
        <div className="card mb-6">
          <div className="card-title mb-4">Full Section Coverage Map</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {Object.entries(data.coverage).map(([section, level]) => (
              <div key={section} className="flex items-center justify-between" style={{ padding: "6px 0", borderBottom: "1px solid var(--grey-100)" }}>
                <span className="text-sm">{section}</span>
                <span className={`badge ${COVERAGE_COLORS[level] || "badge-grey"}`}>{level}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button className="btn btn-primary btn-lg" onClick={() => navigate(`/project/${projectId}/sections`)}>
          Continue to Section Selection →
        </button>
        {unresolvedConflicts.length > 0 && (
          <div className="alert alert-warning" style={{ alignItems: "center" }}>
            <AlertTriangle size={15} /> {unresolvedConflicts.length} conflict(s) still unresolved. You can proceed but they may affect quality.
          </div>
        )}
      </div>
    </div>
  );
}
