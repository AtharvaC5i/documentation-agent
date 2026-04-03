import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  GitBranch, Upload, CheckCircle, XCircle, AlertTriangle,
  ArrowLeft, RefreshCw, Clock, ChevronDown, ChevronRight,
  Plus, Minus, Edit3
} from "lucide-react";
import { getChanges, applyChanges, getVersionHistory, uploadNewTranscript, getProjectStatus } from "../utils/api";
import { usePolling } from "../hooks/usePolling";

const CHANGE_ICONS = {
  new:      { icon: Plus,   color: "#10b981", bg: "#ecfdf5", label: "New" },
  modified: { icon: Edit3,  color: "#f59e0b", bg: "#fffbeb", label: "Modified" },
  removed:  { icon: Minus,  color: "#ef4444", bg: "#fef2f2", label: "Removed" },
  conflict: { icon: AlertTriangle, color: "#7c3aed", bg: "#f5f3ff", label: "Conflict" },
};

export default function LivingBRD() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [changes, setChanges] = useState([]);
  const [changeReport, setChangeReport] = useState("");
  const [version, setVersion] = useState(1);
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState("");
  const [uploading, setUploading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [openChange, setOpenChange] = useState(null);
  const [selected, setSelected] = useState({});
  const [file, setFile] = useState(null);
  const [tab, setTab] = useState("changes"); // changes | history
  const [pollActive, setPollActive] = useState(false);

  useEffect(() => { loadAll(); }, [projectId]);

  const loadAll = async () => {
    try {
      const [c, h, s] = await Promise.all([
        getChanges(projectId),
        getVersionHistory(projectId),
        getProjectStatus(projectId),
      ]);
      setChanges(c.data.pending_changes || []);
      setChangeReport(c.data.change_report || "");
      setVersion(c.data.current_version || 1);
      setHistory(h.data.history || []);
      setStatus(s.data.status);
    } catch {}
  };

  usePolling(async () => {
    const s = await getProjectStatus(projectId);
    setStatus(s.data.status);
    if (s.data.status === "changes_detected" || s.data.status === "error") {
      setPollActive(false);
      await loadAll();
    }
  }, 2500, pollActive);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await uploadNewTranscript(projectId, file);
      setPollActive(true);
      setFile(null);
    } catch (e) {
      alert("Upload failed: " + e.message);
    } finally {
      setUploading(false);
    }
  };

  const toggleSelect = (id) => setSelected((s) => ({ ...s, [id]: !s[id] }));
  const selectAll = () => {
    const s = {};
    changes.forEach((c) => { s[c.change_id] = true; });
    setSelected(s);
  };

  const handleApply = async () => {
    const ids = Object.entries(selected).filter(([, v]) => v).map(([k]) => k);
    if (!ids.length) { alert("Select at least one change to apply."); return; }
    setApplying(true);
    try {
      await applyChanges({ project_id: projectId, approved_change_ids: ids });
      await loadAll();
      setSelected({});
    } catch (e) {
      alert("Apply failed: " + e.message);
    } finally {
      setApplying(false);
    }
  };

  const selectedCount = Object.values(selected).filter(Boolean).length;

  return (
    <div style={{ maxWidth: 860 }}>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="flex items-center gap-2">
              <GitBranch size={22} color="#2563eb" /> Living BRD
            </h2>
            <p>Upload a new meeting transcript to detect what changed and update the BRD.</p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}>
            <ArrowLeft size={14} /> Back
          </button>
        </div>
      </div>

      {/* Version badge */}
      <div className="card mb-6" style={{ padding: "14px 20px" }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <div className="text-xs text-muted font-semibold" style={{ letterSpacing: ".05em" }}>CURRENT VERSION</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#2563eb" }}>v{version}.0</div>
            </div>
            <div style={{ height: 36, width: 1, background: "var(--grey-200)" }} />
            <div>
              <div className="text-xs text-muted font-semibold" style={{ letterSpacing: ".05em" }}>PREVIOUS VERSIONS</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#64748b" }}>{history.length}</div>
            </div>
            <div style={{ height: 36, width: 1, background: "var(--grey-200)" }} />
            <div>
              <div className="text-xs text-muted font-semibold" style={{ letterSpacing: ".05em" }}>PENDING CHANGES</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: changes.length > 0 ? "#f59e0b" : "#10b981" }}>
                {changes.length}
              </div>
            </div>
          </div>
          {status === "complete" && (
            <span className="badge badge-green">BRD Complete</span>
          )}
          {status === "detecting_changes" && (
            <div className="flex items-center gap-2">
              <div className="spinner" style={{ width: 14, height: 14 }} />
              <span className="text-sm text-muted">Detecting changes...</span>
            </div>
          )}
        </div>
      </div>

      {/* Upload new transcript */}
      <div className="card mb-6">
        <div className="card-title mb-1">Upload New Meeting Transcript</div>
        <div className="card-sub">
          Upload a follow-up call recording transcript. The agent will compare it against the current
          requirements pool and identify what's new, changed, or conflicting.
        </div>
        <div className="flex gap-3 items-center">
          <label style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "10px 16px", border: "1.5px dashed var(--grey-300)",
            borderRadius: 8, cursor: "pointer", background: "var(--grey-50)",
            flex: 1, transition: "all .15s",
          }}
            className={file ? "drag" : ""}
          >
            <input type="file" accept=".txt,.docx,.pdf" style={{ display: "none" }}
              onChange={(e) => setFile(e.target.files[0])} />
            <Upload size={16} color={file ? "#2563eb" : "#94a3b8"} />
            <span className="text-sm" style={{ color: file ? "#2563eb" : "#94a3b8" }}>
              {file ? file.name : "Click to select new transcript (.txt, .docx, .pdf)"}
            </span>
          </label>
          <button
            className="btn btn-primary"
            disabled={!file || uploading || status === "detecting_changes"}
            onClick={handleUpload}
          >
            {uploading || status === "detecting_changes"
              ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Detecting...</>
              : <><GitBranch size={15} /> Detect Changes</>}
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display: "flex", borderBottom: "2px solid var(--grey-200)", marginBottom: 20 }}>
        {[
          { key: "changes", label: `Pending Changes (${changes.length})` },
          { key: "history", label: `Version History (${history.length})` },
        ].map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding: "10px 20px", border: "none", background: "none",
            borderBottom: tab === t.key ? "2.5px solid #2563eb" : "2.5px solid transparent",
            marginBottom: -2, color: tab === t.key ? "#2563eb" : "#64748b",
            fontWeight: tab === t.key ? 700 : 500, fontSize: ".875rem", cursor: "pointer",
          }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Changes tab */}
      {tab === "changes" && (
        <>
          {changes.length === 0 && !pollActive && (
            <div className="card full-center" style={{ minHeight: 160 }}>
              <GitBranch size={32} color="#cbd5e1" />
              <div className="text-muted text-sm">No pending changes. Upload a new transcript to detect changes.</div>
            </div>
          )}

          {changes.length > 0 && (
            <>
              {/* Change report */}
              {changeReport && (
                <div className="card mb-4" style={{ background: "var(--blue-pale)", border: "1.5px solid #bfdbfe" }}>
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle size={15} color="#2563eb" />
                    <div className="font-semibold text-sm">Change Summary</div>
                  </div>
                  <div className="text-sm" style={{ lineHeight: 1.7 }}>{changeReport}</div>
                </div>
              )}

              {/* Controls */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex gap-2">
                  <button className="btn btn-sm btn-secondary" onClick={selectAll}>Select All</button>
                  <button className="btn btn-sm btn-secondary" onClick={() => setSelected({})}>None</button>
                </div>
                <button
                  className="btn btn-success"
                  disabled={selectedCount === 0 || applying}
                  onClick={handleApply}
                >
                  {applying
                    ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Applying...</>
                    : <><CheckCircle size={15} /> Apply {selectedCount} Change{selectedCount !== 1 ? "s" : ""} → v{version + 1}</>}
                </button>
              </div>

              {/* Change list */}
              {changes.map((c) => {
                const typeInfo = CHANGE_ICONS[c.change_type] || CHANGE_ICONS.new;
                const Icon = typeInfo.icon;
                const isOpen = openChange === c.change_id;
                return (
                  <div key={c.change_id} className="section-review-card" style={{
                    marginBottom: 8,
                    border: selected[c.change_id] ? "1.5px solid #2563eb" : "1.5px solid var(--grey-200)",
                  }}>
                    <div className="section-review-header" style={{ cursor: "default" }}>
                      <div className="flex items-center gap-3" style={{ flex: 1 }}>
                        <input type="checkbox" checked={!!selected[c.change_id]}
                          onChange={() => toggleSelect(c.change_id)}
                          style={{ width: 16, height: 16, accentColor: "#2563eb", cursor: "pointer" }} />
                        <div style={{
                          background: typeInfo.bg, borderRadius: 6,
                          padding: "4px 8px", display: "flex", alignItems: "center", gap: 5,
                        }}>
                          <Icon size={13} color={typeInfo.color} />
                          <span style={{ fontSize: ".72rem", fontWeight: 700, color: typeInfo.color }}>
                            {typeInfo.label}
                          </span>
                        </div>
                        <div className="flex-1">
                          <div className="text-sm font-semibold">{c.description}</div>
                          {c.affected_sections?.length > 0 && (
                            <div className="text-xs text-muted mt-1">
                              Affects: {c.affected_sections.join(", ")}
                            </div>
                          )}
                        </div>
                        <span className={`badge ${c.impact === "high" ? "badge-red" : c.impact === "medium" ? "badge-orange" : "badge-grey"}`}>
                          {c.impact}
                        </span>
                      </div>
                      <button className="btn-icon" onClick={() => setOpenChange(isOpen ? null : c.change_id)}>
                        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </button>
                    </div>
                    {isOpen && (
                      <div style={{ padding: "12px 20px", background: "var(--grey-50)", borderTop: "1px solid var(--grey-200)" }}>
                        {c.old_text && (
                          <div style={{ marginBottom: 10 }}>
                            <div className="text-xs font-semibold text-muted mb-1">BEFORE</div>
                            <div style={{ background: "#fef2f2", borderRadius: 6, padding: "8px 12px", fontSize: ".85rem", borderLeft: "3px solid #ef4444" }}>
                              {c.old_text}
                            </div>
                          </div>
                        )}
                        {c.new_text && (
                          <div>
                            <div className="text-xs font-semibold text-muted mb-1">AFTER</div>
                            <div style={{ background: "#ecfdf5", borderRadius: 6, padding: "8px 12px", fontSize: ".85rem", borderLeft: "3px solid #10b981" }}>
                              {c.new_text}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </>
          )}
        </>
      )}

      {/* History tab */}
      {tab === "history" && (
        <div className="card">
          <div className="card-title mb-4">Version History</div>
          {history.length === 0 && (
            <div className="text-muted text-sm">No previous versions yet. This will populate after the first BRD update.</div>
          )}
          {history.map((v) => (
            <div key={v.version} style={{ padding: "14px 0", borderBottom: "1px solid var(--grey-100)" }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: "#eff6ff", display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    <Clock size={15} color="#2563eb" />
                  </div>
                  <div>
                    <div className="font-semibold text-sm">v{v.version}.0</div>
                    <div className="text-xs text-muted">{new Date(v.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}</div>
                  </div>
                </div>
                <div className="flex gap-3 text-xs text-muted">
                  <span>{v.requirement_ids?.length || 0} requirements</span>
                  <span>{v.section_names?.length || 0} sections</span>
                </div>
              </div>
              {v.change_summary && (
                <div className="text-xs text-muted mt-2" style={{ paddingLeft: 44 }}>
                  {v.change_summary.slice(0, 200)}{v.change_summary.length > 200 ? "..." : ""}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
