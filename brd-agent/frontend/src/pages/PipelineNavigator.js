import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Upload, Cpu, AlertTriangle, LayoutList, Zap, Eye, CheckCircle,
  ChevronRight, RefreshCw, FileText, Database, BookOpen, Shield
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { getRequirements, getConflicts, getSuggestedSections, getSections, listProjects } from "../utils/api";
import { downloadBRD } from "../utils/download";
import QualityBadge from "../components/QualityBadge";

// ── Stage definitions ───────────────────────────────────────────────────────
const STAGES = [
  { key: "upload",      label: "Upload",       icon: Upload },
  { key: "extraction",  label: "Extraction",   icon: Cpu },
  { key: "conflicts",   label: "Conflicts",    icon: AlertTriangle },
  { key: "sections",    label: "Sections",     icon: LayoutList },
  { key: "generation",  label: "Generation",   icon: Zap },
  { key: "review",      label: "Review",       icon: Eye },
  { key: "complete",    label: "Complete",     icon: CheckCircle },
];

const TYPE_COLORS = {
  functional:      "#2563eb",
  non_functional:  "#f59e0b",
  business_rule:   "#10b981",
  assumption:      "#94a3b8",
  constraint:      "#ef4444",
  stakeholder:     "#8b5cf6",
};

const COVERAGE_BADGE = {
  strong: "badge-green",
  weak:   "badge-orange",
  none:   "badge-red",
};

// ── Main Component ──────────────────────────────────────────────────────────
export default function PipelineNavigator() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [active, setActive] = useState("extraction");
  const [project, setProject] = useState(null);

  // Data per stage
  const [requirements, setRequirements] = useState([]);
  const [glossary, setGlossary]         = useState({});
  const [conflicts, setConflicts]       = useState([]);
  const [gaps, setGaps]                 = useState([]);
  const [coverage, setCoverage]         = useState({});
  const [suggestedSections, setSuggestedSections] = useState([]);
  const [generatedSections, setGeneratedSections] = useState([]);

  // UI state
  const [loading, setLoading]           = useState(false);
  const [reqFilter, setReqFilter]       = useState("all");
  const [openSection, setOpenSection]   = useState(null);
  const [downloading, setDownloading]   = useState(false);
  const [dlError, setDlError]           = useState("");

  // Load project metadata
  useEffect(() => {
    listProjects()
      .then((r) => {
        const p = (r.data.projects || []).find((p) => p.id === projectId);
        if (p) setProject(p);
      })
      .catch(() => {});
  }, [projectId]);

  // Load data when stage changes
  useEffect(() => {
    loadStageData(active);
  }, [active, projectId]);

  const loadStageData = async (stage) => {
    setLoading(true);
    try {
      if (stage === "extraction") {
        const r = await getRequirements(projectId);
        setRequirements(r.data.requirements || []);
        setGlossary(r.data.glossary || {});
      }
      if (stage === "conflicts") {
        const r = await getConflicts(projectId);
        setConflicts(r.data.conflicts || []);
        setGaps(r.data.gaps || []);
        setCoverage(r.data.coverage || {});
      }
      if (stage === "sections") {
        const r = await getSuggestedSections(projectId);
        setSuggestedSections(r.data.suggested_sections || []);
      }
      if (stage === "generation" || stage === "review" || stage === "complete") {
        const r = await getSections(projectId);
        setGeneratedSections(r.data.sections || []);
      }
    } catch {}
    setLoading(false);
  };

  const handleDownload = async () => {
    setDownloading(true); setDlError("");
    try { await downloadBRD(projectId, project?.project_name); }
    catch (e) { setDlError(e.message); }
    finally { setDownloading(false); }
  };

  // ── Stage tab bar ───────────────────────────────────────────────────────
  const renderTabs = () => (
    <div style={{ display: "flex", borderBottom: "2px solid var(--grey-200)", marginBottom: 24, overflowX: "auto", gap: 0 }}>
      {STAGES.map((s) => {
        const Icon = s.icon;
        const isActive = s.key === active;
        return (
          <button
            key={s.key}
            onClick={() => setActive(s.key)}
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "10px 18px",
              border: "none", background: "none", cursor: "pointer",
              borderBottom: isActive ? "2.5px solid #2563eb" : "2.5px solid transparent",
              marginBottom: -2,
              color: isActive ? "#2563eb" : "#64748b",
              fontWeight: isActive ? 700 : 500,
              fontSize: ".85rem", whiteSpace: "nowrap",
              transition: "all .15s",
            }}
          >
            <Icon size={15} />
            {s.label}
          </button>
        );
      })}
      <div style={{ flex: 1 }} />
      <button
        className="btn btn-sm btn-secondary"
        style={{ margin: "6px 0 6px 8px", alignSelf: "center" }}
        onClick={() => loadStageData(active)}
      >
        <RefreshCw size={13} /> Refresh
      </button>
    </div>
  );

  // ── Upload stage ────────────────────────────────────────────────────────
  const renderUpload = () => (
    <div>
      <div className="card">
        <div className="card-title mb-2">Project Details</div>
        {project ? (
          <table className="data-table">
            <tbody>
              {[
                ["Project Name", project.project_name],
                ["Client", project.client_name],
                ["Industry", project.industry],
                ["Description", project.description],
                ["Team", (project.team_members || []).join(", ") || "—"],
                ["Status", project.status],
              ].map(([k, v]) => (
                <tr key={k}>
                  <td className="font-semibold text-sm" style={{ width: 140 }}>{k}</td>
                  <td className="text-sm">{v || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-muted text-sm">Loading project details...</div>
        )}
      </div>
      <div className="flex gap-3 mt-4">
        <button className="btn btn-primary" onClick={() => navigate(`/project/${projectId}/upload`)}>
          Re-upload Files
        </button>
      </div>
    </div>
  );

  // ── Extraction stage ────────────────────────────────────────────────────
  const renderExtraction = () => {
    const filtered = reqFilter === "all"
      ? requirements
      : requirements.filter((r) => r.type === reqFilter);

    const typeCounts = requirements.reduce((acc, r) => {
      acc[r.type] = (acc[r.type] || 0) + 1; return acc;
    }, {});

    return (
      <div>
        {/* Stats row */}
        <div className="grid-3 mb-6">
          <div className="card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "#2563eb" }}>{requirements.length}</div>
            <div className="text-sm text-muted mt-1">Total Requirements</div>
          </div>
          <div className="card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "#06b6d4" }}>{Object.keys(glossary).length}</div>
            <div className="text-sm text-muted mt-1">Glossary Terms</div>
          </div>
          <div className="card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "#10b981" }}>
              {new Set(requirements.filter(r => r.source === "transcript").map(r => r.req_id)).size}
              {" / "}
              {new Set(requirements.filter(r => r.source === "user_story").map(r => r.req_id)).size}
            </div>
            <div className="text-sm text-muted mt-1">Transcript Reqs / Story Reqs</div>
          </div>
        </div>

        {/* Type filter chips */}
        <div className="flex gap-2 mb-4" style={{ flexWrap: "wrap" }}>
          <button
            className={`btn btn-sm ${reqFilter === "all" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setReqFilter("all")}
          >All ({requirements.length})</button>
          {Object.entries(typeCounts).map(([type, count]) => (
            <button
              key={type}
              className={`btn btn-sm ${reqFilter === type ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setReqFilter(type)}
              style={{ borderLeft: `3px solid ${TYPE_COLORS[type] || "#94a3b8"}` }}
            >
              {type.replace("_", " ")} ({count})
            </button>
          ))}
        </div>

        {/* Requirements table */}
        <div className="card mb-6">
          <div className="card-title mb-3">Requirements Pool — {filtered.length} shown</div>
          <div style={{ maxHeight: 420, overflowY: "auto" }}>
            <table className="data-table">
              <thead>
                <tr><th>ID</th><th>Type</th><th>Description</th><th>Source</th><th>Priority</th><th>Module</th></tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.req_id}>
                    <td><code style={{ fontSize: ".78rem" }}>{r.req_id}</code></td>
                    <td>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                        <span style={{ width: 8, height: 8, borderRadius: "50%", background: TYPE_COLORS[r.type] || "#94a3b8", flexShrink: 0 }} />
                        <span style={{ fontSize: ".75rem", color: "#64748b" }}>{r.type.replace("_", " ")}</span>
                      </span>
                    </td>
                    <td style={{ fontSize: ".85rem", maxWidth: 380 }}>{r.description}</td>
                    <td><span className="badge badge-grey" style={{ fontSize: ".68rem" }}>{r.source}</span></td>
                    <td>{r.priority && <span className="badge badge-grey" style={{ fontSize: ".68rem" }}>{r.priority.replace("_", " ")}</span>}</td>
                    <td style={{ fontSize: ".75rem", color: "#94a3b8" }}>{r.module_tag || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Glossary */}
        {Object.keys(glossary).length > 0 && (
          <div className="card">
            <div className="card-title mb-4"><BookOpen size={15} style={{ marginRight: 6 }} />Project Glossary ({Object.keys(glossary).length} terms)</div>
            <div style={{ columns: 2, gap: 24 }}>
              {Object.entries(glossary).map(([term, def]) => (
                <div key={term} style={{ breakInside: "avoid", marginBottom: 10, padding: "8px 0", borderBottom: "1px solid var(--grey-100)" }}>
                  <div className="font-semibold text-sm">{term}</div>
                  <div className="text-xs text-muted mt-1">{def}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // ── Conflicts stage ─────────────────────────────────────────────────────
  const renderConflicts = () => (
    <div>
      <div className="grid-3 mb-6">
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: conflicts.filter(c => !c.resolved).length > 0 ? "#ef4444" : "#10b981" }}>
            {conflicts.filter(c => !c.resolved).length}
          </div>
          <div className="text-sm text-muted mt-1">Unresolved Conflicts</div>
        </div>
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#f59e0b" }}>{gaps.length}</div>
          <div className="text-sm text-muted mt-1">Coverage Gaps</div>
        </div>
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", fontWeight: 700, color: "#10b981" }}>
            {conflicts.filter(c => c.resolved).length}
          </div>
          <div className="text-sm text-muted mt-1">Resolved</div>
        </div>
      </div>

      {conflicts.length > 0 && (
        <div className="card mb-4">
          <div className="card-title mb-3">Detected Conflicts</div>
          {conflicts.map((c) => (
            <div key={c.id} style={{ padding: "12px 0", borderBottom: "1px solid var(--grey-100)" }}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`badge ${c.resolved ? "badge-green" : c.impact === "high" ? "badge-red" : "badge-orange"}`}>
                  {c.resolved ? "Resolved" : c.impact}
                </span>
                <span className="text-sm font-semibold">{c.description}</span>
              </div>
              <div className="grid-2 mt-2" style={{ gap: 8 }}>
                <div style={{ background: "rgba(59,130,246,.08)", borderRadius: 6, padding: "8px 12px", fontSize: ".82rem" }}>
                  <div className="text-xs font-semibold text-muted mb-1">VERSION A — {c.version_a?.req_id}</div>
                  {c.version_a?.text}
                </div>
                <div style={{ background: "rgba(245,158,11,.08)", borderRadius: 6, padding: "8px 12px", fontSize: ".82rem" }}>
                  <div className="text-xs font-semibold text-muted mb-1">VERSION B — {c.version_b?.req_id}</div>
                  {c.version_b?.text}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <div className="card-title mb-3"><Shield size={15} style={{ marginRight: 6 }} />Section Coverage Map</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
          {Object.entries(coverage).map(([section, level]) => (
            <div key={section} className="flex items-center justify-between" style={{ padding: "6px 4px", borderBottom: "1px solid var(--grey-100)" }}>
              <span className="text-sm">{section}</span>
              <span className={`badge ${COVERAGE_BADGE[level] || "badge-grey"}`}>{level}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // ── Sections stage ──────────────────────────────────────────────────────
  const renderSections = () => {
    const suggested = suggestedSections.filter(s => s.suggested);
    const notSuggested = suggestedSections.filter(s => !s.suggested);
    return (
      <div>
        <div className="alert alert-info mb-4">
          <LayoutList size={15} style={{ flexShrink: 0 }} />
          <div className="text-sm"><strong>{suggested.length}</strong> sections were pre-selected by AI. <strong>{notSuggested.length}</strong> were left unchecked due to insufficient coverage.</div>
        </div>
        <div className="card">
          <div className="card-title mb-4">AI Section Recommendation</div>
          {suggestedSections.map((s) => (
            <div key={s.id} className="flex items-center gap-3" style={{ padding: "10px 0", borderBottom: "1px solid var(--grey-100)" }}>
              <div style={{ width: 18, height: 18, borderRadius: 4, background: s.suggested ? "#2563eb" : "var(--grey-200)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                {s.suggested && <CheckCircle size={12} color="#fff" />}
              </div>
              <div style={{ flex: 1 }}>
                <div className="text-sm font-semibold">{s.name}</div>
                {s.reason && <div className="text-xs text-muted mt-0.5">{s.reason}</div>}
              </div>
              <span className={`badge ${COVERAGE_BADGE[s.coverage] || "badge-grey"}`}>{s.coverage}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // ── Generation / Review / Complete stage ────────────────────────────────
  const renderSectionsOutput = () => {
    const avgQ = generatedSections.length > 0
      ? generatedSections.reduce((a, s) => a + (s.quality_score || 0), 0) / generatedSections.length
      : 0;

    return (
      <div>
        {/* Summary */}
        <div className="grid-3 mb-6">
          <div className="card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "#2563eb" }}>{generatedSections.length}</div>
            <div className="text-sm text-muted mt-1">Sections Generated</div>
          </div>
          <div className="card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: avgQ >= 0.8 ? "#10b981" : avgQ >= 0.6 ? "#f59e0b" : "#ef4444" }}>
              {Math.round(avgQ * 100)}%
            </div>
            <div className="text-sm text-muted mt-1">Avg Quality</div>
          </div>
          <div className="card" style={{ textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "#10b981" }}>
              {generatedSections.filter(s => s.approved).length}
            </div>
            <div className="text-sm text-muted mt-1">Approved</div>
          </div>
        </div>

        {/* Sections list with expandable content */}
        {generatedSections.map((s, i) => (
          <div key={s.id} className="section-review-card" style={{ marginBottom: 10 }}>
            <div
              className="section-review-header"
              onClick={() => setOpenSection(openSection === s.id ? null : s.id)}
            >
              <div className="flex items-center gap-3">
                <span className="text-muted text-sm" style={{ minWidth: 24 }}>{i + 1}</span>
                {s.approved
                  ? <CheckCircle size={16} color="#10b981" />
                  : <div style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid var(--grey-300)" }} />}
                <span className="font-semibold text-sm">{s.name}</span>
                <QualityBadge score={s.quality_score || 0} />
                {s.status === "regenerated" && <span className="badge badge-blue">Regenerated</span>}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">{s.req_count} reqs</span>
                {openSection === s.id ? "▲" : "▼"}
              </div>
            </div>
            {openSection === s.id && (
              <div style={{ padding: "16px 20px", borderTop: "1px solid var(--grey-200)" }}>
                {/* Source req IDs */}
                {s.source_req_ids?.length > 0 && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-muted mb-2">SOURCE REQUIREMENTS</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                      {s.source_req_ids.map((id) => (
                        <code key={id} style={{ background: "var(--bg-elevated)", padding: "2px 7px", borderRadius: 4, fontSize: ".73rem" }}>{id}</code>
                      ))}
                    </div>
                  </div>
                )}
                {/* Content preview */}
                <div style={{ background: "var(--bg-elevated)", borderRadius: 8, padding: "14px 18px", maxHeight: 450, overflowY: "auto" }}>
                  <div className="md-content">
                    <ReactMarkdown>{s.content || "*No content.*"}</ReactMarkdown>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Download button in complete stage */}
        {active === "complete" && (
          <div className="card mt-4" style={{ background: "var(--navy)", border: "none", padding: "20px 24px" }}>
            <div className="flex items-center justify-between">
              <div className="font-semibold" style={{ color: "#fff" }}>Download your BRD</div>
              <button
                className="btn"
                style={{ background: "#06b6d4", color: "#fff" }}
                onClick={handleDownload}
                disabled={downloading}
              >
                {downloading ? "Preparing..." : <><Download size={15} /> Download .docx</>}
              </button>
            </div>
            {dlError && <div className="text-sm mt-2" style={{ color: "#fca5a5" }}>{dlError}</div>}
          </div>
        )}
      </div>
    );
  };

  // ── Stage content router ─────────────────────────────────────────────────
  const renderContent = () => {
    if (loading) return <div className="full-center"><div className="spinner" /></div>;
    switch (active) {
      case "upload":      return renderUpload();
      case "extraction":  return renderExtraction();
      case "conflicts":   return renderConflicts();
      case "sections":    return renderSections();
      case "generation":
      case "review":
      case "complete":    return renderSectionsOutput();
      default:            return null;
    }
  };

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h2>Pipeline Inspector</h2>
            <p>View the output of every pipeline stage. Click any tab to inspect.</p>
          </div>
          <div className="flex gap-2">
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/project/${projectId}/review`)}>
              <Eye size={14} /> Go to Review
            </button>
            <button className="btn btn-primary btn-sm" onClick={() => navigate(`/project/${projectId}/complete`)}>
              <FileText size={14} /> Complete
            </button>
          </div>
        </div>
      </div>

      {renderTabs()}
      {renderContent()}
    </div>
  );
}
