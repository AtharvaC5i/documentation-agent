import React from "react";
import { Outlet, NavLink, useNavigate, useLocation } from "react-router-dom";
import { Home, HelpCircle, Plus, Activity, Mail, GitBranch, Link2, LayoutList } from "lucide-react";

const STAGES = [
  { key: "upload",     label: "1. Upload",    path: (id) => `/project/${id}/upload` },
  { key: "extraction", label: "2. Extract",   path: (id) => `/project/${id}/extraction` },
  { key: "conflicts",  label: "3. Conflicts", path: (id) => `/project/${id}/conflicts` },
  { key: "sections",   label: "4. Sections",  path: (id) => `/project/${id}/sections` },
  { key: "generation", label: "5. Generate",  path: (id) => `/project/${id}/generation` },
  { key: "review",     label: "6. Review",    path: (id) => `/project/${id}/review` },
  { key: "complete",   label: "7. Done",      path: (id) => `/project/${id}/complete` },
];

const FEATURES = [
  { label: "Follow-Up Email", path: (id) => `/project/${id}/followup-email`, icon: Mail,       slug: "followup-email" },
  { label: "Living BRD",      path: (id) => `/project/${id}/living-brd`,     icon: GitBranch,  slug: "living-brd" },
  { label: "Traceability",    path: (id) => `/project/${id}/traceability`,   icon: Link2,      slug: "traceability" },
  { label: "Pipeline View",   path: (id) => `/project/${id}/pipeline`,       icon: LayoutList, slug: "pipeline" },
];

function getProjectIdFromPath(pathname) {
  const m = pathname.match(/\/project\/([^/]+)\//);
  return m ? m[1] : null;
}

function getStageFromPath(pathname) {
  for (const s of STAGES) {
    if (pathname.includes(`/${s.key}`)) return s.key;
  }
  return null;
}

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const currentProjectId = getProjectIdFromPath(location.pathname);
  const currentStage = getStageFromPath(location.pathname);
  const inProject = !!currentProjectId;

  return (
    <div className="app-shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>BRD Agent</h1>
          <span>AI Requirements Generator</span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-label">Main</div>
          <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
            <Home size={15} /> Dashboard
          </NavLink>
          <NavLink to="/question-bank" className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
            <HelpCircle size={15} /> Question Bank
          </NavLink>

          <div className="nav-label" style={{ marginTop: 4 }}>Project</div>
          <button className="nav-item" onClick={() => navigate("/new-project")}>
            <Plus size={15} /> New Project
          </button>

          {inProject && (
            <>
              <div className="nav-label" style={{ marginTop: 8 }}>Pipeline</div>
              {STAGES.map((stage) => (
                <button
                  key={stage.key}
                  className={`nav-item${currentStage === stage.key ? " active" : ""}`}
                  style={{ fontSize: ".77rem", padding: "6px 11px" }}
                  onClick={() => navigate(stage.path(currentProjectId))}
                >
                  <Activity size={12} />
                  {stage.label}
                </button>
              ))}

              <div className="nav-label" style={{ marginTop: 8 }}>Features</div>
              {FEATURES.map((f) => {
                const Icon = f.icon;
                const isActive = location.pathname.includes(`/${f.slug}`);
                return (
                  <button
                    key={f.label}
                    className={`nav-item${isActive ? " active" : ""}`}
                    style={{ fontSize: ".77rem", padding: "6px 11px" }}
                    onClick={() => navigate(f.path(currentProjectId))}
                  >
                    <Icon size={12} /> {f.label}
                  </button>
                );
              })}
            </>
          )}
        </nav>
      </aside>

      {/* ── Main ── */}
      <div className="main-content">
        <header className="topbar">
          <span className="topbar-title">BRD Generation Agent</span>
          <div className="flex items-center gap-3">
            {inProject && currentStage && (
              <span className="stage-pill">
                Stage: {STAGES.find(s => s.key === currentStage)?.label}
              </span>
            )}
            <span className="powered-pill">Powered by Databricks LLMs</span>
          </div>
        </header>
        <main className="page-body">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
