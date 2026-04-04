import { useNavigate, useLocation } from "react-router-dom";
import { useApp } from "../../context/AppContext";

const STEPS = [
  { label: "Ingest", path: "/ingest" },
  { label: "Sections", path: "/project/:id/sections" },
  { label: "Context", path: "/project/:id/context" },
  { label: "Generate", path: "/project/:id/generate" },
  { label: "Review", path: "/project/:id/review" },
  { label: "Assembly", path: "/project/:id/assembly" },
  { label: "Report", path: "/project/:id/report" },
];

function resolvedPath(pattern, projectId) {
  return projectId ? pattern.replace(":id", projectId) : pattern;
}

function CheckIcon() {
  return (
    <svg
      width="8"
      height="8"
      viewBox="0 0 12 12"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="2 6 5 9 10 3" />
    </svg>
  );
}

export default function Stepper() {
  const { state } = useApp();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const projectId = state.projectId;

  const activeIndex = STEPS.findIndex(
    (s) => pathname === resolvedPath(s.path, projectId),
  );

  return (
    <nav
      aria-label="Progress steps"
      className="bg-white border-b border-gray-200"
    >
      <div className="max-w-[1024px] mx-auto px-6">
        <ol className="flex items-stretch" role="list">
          {STEPS.map((step, i) => {
            const isCompleted = i < activeIndex;
            const isActive = i === activeIndex;
            const isPending = i > activeIndex;
            const isClickable = isCompleted && !!projectId;

            return (
              <li key={step.label} className="flex-1 relative flex">
                <button
                  onClick={() => {
                    if (isClickable)
                      navigate(resolvedPath(step.path, projectId));
                  }}
                  disabled={isPending || (!projectId && i > 0)}
                  aria-current={isActive ? "step" : undefined}
                  className={`
                    flex-1 flex items-center justify-center gap-2
                    py-3.5 text-xs border-b-2 transition-all duration-150
                    ${
                      isActive
                        ? "border-primary text-primary font-semibold"
                        : isCompleted
                          ? "border-transparent text-gray-500 font-medium hover:text-gray-800 hover:bg-gray-50"
                          : "border-transparent text-gray-400 font-medium cursor-default"
                    }
                    disabled:cursor-default
                  `}
                >
                  {/* Circle indicator */}
                  <span
                    className={`
                    w-5 h-5 rounded-full flex items-center justify-center
                    flex-shrink-0 text-[10px] font-bold leading-none
                    ${
                      isActive
                        ? "bg-primary text-white"
                        : isCompleted
                          ? "bg-green-500 text-white"
                          : "bg-gray-100 text-gray-400 border border-gray-200"
                    }
                  `}
                  >
                    {isCompleted ? <CheckIcon /> : i + 1}
                  </span>

                  {/* Label — hidden on small screens */}
                  <span className="hidden sm:block truncate">{step.label}</span>
                </button>

                {/* Vertical divider between steps */}
                {i < STEPS.length - 1 && (
                  <div
                    className="absolute right-0 top-1/2 -translate-y-1/2
                                  w-px h-5 bg-gray-200"
                  />
                )}
              </li>
            );
          })}
        </ol>
      </div>
    </nav>
  );
}
