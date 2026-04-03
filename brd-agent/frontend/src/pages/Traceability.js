import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Link2, Download, RefreshCw, ArrowLeft, Filter, FileText } from "lucide-react";
import { getTraceability, generateTraceability, downloadTraceability, listProjects } from "../utils/api";

const TYPE_COLORS = {
  "Functional":      { bg: "#dbeafe", text: "#1d4ed8" },
  "Non Functional":  { bg: "#fef3c7", text: "#92400e" },
  "Business Rule":   { bg: "#d1fae5", text: "#065f46" },
  "Assumption":      { bg: "#f1f5f9", text: "#475569" },
  "Constraint":      { bg: "#fee2e2", text: "#991b1b" },
  "Stakeholder":     { bg: "#ede9fe", text: "#5b21b6" },
};

const SOURCE_COLORS = {
  "Transcript":   { bg: "#eff6ff", text: "#1d4ed8" },
  "User Story":   { bg: "#ecfdf5", text: "#065f46" },
};

export default function Traceability() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [matrix, setMatrix] = useState([]);
  const [docReady, setDocReady] = useState(false);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [project, setProject] = useState(null);
  const [sectionFilter, setSectionFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");

  useEffect(() => {
    loadAll();
  }, [projectId]);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [t, p] = await Promise.all([
        getTraceability(projectId),
        listProjects(),
      ]);
      setMatrix(t.data.matrix || []);
      setDocReady(t.data.doc_ready || false);
      const proj = (p.data.projects || []).find((x) => x.id === projectId);
      if (proj) setProject(proj);
    } catch {}
    setLoading(false);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    await generateTraceability(projectId);
    // Poll until ready
    let tries = 0;
    const poll = setInterval(async () => {
      tries++;
      const r = await getTraceability(projectId);
      if (r.data.matrix?.length > 0 || tries > 20) {
        clearInterval(poll);
        setMatrix(r.data.matrix || []);
        setDocReady(r.data.doc_ready || false);
        setGenerating(false);
      }
    }, 2000);
  };

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await downloadTraceability(projectId, project?.project_name, project?.version);
    } catch (e) {
      alert("Download failed: " + e.message);
    } finally {
      setDownloading(false);
    }
  };

  // Unique values for filters
  const sections = ["all", ...new Set(matrix.map((r) => r.section_name))];
  const types    = ["all", ...new Set(matrix.map((r) => r.req_type).filter((t) => t !== "—"))];
  const sources  = ["all", ...new Set(matrix.map((r) => r.source).filter((s) => s !== "—"))];

  const filtered = matrix.filter((row) => {
    if (sectionFilter !== "all" && row.section_name !== sectionFilter) return false;
    if (typeFilter    !== "all" && row.req_type    !== typeFilter)    return false;
    if (sourceFilter  !== "all" && row.source      !== sourceFilter)  return false;
    return true;
  });

  // Stats
  const totalReqs    = new Set(matrix.map((r) => r.req_id).filter((id) => id !== "—")).size;
  const totalSections = new Set(matrix.map((r) => r.section_name)).size;
  const transcriptReqs = matrix.filter((r) => r.source === "Transcript").length;
  const storyReqs      = matrix.filter((r) => r.source === "User Story").length;

  if (loading) return <div className="full-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="flex items-center gap-2">
              <Link2 size={20} color="#2563eb" /> Requirement Traceability Matrix
            </h2>
            <p>Every BRD section traced back to its source requirement and original input.</p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}>
            <ArrowLeft size={14} /> Back
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
        {[
          { label: "Requirements Traced", value: totalReqs, color: "#2563eb" },
          { label: "BRD Sections",        value: totalSections, color: "#06b6d4" },
          { label: "From Transcript",     value: transcriptReqs, color: "#10b981" },
          { label: "From User Stories",   value: storyReqs, color: "#8b5cf6" },
        ].map((s) => (
          <div key={s.label} className="card" style={{ textAlign: "center", padding: "16px" }}>
            <div style={{ fontSize: "1.8rem", fontWeight: 700, color: s.color }}>{s.value}</div>
            <div className="text-xs text-muted mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Actions bar */}
      <div className="card mb-4" style={{ padding: "14px 20px" }}>
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted">
            {matrix.length === 0
              ? "Matrix not yet generated."
              : `${filtered.length} of ${matrix.length} rows shown`}
          </div>
          <div className="flex gap-2">
            <button className="btn btn-secondary btn-sm" onClick={handleGenerate} disabled={generating}>
              <RefreshCw size={13} /> {generating ? "Generating..." : "Regenerate"}
            </button>
            {docReady && (
              <button className="btn btn-primary btn-sm" onClick={handleDownload} disabled={downloading}>
                <Download size={13} /> {downloading ? "Downloading..." : "Download .docx"}
              </button>
            )}
          </div>
        </div>
      </div>

      {matrix.length === 0 && !generating && (
        <div className="card full-center" style={{ minHeight: 200 }}>
          <Link2 size={36} color="#cbd5e1" />
          <div className="text-muted">Matrix not generated yet.</div>
          <div className="text-xs text-muted">It generates automatically when you create the BRD document, or click Regenerate above.</div>
          <button className="btn btn-primary btn-sm mt-3" onClick={handleGenerate}>
            Generate Now
          </button>
        </div>
      )}

      {generating && (
        <div className="card full-center" style={{ minHeight: 160 }}>
          <div className="spinner" />
          <div className="text-muted">Building traceability matrix...</div>
        </div>
      )}

      {matrix.length > 0 && (
        <>
          {/* Filters */}
          <div className="card mb-4" style={{ padding: "12px 16px" }}>
            <div className="flex items-center gap-3" style={{ flexWrap: "wrap" }}>
              <Filter size={14} color="#64748b" />
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted font-semibold">SECTION</span>
                <select className="form-select" style={{ padding: "4px 8px", fontSize: ".8rem", height: "auto" }}
                  value={sectionFilter} onChange={(e) => setSectionFilter(e.target.value)}>
                  {sections.map((s) => <option key={s} value={s}>{s === "all" ? "All Sections" : s}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted font-semibold">TYPE</span>
                <select className="form-select" style={{ padding: "4px 8px", fontSize: ".8rem", height: "auto" }}
                  value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                  {types.map((t) => <option key={t} value={t}>{t === "all" ? "All Types" : t}</option>)}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted font-semibold">SOURCE</span>
                <select className="form-select" style={{ padding: "4px 8px", fontSize: ".8rem", height: "auto" }}
                  value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
                  {sources.map((s) => <option key={s} value={s}>{s === "all" ? "All Sources" : s}</option>)}
                </select>
              </div>
              {(sectionFilter !== "all" || typeFilter !== "all" || sourceFilter !== "all") && (
                <button className="btn btn-sm btn-secondary" onClick={() => {
                  setSectionFilter("all"); setTypeFilter("all"); setSourceFilter("all");
                }}>Clear Filters</button>
              )}
            </div>
          </div>

          {/* Matrix table */}
          <div className="card" style={{ padding: 0, overflow: "hidden" }}>
            <div style={{ overflowX: "auto", maxHeight: 600, overflowY: "auto" }}>
              <table className="data-table" style={{ minWidth: 900 }}>
                <thead style={{ position: "sticky", top: 0, zIndex: 10 }}>
                  <tr>
                    <th style={{ minWidth: 180 }}>BRD Section</th>
                    <th style={{ minWidth: 80 }}>Req ID</th>
                    <th style={{ minWidth: 110 }}>Type</th>
                    <th style={{ minWidth: 320 }}>Requirement</th>
                    <th style={{ minWidth: 100 }}>Source</th>
                    <th style={{ minWidth: 140 }}>Location / Reference</th>
                    <th style={{ minWidth: 100 }}>Speaker</th>
                    <th style={{ minWidth: 100 }}>Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((row, i) => {
                    const tc = TYPE_COLORS[row.req_type] || { bg: "#f1f5f9", text: "#475569" };
                    const sc = SOURCE_COLORS[row.source] || { bg: "#f1f5f9", text: "#475569" };
                    const isNewSection = i === 0 || filtered[i - 1].section_name !== row.section_name;
                    return (
                      <tr key={i} style={{ background: i % 2 === 0 ? "#f8fafc" : "#fff" }}>
                        <td className="font-semibold text-sm" style={{ color: isNewSection ? "#1f3a5f" : "#94a3b8" }}>
                          {isNewSection ? row.section_name : "↳"}
                        </td>
                        <td>
                          <code style={{ fontSize: ".75rem", background: "#f1f5f9", padding: "2px 6px", borderRadius: 4 }}>
                            {row.req_id}
                          </code>
                        </td>
                        <td>
                          {row.req_type !== "—" && (
                            <span style={{
                              background: tc.bg, color: tc.text,
                              padding: "2px 8px", borderRadius: 99, fontSize: ".72rem", fontWeight: 600,
                            }}>
                              {row.req_type}
                            </span>
                          )}
                        </td>
                        <td style={{ fontSize: ".82rem", color: "#374151", lineHeight: 1.5 }}>
                          {row.description}
                        </td>
                        <td>
                          {row.source !== "—" && (
                            <span style={{
                              background: sc.bg, color: sc.text,
                              padding: "2px 8px", borderRadius: 99, fontSize: ".72rem", fontWeight: 600,
                            }}>
                              {row.source}
                            </span>
                          )}
                        </td>
                        <td style={{ fontSize: ".78rem", color: "#64748b", fontFamily: "var(--mono)" }}>
                          {row.source_location}
                        </td>
                        <td style={{ fontSize: ".78rem", color: "#64748b" }}>{row.speaker}</td>
                        <td>
                          {row.priority !== "—" && (
                            <span className={`badge ${
                              row.priority?.toLowerCase().includes("must") ? "badge-blue" :
                              row.priority?.toLowerCase().includes("should") ? "badge-orange" : "badge-grey"
                            }`} style={{ fontSize: ".68rem" }}>
                              {row.priority}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {docReady && (
            <div className="card mt-4" style={{ background: "var(--navy)", border: "none", padding: "16px 24px" }}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold" style={{ color: "#fff" }}>Download Traceability Matrix</div>
                  <div className="text-xs mt-1" style={{ color: "rgba(255,255,255,.55)" }}>
                    Professional Word document with styled table, cover page, and summary stats
                  </div>
                </div>
                <button className="btn" style={{ background: "#06b6d4", color: "#fff" }}
                  onClick={handleDownload} disabled={downloading}>
                  <Download size={15} /> {downloading ? "Preparing..." : "Download .docx"}
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
