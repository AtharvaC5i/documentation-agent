import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, CheckCircle, ChevronDown, ChevronRight } from "lucide-react";
import { getConflicts, resolveConflict } from "../utils/api";
import StepIndicator from "../components/StepIndicator";

const COVERAGE_BADGE = { strong: "badge-green", weak: "badge-orange", none: "badge-red" };

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

  const resolve = async (conflictId, version) => {
    setResolving((r) => ({ ...r, [conflictId]: true }));
    await resolveConflict({ project_id: projectId, conflict_id: conflictId, chosen_version: version });
    setData((d) => ({
      ...d,
      conflicts: d.conflicts.map((c) =>
        c.id === conflictId ? { ...c, resolved: true, chosen: version } : c
      )
    }));
    setResolving((r) => ({ ...r, [conflictId]: false }));
  };

  if (loading) return <div className="full-center"><div className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} /></div>;
  if (!data) return <div className="alert alert-error">Failed to load conflict data.</div>;

  const unresolvedConflicts = data.conflicts?.filter((c) => !c.resolved) || [];
  const resolvedConflicts   = data.conflicts?.filter((c) => c.resolved) || [];

  return (
    <div>
      <StepIndicator current="conflicts" />
      <div className="page-header">
        <h2>Conflict & Gap Analysis</h2>
        <p>Resolve contradictions before BRD generation. Review coverage gaps to set expectations.</p>
      </div>

      {/* Summary */}
      <div className="grid-3 mb-6">
        {[
          { label: "Unresolved Conflicts", value: unresolvedConflicts.length, color: unresolvedConflicts.length > 0 ? "#fca5a5" : "#6ee7b7" },
          { label: "Coverage Gaps",        value: data.gaps?.length || 0,    color: "#fcd34d" },
          { label: "Resolved",             value: resolvedConflicts.length,   color: "#6ee7b7" },
        ].map((s) => (
          <div key={s.label} className="card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: 800, color: s.color }}>{s.value}</div>
            <div className="text-sm text-muted mt-1">{s.label}</div>
          </div>
        ))}
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
                    ? <CheckCircle size={16} color="#6ee7b7" />
                    : <AlertTriangle size={16} color="#fcd34d" />}
                  <span className="font-semibold text-sm">{c.description}</span>
                  <span className={`badge ${c.impact === "high" ? "badge-red" : c.impact === "medium" ? "badge-orange" : "badge-grey"}`}>
                    {c.impact} impact
                  </span>
                  {c.resolved && <span className="badge badge-green">Resolved</span>}
                </div>
                {open[c.id] ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
              </div>

              {open[c.id] && (
                <div style={{ padding: "16px 20px" }}>
                  <div className="grid-2 mb-4" style={{ gap: 12 }}>
                    {/* Version A */}
                    <div style={{
                      background: "rgba(59,130,246,.08)",
                      border: "1px solid rgba(59,130,246,.25)",
                      borderRadius: 8, padding: 14,
                    }}>
                      <div className="text-xs font-semibold mb-2" style={{ color: "#93c5fd", letterSpacing: ".05em" }}>
                        VERSION A — {c.version_a?.req_id}
                      </div>
                      <div className="text-sm" style={{ color: "var(--text-secondary)", lineHeight: 1.6 }}>
                        {c.version_a?.text}
                      </div>
                      {!c.resolved && (
                        <button
                          className="btn btn-primary btn-sm mt-3"
                          disabled={resolving[c.id]}
                          onClick={() => resolve(c.id, "a")}
                        >
                          Use Version A
                        </button>
                      )}
                    </div>

                    {/* Version B */}
                    <div style={{
                      background: "rgba(245,158,11,.08)",
                      border: "1px solid rgba(245,158,11,.25)",
                      borderRadius: 8, padding: 14,
                    }}>
                      <div className="text-xs font-semibold mb-2" style={{ color: "#fcd34d", letterSpacing: ".05em" }}>
                        VERSION B — {c.version_b?.req_id}
                      </div>
                      <div className="text-sm" style={{ color: "var(--text-secondary)", lineHeight: 1.6 }}>
                        {c.version_b?.text}
                      </div>
                      {!c.resolved && (
                        <button
                          className="btn btn-secondary btn-sm mt-3"
                          disabled={resolving[c.id]}
                          onClick={() => resolve(c.id, "b")}
                        >
                          Use Version B
                        </button>
                      )}
                    </div>
                  </div>
                  {c.resolved && (
                    <div className="alert alert-success">
                      <CheckCircle size={14} />
                      Resolved: version {c.chosen?.toUpperCase()} chosen.
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {data.conflicts?.length === 0 && (
        <div className="alert alert-success mb-6">
          <CheckCircle size={16} /> No conflicts detected between sources.
        </div>
      )}

      {/* Coverage Gaps */}
      {data.gaps?.length > 0 && (
        <div className="card mb-6">
          <div className="card-title mb-1">Coverage Gaps</div>
          <div className="card-sub">
            These BRD sections have insufficient input coverage. They will be generated with limited context or marked TBD.
          </div>
          <table className="data-table">
            <thead><tr><th>BRD Section</th><th>Coverage</th><th>Suggested Action</th></tr></thead>
            <tbody>
              {data.gaps.map((g) => (
                <tr key={g.id}>
                  <td className="font-semibold text-sm">{g.section}</td>
                  <td><span className={`badge ${COVERAGE_BADGE[g.coverage_level]}`}>{g.coverage_level}</span></td>
                  <td className="text-sm text-muted">{g.suggested_action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Full Section Coverage Map */}
      {data.coverage && (
        <div className="card mb-6">
          <div className="card-title mb-1">Full Section Coverage Map</div>
          <div className="card-sub">
            Shows how well each of the 19 BRD sections is covered by your inputs. Strong = enough to generate well. Weak = partial, will need review. None = no data found.
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
            {Object.entries(data.coverage).map(([section, level]) => (
              <div key={section} className="flex items-center justify-between"
                style={{ padding: "7px 4px", borderBottom: "1px solid var(--border)" }}>
                <span className="text-sm" style={{ color: "var(--text-secondary)" }}>{section}</span>
                <span className={`badge ${COVERAGE_BADGE[level] || "badge-grey"}`}>{level}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button className="btn btn-primary btn-lg" onClick={() => navigate(`/project/${projectId}/sections`)}>
        Continue to Section Selection →
      </button>
    </div>
  );
}
