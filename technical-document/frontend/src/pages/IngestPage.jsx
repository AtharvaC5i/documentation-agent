import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { ingestGithub, ingestZip } from "../api/endpoints";
import Notice from "../components/ui/Notice";
import Spinner from "../components/ui/Spinner";
import SectionLabel from "../components/ui/SectionLabel";
import TagRow from "../components/ui/TagRow";
import Card from "../components/ui/Card";
import { useApiStatus } from "../hooks/useApiStatus";

// ── Progress steps ────────────────────────────────────────────────────────────
const GH_STEPS = [
  "Connecting",
  "Cloning repo",
  "Filtering files",
  "Analysing stack",
  "Finalising",
];
const ZIP_STEPS = [
  "Reading ZIP",
  "Extracting",
  "Filtering files",
  "Analysing stack",
  "Finalising",
];

// ── How DocAgent works ────────────────────────────────────────────────────────
const HOW_STEPS = [
  {
    num: 1,
    title: "Ingest",
    desc: "Clone or upload code. Noise stripped automatically.",
  },
  {
    num: 2,
    title: "Sections",
    desc: "AI suggests doc sections based on your actual stack.",
  },
  {
    num: 3,
    title: "Context",
    desc: "Code embedded locally in ChromaDB — nothing leaves your machine.",
  },
  {
    num: 4,
    title: "Generate",
    desc: "Each section written via RAG. Low-quality sections auto-regenerated.",
  },
  {
    num: 5,
    title: "Review",
    desc: "Approve, edit, reject, reorder sections before assembly.",
  },
  { num: 6, title: "Assemble", desc: "Download as .docx or send by email." },
];

// ── Sub-components ────────────────────────────────────────────────────────────

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors duration-150 flex items-center gap-2
        ${
          active
            ? "border-primary text-primary"
            : "border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300"
        }`}
    >
      {children}
    </button>
  );
}

function FieldLabel({ required, children }) {
  return (
    <label className="block text-[11px] font-bold uppercase tracking-widest text-gray-400 mb-1.5">
      {children}
      {required && <span className="text-red-500 ml-0.5">*</span>}
    </label>
  );
}

function InputField({ label, required, className = "", ...props }) {
  return (
    <div className={className}>
      <FieldLabel required={required}>{label}</FieldLabel>
      <input
        {...props}
        className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2
                   text-sm text-gray-900 placeholder:text-gray-300
                   focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
                   disabled:bg-gray-50 disabled:text-gray-400
                   transition-colors duration-150"
      />
    </div>
  );
}

function TextareaField({ label, className = "", ...props }) {
  return (
    <div className={className}>
      <FieldLabel>{label}</FieldLabel>
      <textarea
        {...props}
        className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2
                   text-sm text-gray-900 placeholder:text-gray-300 resize-none
                   focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary
                   disabled:bg-gray-50
                   transition-colors duration-150"
      />
    </div>
  );
}

function PrimaryBtn({ loading, disabled, children, ...props }) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className="flex items-center justify-center gap-2 w-full
                 bg-primary hover:bg-primary-hover active:bg-primary-active
                 text-white text-sm font-semibold
                 px-4 py-2.5 rounded-lg shadow-sm
                 disabled:opacity-50 disabled:cursor-not-allowed
                 transition-colors duration-150"
    >
      {loading && <Spinner size="sm" className="text-white" />}
      {children}
    </button>
  );
}

function StepProgress({ steps, active }) {
  const pct =
    active === null ? 0 : Math.round(((active + 1) / steps.length) * 100);
  return (
    <div className="mt-5 bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center gap-3 mb-4">
        <Spinner size="sm" className="text-primary flex-shrink-0" />
        <span className="text-sm font-medium text-gray-700">
          {active !== null ? steps[active] : "Starting…"}
        </span>
        <span className="ml-auto text-xs font-semibold tabular-nums text-gray-400">
          {pct}%
        </span>
      </div>
      <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-4 space-y-0">
        {steps.map((step, i) => {
          const isDone = i < active;
          const isActive = i === active;
          return (
            <div
              key={step}
              className={`flex items-center gap-3 py-2 border-b border-gray-50
                              last:border-0 transition-opacity duration-300
                              ${i > active ? "opacity-30" : "opacity-100"}`}
            >
              <span
                className={`w-4 h-4 rounded-full flex items-center justify-center
                                flex-shrink-0 transition-all duration-300
                ${
                  isDone
                    ? "bg-green-500"
                    : isActive
                      ? "bg-primary"
                      : "bg-gray-100 border border-gray-200"
                }`}
              >
                {isDone ? (
                  <svg
                    width="7"
                    height="7"
                    viewBox="0 0 10 10"
                    fill="none"
                    stroke="white"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  >
                    <polyline points="1.5 5 4 7.5 8.5 2.5" />
                  </svg>
                ) : isActive ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-white" />
                ) : null}
              </span>
              <span
                className={`text-xs transition-colors duration-300
                ${
                  isDone
                    ? "text-gray-300 line-through"
                    : isActive
                      ? "text-gray-800 font-medium"
                      : "text-gray-400"
                }`}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Metric cell ───────────────────────────────────────────────────────────────
function MetricCell({ label, value, sub }) {
  return (
    <div className="py-4 px-4 text-center">
      <div className="text-xl font-bold tabular-nums text-gray-900 leading-none tracking-tight">
        {value}
      </div>
      <div className="text-[11px] font-semibold text-gray-800 mt-1.5 leading-none">
        {label}
      </div>
      <div className="text-[10px] text-gray-400 mt-0.5">{sub}</div>
    </div>
  );
}

// ── Analysis result panel ─────────────────────────────────────────────────────
function AnalysisResult({ analysis, filteredFileCount, onContinue, onReset }) {
  const loc = analysis?.total_loc ?? 0;
  const strategy = loc > 50000 ? "RAPTOR" : "Flat";

  const tagGroups = [
    {
      label: "Languages",
      icon: (
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <polyline points="16 18 22 12 16 6" />
          <polyline points="8 6 2 12 8 18" />
        </svg>
      ),
      items: analysis?.languages ?? [],
      color: "bg-blue-50 border-blue-200 text-blue-700",
    },
    {
      label: "Frameworks",
      icon: (
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <rect x="2" y="3" width="20" height="14" rx="2" />
          <line x1="8" y1="21" x2="16" y2="21" />
          <line x1="12" y1="17" x2="12" y2="21" />
        </svg>
      ),
      items: analysis?.frameworks ?? [],
      color: "bg-purple-50 border-purple-200 text-purple-700",
    },
    {
      label: "Databases",
      icon: (
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
        </svg>
      ),
      items: analysis?.databases ?? [],
      color: "bg-green-50 border-green-200 text-green-700",
    },
  ].filter((g) => g.items.length > 0);

  // Infrastructure badges
  const infra = [
    { key: "has_dockerfile", label: "Docker" },
    { key: "has_cicd", label: "CI/CD" },
    { key: "has_kubernetes", label: "Kubernetes" },
    { key: "has_terraform", label: "Terraform" },
    { key: "has_ansible", label: "Ansible" },
  ].filter((b) => analysis?.[b.key]);

  return (
    <div className="mt-5">
      {/* Success notice */}
      <div
        className="flex items-center gap-2.5 bg-green-50 border border-green-100
                      rounded-lg px-3.5 py-2.5 mb-4 text-xs font-medium text-green-700"
      >
        <svg
          width="13"
          height="13"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          className="flex-shrink-0"
          aria-hidden="true"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
        Codebase ingested and analysed successfully.
      </div>

      {/* KPI strip */}
      <div
        className="grid grid-cols-4 bg-white border border-gray-200
                      rounded-xl overflow-hidden mb-4 shadow-sm"
      >
        {[
          {
            label: "Lines of Code",
            value: loc.toLocaleString(),
            sub: "source LOC",
          },
          {
            label: "Endpoints",
            value: analysis?.api_endpoints_count ?? 0,
            sub: "detected",
          },
          { label: "Strategy", value: strategy, sub: "auto-selected" },
          { label: "Files", value: filteredFileCount, sub: "after filter" },
        ].map((m, i, arr) => (
          <div
            key={m.label}
            className={`py-4 px-4 text-center
                 ${i < arr.length - 1 ? "border-r border-gray-100" : ""}`}
          >
            <div
              className="text-xl font-bold tabular-nums text-gray-900
                            leading-none tracking-tight"
            >
              {m.value}
            </div>
            <div className="text-[11px] font-semibold text-gray-700 mt-1.5 leading-none">
              {m.label}
            </div>
            <div className="text-[10px] text-gray-400 mt-0.5">{m.sub}</div>
          </div>
        ))}
      </div>

      {/* Stack detection */}
      {tagGroups.length > 0 && (
        <div
          className="bg-white border border-gray-200 rounded-xl
                        overflow-hidden mb-4 shadow-sm"
        >
          {tagGroups.map((group, gi, arr) => (
            <div
              key={group.label}
              className={`px-4 py-3.5
                   ${gi < arr.length - 1 ? "border-b border-gray-50" : ""}`}
            >
              <div className="flex items-center gap-1.5 mb-2.5">
                <span className="text-gray-400">{group.icon}</span>
                <span
                  className="text-[10px] font-bold uppercase tracking-widest
                                 text-gray-400"
                >
                  {group.label}
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {group.items.map((item) => (
                  <span
                    key={item}
                    className={`inline-flex items-center px-2.5 py-1 rounded-full
                                    text-[11px] font-semibold border ${group.color}`}
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}

          {/* Infrastructure row — only shown if any are detected */}
          {infra.length > 0 && (
            <div className="px-4 py-3.5 border-t border-gray-50">
              <div className="flex items-center gap-1.5 mb-2.5">
                <svg
                  width="11"
                  height="11"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  className="text-gray-400"
                  aria-hidden="true"
                >
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                <span
                  className="text-[10px] font-bold uppercase tracking-widest
                                 text-gray-400"
                >
                  Infrastructure
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {infra.map((b) => (
                  <span
                    key={b.key}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full
                                   text-[11px] font-semibold border
                                   bg-gray-50 border-gray-200 text-gray-600"
                  >
                    <span
                      className="w-1.5 h-1.5 rounded-full bg-gray-400
                                     flex-shrink-0"
                    />
                    {b.label}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onContinue}
          className="flex-1 flex items-center justify-center gap-2
                     bg-primary hover:bg-primary-hover active:bg-primary-active
                     text-white text-sm font-semibold
                     px-6 py-2.5 rounded-lg shadow-sm
                     transition-colors duration-150"
        >
          Continue to Sections
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            aria-hidden="true"
          >
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
        <button
          onClick={onReset}
          className="px-4 py-2.5 text-sm font-medium text-gray-500
                     border border-gray-200 rounded-lg hover:bg-gray-50
                     hover:text-gray-800 transition-colors duration-150"
        >
          New Project
        </button>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function IngestPage() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  const online = useApiStatus();

  const [tab, setTab] = useState("github");
  const [loading, setLoading] = useState(false);
  const [progressStep, setProgressStep] = useState(null);
  const [error, setError] = useState(null);

  // GitHub form
  const [ghUrl, setGhUrl] = useState("");
  const [ghToken, setGhToken] = useState("");
  const [ghName, setGhName] = useState("");
  const [ghClient, setGhClient] = useState("");
  const [ghTeam, setGhTeam] = useState("");
  const [ghDesc, setGhDesc] = useState("");

  // ZIP form
  const [zipFile, setZipFile] = useState(null); // File object — .size read directly
  const [zipName, setZipName] = useState("");
  const [zipClient, setZipClient] = useState("");
  const [zipTeam, setZipTeam] = useState("");
  const [zipDesc, setZipDesc] = useState("");

  // ── Progress simulation ───────────────────────────────────────────────────
  const simulateProgress = (steps) => {
    for (let i = 0; i < steps.length - 1; i++) {
      const ii = i;
      setTimeout(() => setProgressStep(ii), ii * 350);
    }
  };

  // ── GitHub submit ─────────────────────────────────────────────────────────
  const handleGithubSubmit = async () => {
    if (!ghUrl.trim() || !ghName.trim() || !ghClient.trim()) {
      setError("Repository URL, project name and client name are required.");
      return;
    }
    setError(null);
    setLoading(true);
    setProgressStep(0);
    const teamMembers = ghTeam
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    try {
      simulateProgress(GH_STEPS);
      const { data } = await ingestGithub({
        github_url: ghUrl.trim(),
        github_token: ghToken.trim() || null,
        metadata: {
          project_name: ghName.trim(),
          client_name: ghClient.trim(),
          team_members: teamMembers,
          description: ghDesc.trim(),
        },
      });
      setProgressStep(GH_STEPS.length - 1);
      dispatch({
        type: "SET_PROJECT",
        payload: {
          projectId: data.project_id,
          metadata: {
            projectname: ghName.trim(),
            clientname: ghClient.trim(),
            teammembers: teamMembers,
            description: ghDesc.trim(),
          },
          analysis: data.analysis,
          filteredFileCount: data.filtered_file_count ?? 0,
        },
      });
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message);
    } finally {
      setLoading(false);
    }
  };

  // ── ZIP submit ────────────────────────────────────────────────────────────
  const handleZipSubmit = async () => {
    if (!zipFile || !zipName.trim() || !zipClient.trim()) {
      setError("ZIP file, project name and client name are required.");
      return;
    }
    setError(null);
    setLoading(true);
    setProgressStep(0);
    const teamMembers = zipTeam
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const form = new FormData();
    form.append("file", zipFile, zipFile.name);
    form.append("project_name", zipName.trim());
    form.append("client_name", zipClient.trim());
    form.append("team_members", JSON.stringify(teamMembers));
    form.append("description", zipDesc.trim());
    try {
      simulateProgress(ZIP_STEPS);
      const { data } = await ingestZip(form);
      setProgressStep(ZIP_STEPS.length - 1);
      dispatch({
        type: "SET_PROJECT",
        payload: {
          projectId: data.project_id,
          metadata: {
            projectname: zipName.trim(),
            clientname: zipClient.trim(),
            teammembers: teamMembers,
            description: zipDesc.trim(),
          },
          analysis: data.analysis,
          filteredFileCount: data.filtered_file_count ?? 0,
        },
      });
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    dispatch({ type: "RESET" });
    setError(null);
    setProgressStep(null);
  };

  const hasResult = !!state.analysis;

  return (
    <div className="flex gap-10">
      {/* ── Left column ── */}
      <div className="flex-[6] min-w-0">
        <div className="mb-5">
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
            Ingest Codebase
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Provide a GitHub repository or a ZIP archive. Binaries, lock files,
            and node_modules are stripped automatically.
          </p>
        </div>

        {!online && (
          <Notice kind="error" className="mb-4">
            API server not responding. Start the backend with{" "}
            <code className="font-mono text-xs">python run.py</code> then
            refresh.
          </Notice>
        )}

        {error && (
          <Notice kind="error" className="mb-4">
            {error}
          </Notice>
        )}

        {/* Tab bar */}
        <div className="flex border-b border-gray-200 mb-5">
          <TabButton
            active={tab === "github"}
            onClick={() => {
              setTab("github");
              setError(null);
            }}
          >
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57
                       0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41
                       -1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815
                       2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925
                       0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23
                       .96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65
                       .24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925
                       .435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57
                       A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"
              />
            </svg>
            GitHub Repository
          </TabButton>
          <TabButton
            active={tab === "zip"}
            onClick={() => {
              setTab("zip");
              setError(null);
            }}
          >
            <svg
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            ZIP Archive
          </TabButton>
        </div>

        {/* ── GitHub form ── */}
        {tab === "github" && !hasResult && (
          <div>
            <div className="grid grid-cols-2 gap-4">
              <InputField
                label="Repository URL"
                required
                placeholder="https://github.com/owner/repo"
                value={ghUrl}
                onChange={(e) => setGhUrl(e.target.value)}
                disabled={loading}
                className="col-span-2"
              />
              <InputField
                label="Access Token"
                type="password"
                placeholder="ghp_… for private repos"
                value={ghToken}
                onChange={(e) => setGhToken(e.target.value)}
                disabled={loading}
              />
              <div />
              <InputField
                label="Project Name"
                required
                placeholder="My API Service"
                value={ghName}
                onChange={(e) => setGhName(e.target.value)}
                disabled={loading}
              />
              <InputField
                label="Client Name"
                required
                placeholder="Acme Corp"
                value={ghClient}
                onChange={(e) => setGhClient(e.target.value)}
                disabled={loading}
              />
              <InputField
                label="Team Members (comma-separated)"
                placeholder="Alice, Bob"
                value={ghTeam}
                onChange={(e) => setGhTeam(e.target.value)}
                disabled={loading}
              />
              <div />
              <TextareaField
                label="Description (optional)"
                placeholder="What does this project do?"
                rows={3}
                value={ghDesc}
                onChange={(e) => setGhDesc(e.target.value)}
                disabled={loading}
                className="col-span-2"
              />
            </div>
            {loading ? (
              <StepProgress steps={GH_STEPS} active={progressStep} />
            ) : (
              <div className="mt-4">
                <PrimaryBtn
                  onClick={handleGithubSubmit}
                  loading={loading}
                  disabled={!online}
                >
                  Clone &amp; Analyse
                </PrimaryBtn>
              </div>
            )}
          </div>
        )}

        {/* ── ZIP form ── */}
        {tab === "zip" && !hasResult && (
          <div>
            {/* Drop zone */}
            {/* Drop zone */}
            <div className="mb-4">
              <FieldLabel>ZIP File</FieldLabel>
              <label
                className={`group relative flex flex-col items-center justify-center
                border-2 border-dashed rounded-xl px-6 py-10
                cursor-pointer transition-all duration-200 text-center
                ${
                  zipFile
                    ? "border-primary bg-primary/5"
                    : "border-gray-200 hover:border-primary/50 hover:bg-gray-50/80"
                }`}
              >
                <input
                  type="file"
                  accept=".zip"
                  className="sr-only"
                  disabled={loading}
                  onClick={(e) => {
                    // Reset value so selecting the same file re-triggers onChange
                    e.target.value = "";
                  }}
                  onChange={(e) => {
                    const f = e.target.files?.[0] ?? null;
                    if (!f) {
                      setZipFile(null);
                      return;
                    }

                    // Use FileReader to fully materialise the file before reading .size
                    const reader = new FileReader();
                    reader.onload = () => {
                      // reader.result is an ArrayBuffer — byteLength is always accurate
                      const accurate = new File([reader.result], f.name, {
                        type: f.type,
                      });
                      setZipFile(accurate);
                    };
                    reader.readAsArrayBuffer(f);
                  }}
                />

                {zipFile ? (
                  /* ── File selected state ── */
                  <div className="flex flex-col items-center gap-2 w-full">
                    {/* File icon + name row */}
                    <div
                      className="flex items-center gap-3 bg-white border border-primary/20
                        rounded-lg px-4 py-3 w-full max-w-sm shadow-sm"
                    >
                      <div
                        className="w-9 h-9 rounded-lg bg-primary/10 flex items-center
                          justify-center flex-shrink-0"
                      >
                        <svg
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          className="text-primary"
                          aria-hidden="true"
                        >
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                          <line x1="16" y1="13" x2="8" y2="13" />
                          <line x1="16" y1="17" x2="8" y2="17" />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0 text-left">
                        <div className="text-xs font-semibold text-gray-800 truncate">
                          {zipFile.name}
                        </div>
                        <div className="text-[10px] text-gray-400 mt-0.5 tabular-nums">
                          {(zipFile.size / 1024 / 1024).toFixed(2)} MB
                        </div>
                      </div>
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        className="text-green-500 flex-shrink-0"
                        aria-hidden="true"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </div>
                    <span className="text-[10px] text-gray-400 mt-1">
                      Click to replace file
                    </span>
                  </div>
                ) : (
                  /* ── Empty state ── */
                  <div className="flex flex-col items-center gap-3">
                    <div
                      className="w-12 h-12 rounded-xl bg-gray-100 border border-gray-200
                        flex items-center justify-center
                        group-hover:bg-primary/10 group-hover:border-primary/20
                        transition-colors duration-200"
                    >
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        className="text-gray-400 group-hover:text-primary transition-colors duration-200"
                        aria-hidden="true"
                      >
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-gray-700">
                        Click to select a ZIP file
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        .zip archives only — node_modules and binaries stripped
                        automatically
                      </p>
                    </div>
                  </div>
                )}
              </label>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <InputField
                label="Project Name"
                required
                placeholder="My Project"
                value={zipName}
                onChange={(e) => setZipName(e.target.value)}
                disabled={loading}
              />
              <InputField
                label="Client Name"
                required
                placeholder="Acme Corp"
                value={zipClient}
                onChange={(e) => setZipClient(e.target.value)}
                disabled={loading}
              />
              <InputField
                label="Team Members (comma-separated)"
                placeholder="Alice, Bob"
                value={zipTeam}
                onChange={(e) => setZipTeam(e.target.value)}
                disabled={loading}
              />
              <div />
              <TextareaField
                label="Description (optional)"
                placeholder="What does this project do?"
                rows={3}
                value={zipDesc}
                onChange={(e) => setZipDesc(e.target.value)}
                disabled={loading}
                className="col-span-2"
              />
            </div>

            {loading ? (
              <StepProgress steps={ZIP_STEPS} active={progressStep} />
            ) : (
              <div className="mt-4">
                <PrimaryBtn
                  onClick={handleZipSubmit}
                  loading={loading}
                  disabled={!online}
                >
                  Extract &amp; Analyse
                </PrimaryBtn>
              </div>
            )}
          </div>
        )}

        {/* ── Analysis result ── */}
        {hasResult && !loading && (
          <AnalysisResult
            analysis={state.analysis}
            filteredFileCount={state.filteredFileCount}
            onContinue={() => navigate(`/project/${state.projectId}/sections`)}
            onReset={handleReset}
          />
        )}
      </div>

      {/* ── Right sidebar ── */}
      <div className="flex-[4] min-w-0 hidden md:block">
        <div className="h-[60px]" />
        <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-3">
          How DocAgent Works
        </p>
        <div className="flex flex-col">
          {HOW_STEPS.map(({ num, title, desc }) => (
            <div
              key={num}
              className="flex gap-3 py-3 border-b border-gray-100 last:border-0"
            >
              <div
                className="flex-shrink-0 w-6 h-6 rounded-md bg-blue-50 border border-blue-100
                              flex items-center justify-center
                              text-[10px] font-bold text-blue-400"
              >
                {num}
              </div>
              <div>
                <div className="text-sm font-semibold text-gray-800 mb-0.5">
                  {title}
                </div>
                <div className="text-xs text-gray-400 leading-relaxed">
                  {desc}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Active project card */}
        {state.projectId && (
          <div className="mt-5">
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-2">
              Active Project
            </p>
            <Card variant="blue">
              <div className="text-sm font-semibold text-blue-800 mb-0.5">
                {state.metadata?.projectname}
              </div>
              <div className="text-xs text-blue-600/70 mb-1">
                Client: {state.metadata?.clientname}
              </div>
              <div className="font-mono text-[10px] text-blue-400 mt-1.5 break-all">
                {state.projectId}
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
