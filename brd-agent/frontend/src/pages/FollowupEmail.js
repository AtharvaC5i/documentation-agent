import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Mail, RefreshCw, Copy, CheckCircle, AlertTriangle, ArrowLeft, Send } from "lucide-react";
import { getFollowupEmail, generateFollowupEmail, getConflicts } from "../utils/api";

export default function FollowupEmail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [meta, setMeta] = useState({ gap_count: 0, conflict_count: 0 });
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [edited, setEdited] = useState("");

  useEffect(() => {
    loadEmail();
  }, [projectId]);

  const loadEmail = async () => {
    setLoading(true);
    try {
      const r = await getFollowupEmail(projectId);
      setEmail(r.data.email_draft || "");
      setEdited(r.data.email_draft || "");
      setMeta({ gap_count: r.data.gap_count || 0, conflict_count: r.data.conflict_count || 0 });
    } catch {}
    setLoading(false);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateFollowupEmail(projectId);
      // Poll until ready
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        const r = await getFollowupEmail(projectId);
        if (r.data.email_draft || attempts > 30) {
          clearInterval(poll);
          setEmail(r.data.email_draft || "");
          setEdited(r.data.email_draft || "");
          setMeta({ gap_count: r.data.gap_count || 0, conflict_count: r.data.conflict_count || 0 });
          setGenerating(false);
        }
      }, 2000);
    } catch {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(edited);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const openMailClient = () => {
    // Extract subject line from email if present
    const subjectMatch = edited.match(/Subject:\s*(.+)/i);
    const subject = subjectMatch ? subjectMatch[1].trim() : "BRD Follow-Up — Clarifications Required";
    const body = edited.replace(/Subject:.+\n?/i, "").trim();
    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  if (loading) return <div className="full-center"><div className="spinner" /></div>;

  return (
    <div style={{ maxWidth: 800 }}>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h2>Follow-Up Email Generator</h2>
            <p>Auto-drafted client email with targeted questions for every coverage gap.</p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}>
            <ArrowLeft size={14} /> Back
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid-2 mb-6">
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: "#f59e0b" }}>{meta.gap_count}</div>
          <div className="text-sm text-muted mt-1">Coverage Gaps Driving Questions</div>
        </div>
        <div className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "1.8rem", fontWeight: 700, color: meta.conflict_count > 0 ? "#ef4444" : "#10b981" }}>
            {meta.conflict_count}
          </div>
          <div className="text-sm text-muted mt-1">Unresolved Conflicts to Clarify</div>
        </div>
      </div>

      {/* Generate / Regenerate */}
      {!email && !generating && (
        <div className="card mb-6" style={{ textAlign: "center", padding: "40px 32px" }}>
          <Mail size={40} color="#cbd5e1" style={{ margin: "0 auto 16px" }} />
          <div className="card-title mb-2">No email drafted yet</div>
          <div className="text-sm text-muted mb-4">
            The agent will write a professional follow-up email with one question per gap, organised by priority.
          </div>
          <button className="btn btn-primary btn-lg" onClick={handleGenerate}>
            <Mail size={16} /> Generate Follow-Up Email
          </button>
        </div>
      )}

      {generating && (
        <div className="card mb-6" style={{ textAlign: "center", padding: "40px 32px" }}>
          <div className="spinner" style={{ margin: "0 auto 16px" }} />
          <div className="card-title">Drafting follow-up email...</div>
          <div className="text-sm text-muted mt-2">Analysing gaps and writing targeted questions</div>
        </div>
      )}

      {email && !generating && (
        <>
          <div className="alert alert-info mb-4">
            <CheckCircle size={15} style={{ flexShrink: 0 }} />
            <div className="text-sm">
              Email drafted. Edit directly below, then copy or open in your email client.
              The email is based on <strong>{meta.gap_count}</strong> coverage gaps detected in your inputs.
            </div>
          </div>

          {/* Email editor */}
          <div className="card mb-4">
            <div className="flex items-center justify-between mb-3">
              <div className="card-title" style={{ marginBottom: 0 }}>Email Draft</div>
              <div className="flex gap-2">
                <button className="btn btn-sm btn-secondary" onClick={handleGenerate} disabled={generating}>
                  <RefreshCw size={13} /> Regenerate
                </button>
              </div>
            </div>
            <textarea
              value={edited}
              onChange={(e) => setEdited(e.target.value)}
              style={{
                width: "100%",
                minHeight: 480,
                fontFamily: "'DM Mono', monospace",
                fontSize: "0.82rem",
                lineHeight: 1.7,
                padding: "16px",
                border: "1.5px solid var(--grey-200)",
                borderRadius: 8,
                background: "var(--grey-50)",
                color: "var(--grey-900)",
                resize: "vertical",
                outline: "none",
              }}
            />
            <div className="text-xs text-muted mt-2">
              {edited.split(/\s+/).filter(Boolean).length} words · You can edit freely before sending
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3">
            <button className="btn btn-primary" onClick={handleCopy}>
              {copied ? <><CheckCircle size={15} /> Copied!</> : <><Copy size={15} /> Copy to Clipboard</>}
            </button>
            <button className="btn btn-secondary" onClick={openMailClient}>
              <Send size={15} /> Open in Mail App
            </button>
          </div>

          <div className="alert alert-warning mt-4">
            <AlertTriangle size={15} style={{ flexShrink: 0 }} />
            <div className="text-sm">
              Review before sending. Verify the client contact name and email address.
              Remove any questions that were already answered verbally in the meeting.
            </div>
          </div>
        </>
      )}
    </div>
  );
}
