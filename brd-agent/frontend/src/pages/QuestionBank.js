import React, { useEffect, useState } from "react";
import { HelpCircle, ChevronDown, ChevronRight, Download } from "lucide-react";
import { getQuestionBank } from "../utils/api";

export default function QuestionBank() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getQuestionBank()
      .then((r) => { setData(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const toggle = (i) => setOpen((o) => ({ ...o, [i]: !o[i] }));

  if (loading) return <div className="full-center"><div className="spinner" /></div>;
  if (!data) return <div className="alert alert-error">Failed to load question bank.</div>;

  return (
    <div>
      <div className="page-header">
        <h2>Pre-Meeting Question Bank</h2>
        <p>Use these questions in every client discovery call. They are designed to ensure full BRD coverage.</p>
      </div>

      <div className="alert alert-info mb-6">
        <HelpCircle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
        <div>
          <strong>How to use:</strong> Before each client meeting, review these questions and adapt them to the project context.
          They are organized by BRD section — covering all sections ensures the transcript will contain everything needed.
        </div>
      </div>

      <div className="card mb-4" style={{ padding: "14px 20px" }}>
        <div className="flex items-center justify-between">
          <div>
            <span className="font-semibold">{data.title}</span>
            <span className="text-sm text-muted" style={{ marginLeft: 10 }}>{data.sections?.length} sections · {data.sections?.reduce((a, s) => a + s.questions.length, 0)} questions</span>
          </div>
          <button className="btn btn-sm btn-secondary" onClick={() => {
            const text = data.sections.map(s =>
              `=== ${s.section} ===\n${s.questions.map((q, i) => `${i + 1}. ${q}`).join("\n")}`
            ).join("\n\n");
            const blob = new Blob([text], { type: "text/plain" });
            const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
            a.download = "BRD_Question_Bank.txt"; a.click();
          }}>
            <Download size={14} /> Export
          </button>
        </div>
      </div>

      {data.sections?.map((section, i) => (
        <div key={i} className="section-review-card" style={{ marginBottom: 10 }}>
          <div className="section-review-header" onClick={() => toggle(i)}>
            <div className="flex items-center gap-3">
              <span className="badge badge-blue">{section.questions.length}</span>
              <span className="font-semibold" style={{ fontSize: ".95rem" }}>{section.section}</span>
            </div>
            {open[i] ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </div>
          {open[i] && (
            <div style={{ padding: "16px 20px" }}>
              <ol style={{ paddingLeft: 18 }}>
                {section.questions.map((q, j) => (
                  <li key={j} style={{ marginBottom: 10, lineHeight: 1.6, color: "var(--grey-700)", fontSize: ".9rem" }}>{q}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
