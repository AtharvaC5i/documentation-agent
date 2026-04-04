import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { getSuggestions, confirmSections } from "../api/endpoints";
import Notice from "../components/ui/Notice";
import Spinner from "../components/ui/Spinner";
import TagRow from "../components/ui/TagRow";

// ── Sub-components ────────────────────────────────────────────────────────────

function SectionCheckbox({
  name,
  reason,
  defaultChecked,
  onChange,
  variant = "recommended",
}) {
  const [checked, setChecked] = useState(defaultChecked);

  function handleChange() {
    const next = !checked;
    setChecked(next);
    onChange(name, next);
  }

  return (
    <label
      className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer
                  transition-all duration-150 group
                  ${
                    checked
                      ? variant === "recommended"
                        ? "bg-primary/5 border-primary/30"
                        : "bg-blue-50 border-blue-200"
                      : "bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  }`}
    >
      {/* Custom checkbox */}
      <span
        className={`flex-shrink-0 w-4 h-4 rounded border-[1.5px] mt-0.5
                        flex items-center justify-center transition-all duration-150
                        ${
                          checked
                            ? "bg-primary border-primary"
                            : "border-gray-300 group-hover:border-gray-400"
                        }`}
      >
        {checked && (
          <svg
            width="8"
            height="8"
            viewBox="0 0 10 10"
            fill="none"
            stroke="white"
            strokeWidth="2.5"
            strokeLinecap="round"
          >
            <polyline points="1.5 5 4 7.5 8.5 2.5" />
          </svg>
        )}
      </span>

      <div className="min-w-0">
        <div
          className={`text-sm font-medium leading-tight transition-colors
                         ${checked ? "text-gray-900" : "text-gray-700"}`}
        >
          {name}
        </div>
        {reason && (
          <div className="text-xs text-gray-400 mt-0.5 leading-relaxed">
            {reason}
          </div>
        )}
      </div>

      <input
        type="checkbox"
        className="sr-only"
        checked={checked}
        onChange={handleChange}
      />
    </label>
  );
}

function DevOpsFlag({ label, active }) {
  return (
    <div
      className={`flex items-center gap-1.5 text-xs
                     ${active ? "text-gray-700" : "text-gray-300"}`}
    >
      <span
        className={`w-2 h-2 rounded-full flex-shrink-0
                        ${active ? "bg-green-500" : "bg-gray-200"}`}
      />
      {label}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function SectionsPage() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  const pid = state.projectId;
  const analysis = state.analysis;

  const [suggestions, setSuggestions] = useState([]);
  const [selected, setSelected] = useState({}); // { [name]: bool }
  const [customRaw, setCustomRaw] = useState("");
  const [loadingSugg, setLoadingSugg] = useState(false);
  const [loadingConf, setLoadingConf] = useState(false);
  const [error, setError] = useState(null);

  // ── Derived ───────────────────────────────────────────────────────────────
  const recommended = suggestions.filter((s) => s.selected);
  const optional = suggestions.filter((s) => !s.selected);
  const customSecs = customRaw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const chosen = suggestions
    .filter((s) => selected[s.name] ?? s.selected)
    .map((s) => s.name);
  const allSections = [...chosen, ...customSecs];

  // ── Handlers ─────────────────────────────────────────────────────────────

  // ✅ Same logic as original
  async function handleLoadSuggestions() {
    setLoadingSugg(true);
    setError(null);
    try {
      const { data } = await getSuggestions(pid);
      const suggs = data.suggestions ?? [];
      setSuggestions(suggs);
      // Initialise selected map: recommended = true, optional = false
      const initSelected = {};
      suggs.forEach((s) => {
        initSelected[s.name] = s.selected;
      });
      setSelected(initSelected);
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message);
    } finally {
      setLoadingSugg(false);
    }
  }

  function handleCheckChange(name, val) {
    setSelected((prev) => ({ ...prev, [name]: val }));
  }

  // ✅ Same logic as original
  async function handleConfirm() {
    if (allSections.length === 0) {
      setError("Select at least one section.");
      return;
    }
    setLoadingConf(true);
    setError(null);
    try {
      const { data } = await confirmSections({
        project_id: pid,
        confirmed_sections: chosen,
        custom_sections: customSecs,
      });
      dispatch({
        type: "SET_SECTIONS",
        payload: {
          confirmedSections: data.final_sections,
          sectionOrder: data.final_sections,
        },
      });
      navigate(`/project/${pid}/context`);
    } catch (e) {
      setError(e.response?.data?.detail ?? e.message);
    } finally {
      setLoadingConf(false);
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex gap-10">
      {/* ── Left column ── */}
      <div className="flex-[6] min-w-0">
        {/* Page heading */}
        <div className="mb-5">
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
            Section Selection
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            AI reviews your stack and recommends documentation sections. Adjust
            the selection and add custom sections as needed.
          </p>
        </div>

        {error && (
          <Notice kind="error" className="mb-4">
            {error}
          </Notice>
        )}

        {/* Generate suggestions button */}
        {suggestions.length === 0 && (
          <div className="mb-5">
            {!loadingSugg ? (
              <button
                onClick={handleLoadSuggestions}
                className="flex items-center gap-2 bg-primary hover:bg-primary-hover
                           text-white text-sm font-semibold px-5 py-2.5 rounded-lg
                           shadow-sm transition-colors duration-150"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                Generate Suggestions
              </button>
            ) : (
              <div className="flex items-center gap-3 text-sm text-gray-600">
                <Spinner size="sm" className="text-primary" />
                <span>Analysing stack and generating recommendations…</span>
              </div>
            )}
            <Notice kind="info" className="mt-4">
              Click <strong>Generate Suggestions</strong> to get AI-driven
              recommendations based on your detected stack.
            </Notice>
          </div>
        )}

        {/* ── Suggestions grid ── */}
        {suggestions.length > 0 && (
          <div>
            {/* Recommended */}
            {recommended.length > 0 && (
              <div className="mb-5">
                <div className="flex items-center gap-2 mb-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                    Recommended
                  </span>
                  <span
                    className="text-[10px] font-semibold text-primary bg-primary/10
                                   px-1.5 py-0.5 rounded-full"
                  >
                    {recommended.length}
                  </span>
                  <div className="flex-1 h-px bg-gray-100" />
                </div>
                <div className="grid grid-cols-1 gap-1.5">
                  {recommended.map((s) => (
                    <SectionCheckbox
                      key={s.name}
                      name={s.name}
                      reason={s.reason}
                      defaultChecked={true}
                      onChange={handleCheckChange}
                      variant="recommended"
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Optional */}
            {optional.length > 0 && (
              <div className="mb-5">
                <div className="flex items-center gap-2 mb-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                    Optional
                  </span>
                  <span
                    className="text-[10px] font-semibold text-gray-400 bg-gray-100
                                   px-1.5 py-0.5 rounded-full"
                  >
                    {optional.length}
                  </span>
                  <div className="flex-1 h-px bg-gray-100" />
                </div>
                <div className="grid grid-cols-1 gap-1.5">
                  {optional.map((s) => (
                    <SectionCheckbox
                      key={s.name}
                      name={s.name}
                      reason={s.reason}
                      defaultChecked={false}
                      onChange={handleCheckChange}
                      variant="optional"
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Custom sections */}
            <div className="mb-5">
              <div className="flex items-center gap-2 mb-2.5">
                <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                  Custom Sections
                </span>
                <div className="flex-1 h-px bg-gray-100" />
              </div>
              <input
                type="text"
                value={customRaw}
                onChange={(e) => setCustomRaw(e.target.value)}
                placeholder="GDPR Compliance, Data Migration Guide, Runbook…"
                className="w-full bg-white border border-gray-200 rounded-lg
                           px-3 py-2 text-sm text-gray-900 placeholder:text-gray-300
                           focus:outline-none focus:ring-2 focus:ring-primary/20
                           focus:border-primary transition-colors duration-150"
              />
              <p className="text-xs text-gray-400 mt-1.5">
                Comma-separated. These are appended after the selected sections.
              </p>
            </div>

            {/* Queued preview */}
            {allSections.length > 0 && (
              <div className="mb-5">
                <div className="flex items-center gap-2 mb-2.5">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                    Queued
                  </span>
                  <span
                    className="text-[10px] font-semibold text-blue-600 bg-blue-50
                                   border border-blue-100 px-1.5 py-0.5 rounded-full"
                  >
                    {allSections.length} sections
                  </span>
                  <div className="flex-1 h-px bg-gray-100" />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {allSections.map((s, i) => (
                    <span
                      key={s}
                      className="inline-flex items-center gap-1 px-2.5 py-1
                                     bg-blue-50 border border-blue-100 text-blue-700
                                     text-xs font-medium rounded-md"
                    >
                      <span className="text-blue-300 text-[10px] font-bold tabular-nums">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Divider */}
            <div className="h-px bg-gray-100 mb-5" />

            {/* Confirm button */}
            <button
              onClick={handleConfirm}
              disabled={loadingConf || allSections.length === 0}
              className="w-full flex items-center justify-center gap-2
                         bg-primary hover:bg-primary-hover
                         text-white text-sm font-semibold
                         px-6 py-2.5 rounded-lg shadow-sm
                         disabled:opacity-50 disabled:cursor-not-allowed
                         transition-colors duration-150"
            >
              {loadingConf ? (
                <>
                  <Spinner size="sm" className="text-white" /> Saving…
                </>
              ) : (
                <>
                  Confirm &amp; Continue
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
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* ── Right sidebar ── */}
      <div className="flex-[4] min-w-0 hidden md:block">
        <div className="h-[60px]" />

        {/* Stack detected */}
        {analysis && (
          <>
            <p
              className="text-[10px] font-bold uppercase tracking-widest
                          text-gray-400 mb-3"
            >
              Stack Detected
            </p>

            <div className="space-y-3 mb-5">
              {[
                ["Languages", analysis?.languages ?? []],
                ["Frameworks", analysis?.frameworks ?? []],
                ["Databases", analysis?.databases ?? []],
              ]
                .filter(([, items]) => items.length > 0)
                .map(([label, items]) => (
                  <div key={label}>
                    <p
                      className="text-[10px] font-bold uppercase tracking-widest
                                  text-gray-400 mb-1.5"
                    >
                      {label}
                    </p>
                    <TagRow items={items} />
                  </div>
                ))}
            </div>

            {/* DevOps flags */}
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 mb-5">
              {[
                ["has_dockerfile", "Dockerfile"],
                ["has_cicd", "CI/CD"],
                ["has_kubernetes", "Kubernetes"],
                ["has_terraform", "Terraform"],
                ["has_ansible", "Ansible"],
              ].map(([key, label]) => (
                <DevOpsFlag
                  key={key}
                  label={label}
                  active={!!analysis?.[key]}
                />
              ))}
            </div>

            <div className="h-px bg-gray-100 mb-5" />
          </>
        )}

        {/* Active project card */}
        {state.projectId && (
          <>
            <p
              className="text-[10px] font-bold uppercase tracking-widest
                          text-gray-400 mb-2"
            >
              Active Project
            </p>
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-3.5">
              <div className="text-sm font-semibold text-blue-900 mb-0.5">
                {state.metadata?.projectname}
              </div>
              <div className="text-xs text-blue-500 mb-2">
                {state.metadata?.clientname}
              </div>
              <div className="font-mono text-[10px] text-blue-300 break-all">
                {state.projectId}
              </div>
            </div>
          </>
        )}

        {/* Selection counter (visible after suggestions loaded) */}
        {suggestions.length > 0 && (
          <div className="mt-4 bg-white border border-gray-200 rounded-xl p-3.5">
            <p
              className="text-[10px] font-bold uppercase tracking-widest
                          text-gray-400 mb-2.5"
            >
              Selection
            </p>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-lg font-bold text-gray-900 tabular-nums leading-none">
                  {chosen.length}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">From AI</div>
              </div>
              <div>
                <div className="text-lg font-bold text-gray-900 tabular-nums leading-none">
                  {customSecs.length}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">Custom</div>
              </div>
              <div>
                <div
                  className={`text-lg font-bold tabular-nums leading-none
                                 ${allSections.length > 0 ? "text-primary" : "text-gray-300"}`}
                >
                  {allSections.length}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">Total</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
