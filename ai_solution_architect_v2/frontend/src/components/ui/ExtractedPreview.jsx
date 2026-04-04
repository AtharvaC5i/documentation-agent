import { useState } from "react";

export default function ExtractedPreview({ text }) {
  const [open, setOpen] = useState(false);
  const preview = text?.slice(0, 2000) ?? "";
  const truncated = text?.length > 2000;

  return (
    <div className="mt-2 border border-brand-border rounded-[8px] overflow-hidden text-sm">
      <button
        onClick={() => setOpen((o) => !o)}
        className="
          w-full flex items-center justify-between
          px-4 py-2.5 bg-white
          text-brand-purple font-medium text-[0.82rem]
          hover:bg-brand-purple-light transition-colors duration-150
        "
      >
        <span>Preview extracted text</span>
        <svg
          className={`w-4 h-4 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {open && (
        <div className="px-4 py-3 bg-[#FAFAFA] border-t border-brand-border">
          <pre className="text-[0.78rem] text-[#1A1A2E] whitespace-pre-wrap break-words font-mono leading-relaxed">
            {preview}
            {truncated && <span className="text-brand-muted">…</span>}
          </pre>
        </div>
      )}
    </div>
  );
}
