import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createProject } from "../utils/api";

const INDUSTRIES = ["E-Commerce", "Healthcare", "Finance & Banking", "Logistics", "HR & People Ops", "Education", "Real Estate", "Manufacturing", "Media & Entertainment", "Government", "Other"];

export default function NewProject() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ project_name: "", client_name: "", industry: "", description: "", team_members: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async () => {
    if (!form.project_name || !form.client_name || !form.industry) {
      setError("Project name, client name, and industry are required.");
      return;
    }
    setLoading(true); setError("");
    try {
      const members = form.team_members.split(",").map((m) => m.trim()).filter(Boolean);
      const res = await createProject({ ...form, team_members: members });
      navigate(`/project/${res.data.project_id}/upload`);
    } catch {
      setError("Failed to create project. Is the backend running?");
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600 }}>
      <div className="page-header">
        <h2>New Project</h2>
        <p>Enter project details to begin. This is the only structured input required.</p>
      </div>

      {error && <div className="alert alert-error mb-4">{error}</div>}

      <div className="card">
        <div className="form-group">
          <label className="form-label">Project Name *</label>
          <input className="form-input" placeholder="e.g. ShopEase E-Commerce Platform" value={form.project_name} onChange={set("project_name")} />
        </div>
        <div className="form-group">
          <label className="form-label">Client Name *</label>
          <input className="form-input" placeholder="e.g. RetailCorp India Pvt. Ltd." value={form.client_name} onChange={set("client_name")} />
        </div>
        <div className="form-group">
          <label className="form-label">Industry *</label>
          <select className="form-select" value={form.industry} onChange={set("industry")}>
            <option value="">Select industry</option>
            {INDUSTRIES.map((ind) => <option key={ind} value={ind}>{ind}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Project Description</label>
          <textarea className="form-textarea" placeholder="One paragraph describing what the client wants to build and why..." value={form.description} onChange={set("description")} />
          <div className="form-hint">This helps the AI infer domain context and ask the right questions.</div>
        </div>
        <div className="form-group">
          <label className="form-label">Team Members</label>
          <input className="form-input" placeholder="e.g. Arjun Shah, Priya Nair" value={form.team_members} onChange={set("team_members")} />
          <div className="form-hint">Comma-separated names — appears on the BRD cover page.</div>
        </div>

        <hr className="divider" />
        <div className="flex gap-3">
          <button className="btn btn-primary btn-lg" onClick={handleSubmit} disabled={loading}>
            {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Creating...</> : "Create Project →"}
          </button>
          <button className="btn btn-secondary" onClick={() => navigate("/")}>Cancel</button>
        </div>
      </div>
    </div>
  );
}
