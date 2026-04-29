import React, { useEffect, useState, useCallback, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  CheckCircle, XCircle, RefreshCw, ChevronDown, ChevronRight,
  ThumbsUp, MessageSquare, FileDown, LayoutList, Edit3, Eye, Save
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import {
  getSections, approveSection, regenerateSection,
  generateDocument, getProjectStatus
} from "../utils/api";
import StepIndicator from "../components/StepIndicator";
import QualityBadge from "../components/QualityBadge";

export default function Review() {
  const { projectId } = useParams();
  const navigate      = useNavigate();

  const [sections, setSections]           = useState([]);
  const [open, setOpen]                   = useState({});
  const [editMode, setEditMode]           = useState({});
  const [editedContent, setEditedContent] = useState({});
  const [feedback, setFeedback]           = useState({});
  const [feedbackOpen, setFeedbackOpen]   = useState({});
  const [regenerating, setRegenerating]   = useState({});
  const [saving, setSaving]               = useState({});
  const [generating, setGenerating]       = useState(false);
  const [loading, setLoading]             = useState(true);

  // Use a ref for the polling interval so we can clear it reliably
  const pollRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const load = useCallback(async () => {
    try {
      const r = await getSections(projectId);
      const loaded = r.data.sections || [];
      setSections(loaded);
      setEditedContent((prev) => {
        const next = { ...prev };
        loaded.forEach((s) => { if (!(s.id in next)) next[s.id] = s.content || ""; });
        return next;
      });
    } catch {}
    setLoading(false);
  }, [projectId]);

  useEffect(() => {
    load();
    return () => stopPolling(); // cleanup on unmount
  }, [load, stopPolling]);

  // Poll for regeneration completion
  const startRegenPoll = useCallback(() => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const r = await getSections(projectId);
        const loaded = r.data.sections || [];
        const stillRegen = loaded.some(s => s.status === "regenerating");
        setSections(loaded);
        setEditedContent(prev => {
          const next = { ...prev };
          loaded.forEach(s => { if (!(s.id in next)) next[s.id] = s.content || ""; });
          return next;
        });
        if (!stillRegen) {
          setRegenerating({});
          stopPolling();
        }
      } catch {}
    }, 2500);
  }, [projectId, stopPolling]);

  // Poll for document generation completion — stops itself on success or error
  const startDocPoll = useCallback(() => {
    stopPolling();
    let attempts = 0;
    pollRef.current = setInterval(async () => {
      attempts++;
      try {
        const s = await getProjectStatus(projectId);
        const status = s.data.status;

        if (status === "complete") {
          stopPolling();
          setGenerating(false);
          navigate(`/project/${projectId}/complete`);
          return;
        }

        if (status === "error") {
          stopPolling();
          setGenerating(false);
          alert(`Document generation failed: ${s.data.progress_message || "Unknown error"}`);
          return;
        }

        // Safety timeout — stop polling after 3 minutes regardless
        if (attempts > 72) {
          stopPolling();
          setGenerating(false);
          alert("Document generation is taking longer than expected. Check Terminal 1 for details.");
        }
      } catch {}
    }, 2500);
  }, [projectId, navigate, stopPolling]);

  const toggle = (id) => setOpen(o => ({ ...o, [id]: !o[id] }));

  const toggleEditMode = (id) => setEditMode(e => ({ ...e, [id]: !e[id] }));

  const handleContentChange = (id, value) =>
    setEditedContent(c => ({ ...c, [id]: value }));

  const handleSaveEdit = async (sectionId) => {
    setSaving(s => ({ ...s, [sectionId]: true }));
    try {
      await fetch(`/api/projects/${projectId}/save-section-content`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: projectId, section_id: sectionId, content: editedContent[sectionId] }),
      });
      setSections(ss => ss.map(s =>
        s.id === sectionId ? { ...s, content: editedContent[sectionId], status: "edited" } : s
      ));
      setEditMode(e => ({ ...e, [sectionId]: false }));
    } catch {
      setSections(ss => ss.map(s =>
        s.id === sectionId ? { ...s, content: editedContent[sectionId], status: "edited" } : s
      ));
      setEditMode(e => ({ ...e, [sectionId]: false }));
    }
    setSaving(s => ({ ...s, [sectionId]: false }));
  };

  const handleApprove = async (sectionId, approved) => {
    await approveSection({ project_id: projectId, section_id: sectionId, approved });
    setSections(ss => ss.map(s =>
      s.id === sectionId ? { ...s, approved, status: approved ? "approved" : "needs_revision" } : s
    ));
  };

  const handleApproveAll = async () => {
    for (const s of sections) {
      await approveSection({ project_id: projectId, section_id: s.id, approved: true });
    }
    setSections(ss => ss.map(s => ({ ...s, approved: true, status: "approved" })));
  };

  const handleRegenerate = async (sectionId) => {
    const fb = feedback[sectionId] || "";
    setRegenerating(r => ({ ...r, [sectionId]: true }));
    setFeedback(f => ({ ...f, [sectionId]: "" }));
    setFeedbackOpen(f => ({ ...f, [sectionId]: false }));
    await regenerateSection({ project_id: projectId, section_id: sectionId, feedback: fb });
    startRegenPoll();
  };

  const handleGenerateDoc = async () => {
    if (!allApproved) {
      alert(`Please approve all ${sections.length} sections before generating. Currently ${approvedCount} of ${sections.length} approved.`);
      return;
    }
    setGenerating(true);
    try {
      await generateDocument(projectId);
      startDocPoll();
    } catch (e) {
      setGenerating(false);
      alert(`Failed to start document generation: ${e.message}`);
    }
  };

  const approvedCount = sections.filter(s => s.approved).length;
  const allApproved   = approvedCount === sections.length && sections.length > 0;

  if (loading) return (
    <div className="full-center">
      <div className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} />
    </div>
  );

  return (
    <div>
      <StepIndicator current="review" />

      <div className="page-header">
        <h2>Human Review</h2>
        <p>Review, edit, approve or request AI regeneration. All sections must be approved before generating.</p>
      </div>

      {/* Summary bar */}
      <div className="card mb-6" style={{ padding: "14px 20px" }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <span className="font-bold" style={{ fontSize: "1.3rem", color: "#6ee7b7" }}>
                {approvedCount}
              </span>
              <span className="text-muted text-sm"> / {sections.length} approved</span>
            </div>
            <div className="progress-track" style={{ width: 140 }}>
              <div className="progress-fill" style={{ width: `${sections.length > 0 ? (approvedCount / sections.length) * 100 : 0}%` }} />
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/project/${projectId}/pipeline`)}>
              <LayoutList size={13} /> Pipeline Inspector
            </button>
            {!allApproved && (
              <button className="btn btn-success btn-sm" onClick={handleApproveAll}>
                <ThumbsUp size={13} /> Approve All
              </button>
            )}
            <button className="btn btn-primary" disabled={generating} onClick={handleGenerateDoc}>
              {generating
                ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Generating BRD...</>
                : <><FileDown size={14} /> Generate BRD</>}
            </button>
          </div>
        </div>
      </div>

      {/* Generating overlay message */}
      {generating && (
        <div className="alert alert-info mb-4">
          <div className="spinner" style={{ width: 14, height: 14, flexShrink: 0 }} />
          <div className="text-sm">
            Building your BRD document. This takes 10-30 seconds. Do not close this page —
            you will be redirected automatically when it is ready.
          </div>
        </div>
      )}

      {/* Section cards */}
      {sections.map((section, idx) => {
        const isOpen    = !!open[section.id];
        const isEditing = !!editMode[section.id];
        const isSaving  = !!saving[section.id];
        const isRegen   = !!regenerating[section.id];
        const hasEdits  = editedContent[section.id] !== section.content && !!editedContent[section.id];

        const borderColor = section.approved
          ? "rgba(16,185,129,.3)"
          : section.status === "needs_revision"
          ? "rgba(239,68,68,.3)"
          : "var(--border, rgba(255,255,255,.07))";

        return (
          <div key={section.id} className="section-review-card"
            style={{ marginBottom: 10, borderColor, transition: "border-color .2s" }}>

            {/* Header */}
            <div className="section-review-header" onClick={() => toggle(section.id)}>
              <div className="flex items-center gap-3">
                <span className="text-muted text-sm"
                  style={{ minWidth: 22, fontFamily: "var(--mono, monospace)", fontSize: ".72rem" }}>
                  {String(idx + 1).padStart(2, "0")}
                </span>
                {section.approved
                  ? <CheckCircle size={16} color="#6ee7b7" />
                  : section.status === "needs_revision"
                  ? <XCircle size={16} color="#fca5a5" />
                  : <div style={{ width: 16, height: 16, borderRadius: "50%", border: "1.5px solid rgba(255,255,255,.15)" }} />}
                <span className="font-semibold" style={{ fontSize: ".9rem" }}>{section.name}</span>
                <QualityBadge score={section.quality_score || 0} />
                {section.status === "regenerated" && <span className="badge badge-blue">Regenerated</span>}
                {section.status === "edited"      && <span className="badge badge-purple">Edited</span>}
                {section.status === "failed"      && <span className="badge badge-red">Failed</span>}
                {section.status === "regenerating"&& <span className="badge badge-orange">Regenerating...</span>}
                {hasEdits && !isEditing           && <span className="badge badge-orange">Unsaved</span>}
                {section.req_count > 0 && <span className="text-xs text-muted">{section.req_count} reqs</span>}
                {section.word_count > 0 && (
                  <span className="text-xs" style={{ color: section.word_count > 600 ? "#fcd34d" : "var(--text-muted)" }}>
                    {section.word_count}w
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {section.sources?.map(src => (
                  <span key={src} className="badge badge-grey" style={{ fontSize: ".65rem" }}>{src}</span>
                ))}
                {isOpen ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
              </div>
            </div>

            {/* Body */}
            {isOpen && (
              <div style={{ padding: "18px 22px" }}>

                {/* Edit / Preview toggle */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex gap-2">
                    <button className={`btn btn-sm ${!isEditing ? "btn-primary" : "btn-secondary"}`}
                      style={{ pointerEvents: "none", opacity: !isEditing ? 1 : 0.5 }}>
                      <Eye size={12} /> Preview
                    </button>
                    <button className={`btn btn-sm ${isEditing ? "btn-primary" : "btn-secondary"}`}
                      onClick={e => { e.stopPropagation(); toggleEditMode(section.id); }}>
                      <Edit3 size={12} /> {isEditing ? "Editing" : "Edit"}
                    </button>
                  </div>
                  {isEditing && (
                    <div className="flex gap-2">
                      <button className="btn btn-sm btn-secondary" onClick={e => {
                        e.stopPropagation();
                        setEditedContent(c => ({ ...c, [section.id]: section.content || "" }));
                        setEditMode(em => ({ ...em, [section.id]: false }));
                      }}>Cancel</button>
                      <button className="btn btn-sm btn-success" disabled={isSaving}
                        onClick={e => { e.stopPropagation(); handleSaveEdit(section.id); }}>
                        {isSaving
                          ? <><div className="spinner" style={{ width: 12, height: 12 }} /> Saving...</>
                          : <><Save size={12} /> Save Edits</>}
                      </button>
                    </div>
                  )}
                </div>

                {/* Content */}
                {isEditing ? (
                  <div>
                    <textarea className="section-editor"
                      value={editedContent[section.id] || ""}
                      onChange={e => handleContentChange(section.id, e.target.value)}
                      placeholder="Edit section content. Supports Markdown."
                      onClick={e => e.stopPropagation()}
                      spellCheck={false}
                    />
                    <div className="text-xs text-muted mt-2 flex justify-between">
                      <span>Markdown: ## Heading  **bold**  *italic*  | table |  - bullet</span>
                      <span>{(editedContent[section.id] || "").split(/\s+/).filter(Boolean).length} words</span>
                    </div>
                  </div>
                ) : (
                  <div style={{
                    background: "var(--elevated, #1a2236)", borderRadius: 6,
                    padding: "14px 18px", marginBottom: 14, maxHeight: 520, overflowY: "auto",
                    border: "1px solid var(--border, rgba(255,255,255,.07))",
                  }}>
                    <div className="md-content">
                      <ReactMarkdown>
                        {editedContent[section.id] || section.content || "*No content.*"}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                {/* Source req IDs */}
                {!isEditing && section.source_req_ids?.length > 0 && (
                  <div className="mb-4">
                    <div className="text-xs font-semibold text-muted mb-2" style={{ letterSpacing: ".06em" }}>
                      SOURCE REQUIREMENTS
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                      {section.source_req_ids.map(id => (
                        <code key={id} style={{
                          background: "var(--elevated, #1a2236)", border: "1px solid var(--border, rgba(255,255,255,.07))",
                          padding: "1px 7px", borderRadius: 4, fontSize: ".72rem",
                          color: "#60a5fa", fontFamily: "monospace",
                        }}>{id}</code>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2" style={{ flexWrap: "wrap" }}>
                  {!section.approved && (
                    <button className="btn btn-success btn-sm" onClick={() => handleApprove(section.id, true)}>
                      <CheckCircle size={13} /> Approve
                    </button>
                  )}
                  {section.approved && (
                    <button className="btn btn-secondary btn-sm" onClick={() => handleApprove(section.id, false)}>
                      <XCircle size={13} /> Unapprove
                    </button>
                  )}
                  <button className="btn btn-secondary btn-sm"
                    onClick={() => setFeedbackOpen(f => ({ ...f, [section.id]: !f[section.id] }))}>
                    <MessageSquare size={13} /> {feedbackOpen[section.id] ? "Hide" : "Request AI Rewrite"}
                  </button>
                </div>

                {/* Feedback */}
                {feedbackOpen[section.id] && (
                  <div style={{
                    marginTop: 12, background: "rgba(99,102,241,.06)",
                    border: "1px solid rgba(99,102,241,.2)", borderRadius: 6, padding: 14,
                  }}>
                    <div className="text-sm font-semibold mb-2" style={{ color: "#60a5fa" }}>
                      What should the AI change?
                    </div>
                    <textarea className="form-textarea" style={{ minHeight: 68, marginBottom: 10 }}
                      placeholder='e.g. "Add more detail about Bajaj Finance EMI specifics"'
                      value={feedback[section.id] || ""}
                      onChange={e => setFeedback(f => ({ ...f, [section.id]: e.target.value }))}
                    />
                    <button className="btn btn-primary btn-sm"
                      disabled={isRegen || !feedback[section.id]?.trim()}
                      onClick={() => handleRegenerate(section.id)}>
                      {isRegen
                        ? <><div className="spinner" style={{ width: 12, height: 12 }} /> Regenerating...</>
                        : <><RefreshCw size={12} /> Regenerate with AI</>}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
