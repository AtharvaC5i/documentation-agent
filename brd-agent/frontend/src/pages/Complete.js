import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  CheckCircle, Download, FileText, BarChart2, Plus,
  RefreshCw, Loader, Mail, Link2, GitBranch
} from "lucide-react";
import { getSections, listProjects, generateFollowupEmail, getTraceability } from "../utils/api";
import { downloadBRD, downloadTraceability } from "../utils/api";
import StepIndicator from "../components/StepIndicator";
import QualityBadge from "../components/QualityBadge";

export default function Complete() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [sections, setSections]         = useState([]);
  const [project, setProject]           = useState(null);
  const [downloading, setDownloading]   = useState(false);
  const [dlTrace, setDlTrace]           = useState(false);
  const [downloadError, setDownloadError] = useState("");
  const [traceReady, setTraceReady]     = useState(false);
  const [emailStarted, setEmailStarted] = useState(false);

  useEffect(() => {
    getSections(projectId)
      .then((r) => setSections(r.data.sections || []))
      .catch(() => {});
    listProjects()
      .then((r) => {
        const p = (r.data.projects || []).find((p) => p.id === projectId);
        if (p) setProject(p);
      })
      .catch(() => {});
    getTraceability(projectId)
      .then((r) => setTraceReady(r.data.doc_ready || false))
      .catch(() => {});
  }, [projectId]);

  const handleDownload = async () => {
    setDownloading(true); setDownloadError("");
    try { await downloadBRD(projectId, project?.project_name, project?.version); }
    catch (e) { setDownloadError(e.message); }
    finally { setDownloading(false); }
  };

  const handleTraceDownload = async () => {
    setDlTrace(true);
    try { await downloadTraceability(projectId, project?.project_name, project?.version); }
    catch (e) { alert("Traceability download failed: " + e.message); }
    finally { setDlTrace(false); }
  };

  const handleGenerateEmail = async () => {
    setEmailStarted(true);
    await generateFollowupEmail(projectId);
    navigate(`/project/${projectId}/followup-email`);
  };

  const avgQuality = sections.length > 0
    ? sections.reduce((a, s) => a + (s.quality_score || 0), 0) / sections.length
    : 0;
  const approvedCount    = sections.filter((s) => s.approved).length;
  const regeneratedCount = sections.filter((s) => s.status === "regenerated").length;
  const totalReqs        = sections.reduce((a, s) => a + (s.req_count || 0), 0);

  return (
    <div style={{ maxWidth: 720 }}>
      <StepIndicator current="complete" />

      {/* Hero */}
      <div className="card mb-6" style={{
        background: "linear-gradient(135deg, #0f1f3d 0%, #1a3259 100%)",
        border: "none", padding: "40px 36px", textAlign: "center",
      }}>
        <div style={{
          width: 64, height: 64, borderRadius: "50%", background: "#10b981",
          display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px",
        }}>
          <CheckCircle size={32} color="#fff" />
        </div>
        <h2 style={{ color: "#fff", fontSize: "1.6rem", fontWeight: 700, marginBottom: 4 }}>
          BRD Generated Successfully
        </h2>
        <p style={{ color: "rgba(255,255,255,.6)", marginBottom: 8, fontSize: ".9rem" }}>
          {project?.project_name} · {project?.client_name} · v{project?.version || 1}.0
        </p>
        <p style={{ color: "rgba(255,255,255,.5)", marginBottom: 24, fontSize: ".8rem" }}>
          Your Business Requirements Document is ready for download.
        </p>

        <button
          className="btn btn-lg"
          style={{ background: "#06b6d4", color: "#fff", display: "inline-flex", marginBottom: 8 }}
          onClick={handleDownload}
          disabled={downloading}
        >
          {downloading
            ? <><Loader size={18} style={{ animation: "spin .8s linear infinite" }} /> Preparing...</>
            : <><Download size={18} /> Download BRD (.docx)</>}
        </button>

        {downloadError && (
          <div style={{
            marginTop: 10, background: "rgba(239,68,68,.15)",
            border: "1px solid rgba(239,68,68,.4)", borderRadius: 8,
            padding: "8px 14px", color: "#fca5a5", fontSize: ".82rem",
          }}>
            {downloadError}
          </div>
        )}
      </div>

      {/* Generation report */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart2 size={17} color="#2563eb" />
          <div className="card-title" style={{ marginBottom: 0 }}>Generation Report</div>
        </div>
        <div className="grid-2">
          {[
            { label: "Sections Generated",  value: sections.length,                     color: "#2563eb" },
            { label: "Avg Quality Score",   value: `${Math.round(avgQuality * 100)}%`,  color: avgQuality >= .8 ? "#10b981" : avgQuality >= .6 ? "#f59e0b" : "#ef4444" },
            { label: "Sections Approved",   value: approvedCount,                        color: "#10b981" },
            { label: "Auto-Regenerated",    value: regeneratedCount,                     color: "#f59e0b" },
            { label: "Requirements Used",   value: totalReqs,                            color: "#06b6d4" },
            { label: "BRD Version",         value: `v${project?.version || 1}.0`,        color: "#64748b" },
          ].map((stat) => (
            <div key={stat.label} className="flex items-center justify-between"
              style={{ padding: "10px 0", borderBottom: "1px solid var(--grey-100)" }}>
              <span className="text-sm text-muted">{stat.label}</span>
              <span className="font-bold" style={{ color: stat.color }}>{stat.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Three feature cards */}
      <div className="card mb-4" style={{ background: "#f8fafc" }}>
        <div className="card-title mb-4">Additional Deliverables</div>

        {/* Traceability */}
        <div style={{ padding: "14px 0", borderBottom: "1px solid var(--grey-200)" }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div style={{ background: "#ede9fe", borderRadius: 8, padding: 8 }}>
                <Link2 size={18} color="#7c3aed" />
              </div>
              <div>
                <div className="font-semibold text-sm">Requirement Traceability Matrix</div>
                <div className="text-xs text-muted mt-1">
                  {traceReady
                    ? "Every BRD section traced to its source requirement and meeting timestamp"
                    : "Auto-generated alongside your BRD — links sections back to source requirements"}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <button className="btn btn-sm btn-secondary"
                onClick={() => navigate(`/project/${projectId}/traceability`)}>
                View Matrix
              </button>
              {traceReady && (
                <button className="btn btn-sm btn-outline" onClick={handleTraceDownload} disabled={dlTrace}>
                  <Download size={13} /> {dlTrace ? "..." : ".docx"}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Follow-up email */}
        <div style={{ padding: "14px 0", borderBottom: "1px solid var(--grey-200)" }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div style={{ background: "#fef3c7", borderRadius: 8, padding: 8 }}>
                <Mail size={18} color="#d97706" />
              </div>
              <div>
                <div className="font-semibold text-sm">Follow-Up Email</div>
                <div className="text-xs text-muted mt-1">
                  AI-drafted client email with targeted questions for every coverage gap
                </div>
              </div>
            </div>
            <button
              className="btn btn-sm btn-secondary"
              onClick={handleGenerateEmail}
              disabled={emailStarted}
            >
              {emailStarted
                ? <><div className="spinner" style={{ width: 12, height: 12 }} /> Drafting...</>
                : <><Mail size={13} /> Draft Email</>}
            </button>
          </div>
        </div>

        {/* Living BRD */}
        <div style={{ padding: "14px 0" }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div style={{ background: "#dcfce7", borderRadius: 8, padding: 8 }}>
                <GitBranch size={18} color="#16a34a" />
              </div>
              <div>
                <div className="font-semibold text-sm">Living BRD — Upload New Transcript</div>
                <div className="text-xs text-muted mt-1">
                  Got a follow-up call? Upload the new transcript to detect changes and update the BRD
                </div>
              </div>
            </div>
            <button className="btn btn-sm btn-secondary"
              onClick={() => navigate(`/project/${projectId}/living-brd`)}>
              <GitBranch size={13} /> Update BRD
            </button>
          </div>
        </div>
      </div>

      {/* Section quality */}
      <div className="card mb-6">
        <div className="card-title mb-4">Section Quality Breakdown</div>
        <table className="data-table">
          <thead>
            <tr><th>Section</th><th>Quality</th><th>Reqs Used</th><th>Status</th></tr>
          </thead>
          <tbody>
            {sections.map((s) => (
              <tr key={s.id}>
                <td className="text-sm font-semibold">{s.name}</td>
                <td><QualityBadge score={s.quality_score || 0} /></td>
                <td className="text-sm text-muted">{s.req_count}</td>
                <td>
                  {s.approved
                    ? <span className="badge badge-green">Approved</span>
                    : <span className="badge badge-orange">Pending</span>}
                  {s.status === "regenerated" &&
                    <span className="badge badge-blue" style={{ marginLeft: 4 }}>Regenerated</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Navigation */}
      <div className="card">
        <div className="card-title mb-4">Next Steps</div>
        <div className="flex gap-3" style={{ flexWrap: "wrap" }}>
          <button className="btn btn-primary" onClick={handleDownload} disabled={downloading}>
            <Download size={15} /> Download BRD
          </button>
          <button className="btn btn-secondary" onClick={() => navigate(`/project/${projectId}/review`)}>
            <RefreshCw size={15} /> Back to Review
          </button>
          <button className="btn btn-secondary" onClick={() => navigate("/new-project")}>
            <Plus size={15} /> New Project
          </button>
          <button className="btn btn-secondary" onClick={() => navigate("/")}>
            <FileText size={15} /> Dashboard
          </button>
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
