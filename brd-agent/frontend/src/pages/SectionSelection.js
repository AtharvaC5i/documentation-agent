import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getSuggestedSections, selectSections } from "../utils/api";
import { Plus, Trash2, Info } from "lucide-react";
import StepIndicator from "../components/StepIndicator";

const COVERAGE_COLORS = { strong: "#10b981", weak: "#f59e0b", none: "#ef4444" };

export default function SectionSelection() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [sections, setSections] = useState([]);
  const [selected, setSelected] = useState({});
  const [customSections, setCustomSections] = useState([]);
  const [newCustom, setNewCustom] = useState("");
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    getSuggestedSections(projectId)
      .then((r) => {
        const s = r.data.suggested_sections || [];
        setSections(s);
        const init = {};
        s.forEach((sec) => { init[sec.id] = sec.suggested; });
        setSelected(init);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [projectId]);

  const toggle = (id) => setSelected((s) => ({ ...s, [id]: !s[id] }));

  const addCustom = () => {
    const trimmed = newCustom.trim();
    if (trimmed && !customSections.includes(trimmed)) {
      setCustomSections((c) => [...c, trimmed]);
      setNewCustom("");
    }
  };

  const handleGenerate = async () => {
    setStarting(true);
    const selectedNames = sections.filter((s) => selected[s.id]).map((s) => s.name);
    await selectSections({ project_id: projectId, selected_sections: selectedNames, custom_sections: customSections });
    navigate(`/project/${projectId}/generation`);
  };

  if (loading) return <div className="full-center"><div className="spinner" /></div>;

  const totalSelected = Object.values(selected).filter(Boolean).length + customSections.length;

  return (
    <div>
      <StepIndicator current="sections" />
      <div className="page-header">
        <h2>BRD Section Selection</h2>
        <p>AI has pre-selected sections based on your input coverage. Review, adjust, and add custom sections.</p>
      </div>

      <div className="alert alert-info mb-6">
        <Info size={15} style={{ flexShrink: 0, marginTop: 2 }} />
        <div className="text-sm">Coverage colours: <strong style={{ color: "#10b981" }}>green = strong</strong> · <strong style={{ color: "#f59e0b" }}>orange = weak</strong> · <strong style={{ color: "#ef4444" }}>red = none</strong>. Sections with no coverage will be generated with limited context.</div>
      </div>

      <div className="card mb-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="card-title">Standard BRD Sections</div>
            <div className="text-sm text-muted">{totalSelected} sections selected</div>
          </div>
          <div className="flex gap-2">
            <button className="btn btn-sm btn-secondary" onClick={() => setSelected(Object.fromEntries(sections.map((s) => [s.id, true])))}>Select All</button>
            <button className="btn btn-sm btn-secondary" onClick={() => setSelected(Object.fromEntries(sections.map((s) => [s.id, false])))}>None</button>
          </div>
        </div>

        {sections.map((sec) => (
          <div key={sec.id} className="checkbox-row" onClick={() => toggle(sec.id)}>
            <input type="checkbox" checked={!!selected[sec.id]} onChange={() => {}} />
            <div style={{ flex: 1 }}>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm">{sec.name}</span>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: COVERAGE_COLORS[sec.coverage] || "#94a3b8", flexShrink: 0 }} />
                {sec.suggested && <span className="badge badge-blue" style={{ fontSize: ".65rem" }}>AI Suggested</span>}
              </div>
              <div className="text-xs text-muted mt-1">{sec.description}</div>
              {sec.reason && <div className="text-xs mt-1" style={{ color: "#2563eb" }}>{sec.reason}</div>}
            </div>
            <span className={`badge ${sec.coverage === "strong" ? "badge-green" : sec.coverage === "weak" ? "badge-orange" : "badge-red"}`} style={{ flexShrink: 0 }}>{sec.coverage}</span>
          </div>
        ))}
      </div>

      {/* Custom sections */}
      <div className="card mb-6">
        <div className="card-title mb-1">Custom Sections</div>
        <div className="card-sub">Add any project-specific section not in the standard list.</div>
        <div className="flex gap-2 mb-3">
          <input
            className="form-input"
            placeholder="e.g. GDPR Compliance Strategy, Data Migration Plan"
            value={newCustom}
            onChange={(e) => setNewCustom(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addCustom()}
          />
          <button className="btn btn-secondary" onClick={addCustom}><Plus size={16} /></button>
        </div>
        {customSections.map((s) => (
          <div key={s} className="flex items-center justify-between" style={{ padding: "8px 10px", background: "var(--grey-50)", borderRadius: 8, marginBottom: 6 }}>
            <span className="text-sm">{s}</span>
            <button className="btn-icon" onClick={() => setCustomSections((cs) => cs.filter((x) => x !== s))}><Trash2 size={14} /></button>
          </div>
        ))}
      </div>

      <button className="btn btn-primary btn-lg" onClick={handleGenerate} disabled={totalSelected === 0 || starting}>
        {starting ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Starting...</> : `Generate ${totalSelected} Sections →`}
      </button>
    </div>
  );
}
