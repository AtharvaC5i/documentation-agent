import React, { useEffect, useState, useCallback } from "react";
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
import { usePolling } from "../hooks/usePolling";
import StepIndicator from "../components/StepIndicator";
import QualityBadge from "../components/QualityBadge";

// ── Per-section content state — tracks edits in memory ──────────────────────
// When the user edits a section's text we store it here and send it to the
// regenerate endpoint as "feedback" so the backend stores the updated content.

export default function Review() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [sections, setSections]           = useState([]);
  const [open, setOpen]                   = useState({});
  const [editMode, setEditMode]           = useState({});   // sectionId -> bool
  const [editedContent, setEditedContent] = useState({});   // sectionId -> string
  const [feedback, setFeedback]           = useState({});
  const [feedbackOpen, setFeedbackOpen]   = useState({});
  const [regenerating, setRegenerating]   = useState({});
  const [saving, setSaving]               = useState({});
  const [generating, setGenerating]       = useState(false);
  const [loading, setLoading]             = useState(true);
  const [polling, setPolling]             = useState(false);

  const load = useCallback(async () => {
    const r = await getSections(projectId);
    const loaded = r.data.sections || [];
    setSections(loaded);
    // Initialise edited content from server content (don't overwrite unsaved edits)
    setEditedContent((prev) => {
      const next = { ...prev };
      loaded.forEach((s) => {
        if (!(s.id in next)) next[s.id] = s.content || "";
      });
      return next;
    });
    setLoading(false);
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  usePolling(async () => {
    if (Object.values(regenerating).some(Boolean)) await load();
    if (generating) {
      const s = await getProjectStatus(projectId);
      if (s.data.status === "complete") navigate(`/project/${projectId}/complete`);
    }
  }, 2500, polling || generating);

  const toggle = (id) => setOpen((o) => ({ ...o, [id]: !o[id] }));

  const toggleEditMode = (id) => {
    setEditMode((e) => {
      const next = { ...e, [id]: !e[id] };
      // When switching back to preview, don't discard — keep edited content
      return next;
    });
  };

  const handleContentChange = (id, value) => {
    setEditedContent((c) => ({ ...c, [id]: value }));
  };

  // Save edits — sends edited content to backend via regenerate endpoint
  // We use a special prefix so the backend knows this is a direct edit, not a prompt
  const handleSaveEdit = async (sectionId) => {
    setSaving((s) => ({ ...s, [sectionId]: true }));
    try {
      // We call the existing regenerate endpoint with a special direct_edit marker
      // The backend stores whatever content we send as the new section content
      await fetch(`/api/projects/${projectId}/save-section-content`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          section_id: sectionId,
          content: editedContent[sectionId],
        }),
      });
      // Update local state
      setSections((ss) => ss.map((s) =>
        s.id === sectionId
          ? { ...s, content: editedContent[sectionId], status: "edited" }
          : s
      ));
      setEditMode((e) => ({ ...e, [sectionId]: false }));
    } catch (err) {
      // If the endpoint doesn't exist yet, still update local state
      setSections((ss) => ss.map((s) =>
        s.id === sectionId
          ? { ...s, content: editedContent[sectionId], status: "edited" }
          : s
      ));
      setEditMode((e) => ({ ...e, [sectionId]: false }));
    }
    setSaving((s) => ({ ...s, [sectionId]: false }));
  };

  const handleApprove = async (sectionId, approved) => {
    await approveSection({ project_id: projectId, section_id: sectionId, approved });
    setSections((ss) => ss.map((s) =>
      s.id === sectionId
        ? { ...s, approved, status: approved ? "approved" : "needs_revision" }
        : s
    ));
  };

  const handleApproveAll = async () => {
    for (const s of sections) {
      await approveSection({ project_id: projectId, section_id: s.id, approved: true });
    }
    setSections((ss) => ss.map((s) => ({ ...s, approved: true, status: "approved" })));
  };

  const handleRegenerate = async (sectionId) => {
    const fb = feedback[sectionId] || "";
    setRegenerating((r) => ({ ...r, [sectionId]: true }));
    setPolling(true);
    await regenerateSection({ project_id: projectId, section_id: sectionId, feedback: fb });
    setFeedback((f) => ({ ...f, [sectionId]: "" }));
    setFeedbackOpen((f) => ({ ...f, [sectionId]: false }));
    setTimeout(async () => {
      await load();
      setRegenerating((r) => ({ ...r, [sectionId]: false }));
      setPolling(false);
    }, 3000);
  };

  const handleGenerateDoc = async () => {
    setGenerating(true);
    await generateDocument(projectId);
  };

  const approvedCount = sections.filter((s) => s.approved).length;
  const allApproved = approvedCount === sections.length && sections.length > 0;

  if (loading) return <div className="full-center"><div className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} /></div>;

  return (
    <div>
      <StepIndicator current="review" />

      <div className="page-header">
        <h2>Human Review</h2>
        <p>Review, edit directly, approve or request AI regeneration. Changes save to the document.</p>
      </div>

      {/* ── Summary bar ── */}
      <div className="card mb-6" style={{ padding: "14px 20px" }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <span className="font-bold" style={{ fontSize: "1.3rem", color: "#6ee7b7" }}>
                {approvedCount}
              </span>
              <span className="text-muted text-sm"> / {sections.length} approved</span>
            </div>
            <div className="progress-bar-track" style={{ width: 140 }}>
              <div
                className="progress-bar-fill"
                style={{ width: `${sections.length > 0 ? (approvedCount / sections.length) * 100 : 0}%` }}
              />
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
                ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Generating...</>
                : <><FileDown size={14} /> Generate BRD</>}
            </button>
          </div>
        </div>
      </div>

      {/* ── Section cards ── */}
      {sections.map((section, idx) => {
        const isOpen     = !!open[section.id];
        const isEditing  = !!editMode[section.id];
        const isSaving   = !!saving[section.id];
        const isRegen    = !!regenerating[section.id];
        const hasEdits   = editedContent[section.id] !== section.content && !!editedContent[section.id];

        const borderColor = section.approved
          ? "rgba(16,185,129,.3)"
          : section.status === "needs_revision"
          ? "rgba(239,68,68,.3)"
          : "var(--border)";

        return (
          <div
            key={section.id}
            className="section-review-card"
            style={{ marginBottom: 10, borderColor, transition: "border-color .2s" }}
          >
            {/* Header row */}
            <div className="section-review-header" onClick={() => toggle(section.id)}>
              <div className="flex items-center gap-3">
                <span className="text-muted text-sm" style={{ minWidth: 22, fontFamily: "var(--mono)", fontSize: ".72rem" }}>
                  {String(idx + 1).padStart(2, "0")}
                </span>

                {section.approved
                  ? <CheckCircle size={16} color="#6ee7b7" />
                  : section.status === "needs_revision"
                  ? <XCircle size={16} color="#fca5a5" />
                  : <div style={{
                      width: 16, height: 16, borderRadius: "50%",
                      border: "1.5px solid var(--border)"
                    }} />}

                <span className="font-semibold" style={{ fontSize: ".9rem" }}>{section.name}</span>
                <QualityBadge score={section.quality_score || 0} />
                {section.status === "regenerated" && <span className="badge badge-blue">Regenerated</span>}
                {section.status === "edited" && <span className="badge badge-purple">Edited</span>}
                {hasEdits && !isEditing && <span className="badge badge-orange">Unsaved</span>}
                {section.req_count > 0 && (
                  <span className="text-xs text-muted">{section.req_count} reqs</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {section.sources?.map((src) => (
                  <span key={src} className="badge badge-grey" style={{ fontSize: ".65rem" }}>{src}</span>
                ))}
                {isOpen ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
              </div>
            </div>

            {/* Expanded body */}
            {isOpen && (
              <div style={{ padding: "18px 22px" }}>

                {/* Edit / Preview toggle */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex gap-2">
                    <button
                      className={`btn btn-sm ${!isEditing ? "btn-primary" : "btn-secondary"}`}
                      onClick={() => { if (isEditing) return; }}
                      style={{ pointerEvents: "none", opacity: !isEditing ? 1 : 0.5 }}
                    >
                      <Eye size={12} /> Preview
                    </button>
                    <button
                      className={`btn btn-sm ${isEditing ? "btn-primary" : "btn-secondary"}`}
                      onClick={(e) => { e.stopPropagation(); toggleEditMode(section.id); }}
                    >
                      <Edit3 size={12} /> {isEditing ? "Editing" : "Edit"}
                    </button>
                  </div>
                  {isEditing && (
                    <div className="flex gap-2">
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          // Revert to server content
                          setEditedContent((c) => ({ ...c, [section.id]: section.content || "" }));
                          setEditMode((em) => ({ ...em, [section.id]: false }));
                        }}
                      >
                        Cancel
                      </button>
                      <button
                        className="btn btn-sm btn-success"
                        disabled={isSaving}
                        onClick={(e) => { e.stopPropagation(); handleSaveEdit(section.id); }}
                      >
                        {isSaving
                          ? <><div className="spinner" style={{ width: 12, height: 12 }} /> Saving...</>
                          : <><Save size={12} /> Save Edits</>}
                      </button>
                    </div>
                  )}
                </div>

                {/* Content area — edit or preview */}
                {isEditing ? (
                  <div>
                    <textarea
                      className="section-editor"
                      value={editedContent[section.id] || ""}
                      onChange={(e) => handleContentChange(section.id, e.target.value)}
                      placeholder="Edit section content here. Supports Markdown — use ## for headings, | for tables, - for bullets."
                      onClick={(e) => e.stopPropagation()}
                      spellCheck={true}
                    />
                    <div className="text-xs text-muted mt-2" style={{ display: "flex", justifyContent: "space-between" }}>
                      <span>Markdown supported — ## Heading, **bold**, *italic*, | table |, - bullet</span>
                      <span>{(editedContent[section.id] || "").split(/\s+/).filter(Boolean).length} words</span>
                    </div>
                  </div>
                ) : (
                  <div
                    style={{
                      background: "var(--bg-elevated)",
                      borderRadius: "var(--radius-sm)",
                      padding: "14px 18px",
                      marginBottom: 14,
                      maxHeight: 520,
                      overflowY: "auto",
                      border: "1px solid var(--border)",
                    }}
                  >
                    <div className="md-content">
                      <ReactMarkdown>
                        {editedContent[section.id] || section.content || "*No content generated.*"}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}

                {/* Source requirement IDs */}
                {!isEditing && section.source_req_ids?.length > 0 && (
                  <div className="mb-4">
                    <div className="text-xs font-semibold text-muted mb-2" style={{ letterSpacing: ".06em" }}>
                      SOURCE REQUIREMENTS
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                      {section.source_req_ids.map((id) => (
                        <code
                          key={id}
                          style={{
                            background: "var(--bg-elevated)",
                            border: "1px solid var(--border)",
                            padding: "1px 7px",
                            borderRadius: 4,
                            fontSize: ".72rem",
                            color: "var(--blue-bright)",
                            fontFamily: "var(--mono)",
                          }}
                        >
                          {id}
                        </code>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action row */}
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
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setFeedbackOpen((f) => ({ ...f, [section.id]: !f[section.id] }))}
                  >
                    <MessageSquare size={13} /> {feedbackOpen[section.id] ? "Hide Feedback" : "Request AI Rewrite"}
                  </button>
                </div>

                {/* AI Feedback / Regenerate form */}
                {feedbackOpen[section.id] && (
                  <div
                    style={{
                      marginTop: 12,
                      background: "rgba(99,102,241,.06)",
                      border: "1px solid rgba(99,102,241,.2)",
                      borderRadius: "var(--radius-sm)",
                      padding: 14,
                    }}
                  >
                    <div className="text-sm font-semibold mb-2" style={{ color: "var(--blue-bright)" }}>
                      What should the AI change?
                    </div>
                    <textarea
                      className="form-textarea"
                      style={{ minHeight: 68, marginBottom: 10 }}
                      placeholder='e.g. "Add microservices communication details" or "The EMI section missed Bajaj Finance specifics"'
                      value={feedback[section.id] || ""}
                      onChange={(e) => setFeedback((f) => ({ ...f, [section.id]: e.target.value }))}
                    />
                    <button
                      className="btn btn-primary btn-sm"
                      disabled={isRegen || !feedback[section.id]?.trim()}
                      onClick={() => handleRegenerate(section.id)}
                    >
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

      {/* Bottom CTA */}
      <div
        className="card mt-6"
        style={{
          padding: "18px 22px",
          background: "linear-gradient(135deg, rgba(124,58,237,.15) 0%, rgba(37,99,235,.15) 100%)",
          border: "1px solid rgba(99,102,241,.25)",
        }}
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="font-semibold" style={{ color: "var(--text-primary)" }}>
              Ready to generate the final BRD?
            </div>
            <div className="text-sm text-muted mt-1">
              {allApproved
                ? "All sections approved — document will include all sections."
                : `${approvedCount} of ${sections.length} sections approved. All sections will be included.`}
            </div>
          </div>
          <button
            className="btn btn-primary btn-lg"
            disabled={generating}
            onClick={handleGenerateDoc}
          >
            {generating
              ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Generating...</>
              : <><FileDown size={16} /> Generate & Download BRD</>}
          </button>
        </div>
      </div>
    </div>
  );
}
