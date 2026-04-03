import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CheckCircle, Clock } from "lucide-react";
import { getProjectStatus, getSections } from "../utils/api";
import { usePolling } from "../hooks/usePolling";
import StepIndicator from "../components/StepIndicator";
import ProgressCard from "../components/ProgressCard";
import QualityBadge from "../components/QualityBadge";

export default function Generation() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState({ status: "generating", progress: 0, progress_message: "Starting generation..." });
  const [sections, setSections] = useState([]);
  const [done, setDone] = useState(false);

  const poll = async () => {
    try {
      const s = await getProjectStatus(projectId);
      setStatus(s.data);

      // Fetch sections as they come in even before done
      if (["generating", "review"].includes(s.data.status)) {
        const r = await getSections(projectId);
        setSections(r.data.sections || []);
      }

      if (s.data.status === "review" || s.data.status === "error") {
        setDone(true);
      }
    } catch {}
  };

  usePolling(poll, 2500, !done);

  const avgQuality = sections.length > 0
    ? sections.reduce((a, s) => a + (s.quality_score || 0), 0) / sections.length
    : 0;

  return (
    <div>
      <StepIndicator current="generation" />
      <div className="page-header">
        <h2>BRD Section Generation</h2>
        <p>Each section is generated from your Requirements Pool via Databricks LLM. Low-quality sections are auto-regenerated.</p>
      </div>

      {status.status === "generating" && (
        <ProgressCard
          title="Generating BRD sections..."
          message={status.progress_message}
          progress={status.progress}
        />
      )}

      {status.status === "error" && (
        <div className="alert alert-error mb-4">{status.progress_message}</div>
      )}

      {/* Live section list */}
      {sections.length > 0 && (
        <div className="card mb-6" style={{ marginTop: 24 }}>
          <div className="flex items-center justify-between mb-4">
            <div className="card-title">Sections Generated</div>
            {sections.length > 0 && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted">Avg quality:</span>
                <QualityBadge score={avgQuality} />
              </div>
            )}
          </div>
          <table className="data-table">
            <thead>
              <tr><th>#</th><th>Section</th><th>Requirements Used</th><th>Quality</th><th>Status</th></tr>
            </thead>
            <tbody>
              {sections.map((s, i) => (
                <tr key={s.id}>
                  <td className="text-muted text-sm">{i + 1}</td>
                  <td className="font-semibold text-sm">{s.name}</td>
                  <td className="text-sm text-muted">{s.req_count}</td>
                  <td><QualityBadge score={s.quality_score || 0} /></td>
                  <td>
                    {s.status === "pending_review"
                      ? <span className="badge badge-orange">Pending Review</span>
                      : s.status === "regenerated"
                      ? <span className="badge badge-blue">Regenerated</span>
                      : <span className="badge badge-grey">{s.status}</span>}
                  </td>
                </tr>
              ))}
              {/* Placeholder row for in-progress */}
              {status.status === "generating" && (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", padding: "14px", color: "var(--grey-400)" }}>
                    <div className="flex items-center gap-2" style={{ justifyContent: "center" }}>
                      <div className="spinner" style={{ width: 14, height: 14 }} />
                      <span className="text-sm">{status.progress_message}</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {done && status.status === "review" && (
        <>
          <div className="alert alert-success mb-6">
            <CheckCircle size={16} />
            All {sections.length} sections generated. Average quality: {Math.round(avgQuality * 100)}%. Ready for human review.
          </div>
          <button className="btn btn-primary btn-lg" onClick={() => navigate(`/project/${projectId}/review`)}>
            Proceed to Human Review →
          </button>
        </>
      )}
    </div>
  );
}
