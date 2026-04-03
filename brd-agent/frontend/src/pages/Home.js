import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, Plus, HelpCircle, ArrowRight, BookOpen, Zap, Shield } from "lucide-react";
import { listProjects } from "../utils/api";

export default function Home() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    listProjects().then((r) => setProjects(r.data.projects || [])).catch(() => {});
  }, []);

  const statusLabel = {
    created: { label: "Created", cls: "badge-grey" },
    extracting: { label: "Extracting", cls: "badge-blue" },
    extracted: { label: "Ready for Review", cls: "badge-orange" },
    generating: { label: "Generating", cls: "badge-blue" },
    review: { label: "In Review", cls: "badge-orange" },
    complete: { label: "Complete", cls: "badge-green" },
    error: { label: "Error", cls: "badge-red" },
  };

  const routeForStatus = (p) => {
    const map = {
      created: `/project/${p.id}/upload`,
      transcript_uploaded: `/project/${p.id}/upload`,
      extracting: `/project/${p.id}/extraction`,
      extracted: `/project/${p.id}/conflicts`,
      generating: `/project/${p.id}/generation`,
      review: `/project/${p.id}/review`,
      complete: `/project/${p.id}/complete`,
    };
    return map[p.status] || `/project/${p.id}/upload`;
  };

  return (
    <div>
      <div className="page-header">
        <h2>Welcome to BRD Agent</h2>
        <p>Generate professional Business Requirements Documents from meeting transcripts and user stories.</p>
      </div>

      {/* Feature cards */}
      <div className="grid-3 mb-6">
        {[
          { icon: <HelpCircle size={22} color="#2563eb" />, title: "Pre-Meeting Questions", desc: "Use our structured question bank before every discovery call to ensure full BRD coverage." },
          { icon: <Zap size={22} color="#06b6d4" />, title: "AI Extraction", desc: "Transcripts and user stories are parsed, normalized, and structured into a Requirements Pool." },
          { icon: <Shield size={22} color="#10b981" />, title: "Conflict Detection", desc: "Contradictions between sources are flagged before a single word of the BRD is written." },
        ].map((f) => (
          <div key={f.title} className="card">
            <div style={{ marginBottom: 10 }}>{f.icon}</div>
            <div className="card-title">{f.title}</div>
            <div className="text-sm text-muted mt-1">{f.desc}</div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid-2 mb-6">
        <div className="card" style={{ cursor: "pointer", border: "1.5px solid #2563eb" }} onClick={() => navigate("/new-project")}>
          <div className="flex items-center gap-3">
            <div style={{ background: "#eff6ff", borderRadius: 10, padding: 10 }}><Plus size={20} color="#2563eb" /></div>
            <div>
              <div className="font-semibold">Start New Project</div>
              <div className="text-sm text-muted">Upload transcripts and generate a BRD</div>
            </div>
            <ArrowRight size={18} color="#2563eb" style={{ marginLeft: "auto" }} />
          </div>
        </div>
        <div className="card" style={{ cursor: "pointer" }} onClick={() => navigate("/question-bank")}>
          <div className="flex items-center gap-3">
            <div style={{ background: "#ecfdf5", borderRadius: 10, padding: 10 }}><BookOpen size={20} color="#10b981" /></div>
            <div>
              <div className="font-semibold">View Question Bank</div>
              <div className="text-sm text-muted">Pre-meeting discovery questions guide</div>
            </div>
            <ArrowRight size={18} color="#94a3b8" style={{ marginLeft: "auto" }} />
          </div>
        </div>
      </div>

      {/* Recent projects */}
      {projects.length > 0 && (
        <div className="card">
          <div className="card-title mb-4">Recent Projects</div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Project</th>
                <th>Client</th>
                <th>Industry</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {projects.slice(-10).reverse().map((p) => {
                const s = statusLabel[p.status] || { label: p.status, cls: "badge-grey" };
                return (
                  <tr key={p.id}>
                    <td className="font-semibold">{p.project_name}</td>
                    <td>{p.client_name}</td>
                    <td>{p.industry}</td>
                    <td><span className={`badge ${s.cls}`}>{s.label}</span></td>
                    <td>
                      <button className="btn btn-sm btn-secondary" onClick={() => navigate(routeForStatus(p))}>
                        Open <ArrowRight size={13} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {projects.length === 0 && (
        <div className="card full-center" style={{ minHeight: 180 }}>
          <FileText size={36} color="#cbd5e1" />
          <div className="text-muted">No projects yet. Start by creating one above.</div>
        </div>
      )}
    </div>
  );
}
