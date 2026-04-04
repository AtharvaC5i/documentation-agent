import { useApp } from "../../context/AppContext";
import { useApiStatus } from "../../hooks/useApiStatus";

export default function TopBar() {
  const { state } = useApp();
  const apiOnline = useApiStatus();

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex-shrink-0">
      <div className="max-w-[1024px] mx-auto px-6 h-full flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </div>
          <span className="text-[15px] font-semibold tracking-tight text-gray-900">
            Doc<span className="text-primary">Agent</span>
          </span>
        </div>

        {/* Right */}
        <div className="flex items-center gap-3">
          {state.metadata?.project_name && (
            <span
              className="text-sm text-gray-400 hidden sm:block
                             truncate max-w-[180px] border-r border-gray-200 pr-3"
            >
              {state.metadata.project_name}
            </span>
          )}
          <div
            className={`flex items-center gap-1.5 text-[11px] font-semibold
                           px-2.5 py-1 rounded-full border ${
                             apiOnline
                               ? "bg-green-50 border-green-200 text-green-700"
                               : "bg-red-50 border-red-200 text-red-700"
                           }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                apiOnline ? "bg-green-500" : "bg-red-500"
              }`}
            />
            {apiOnline ? "API Live" : "API Offline"}
          </div>
        </div>
      </div>
    </header>
  );
}
