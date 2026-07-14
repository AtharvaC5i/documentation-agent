// src/components/input/InputModeToggle.jsx
import { PencilLine, Paperclip } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";

const MODES = [
  {
    key: "paste",
    label: "Paste text",
    description: "Type or paste your document",
    icon: PencilLine,
  },
  {
    key: "upload",
    label: "Upload files",
    description: "PDF, DOCX, TXT or MD",
    icon: Paperclip,
  },
];

export default function InputModeToggle() {
  const { inputMode, setInputMode } = useAppStore();

  return (
    <div className="flex flex-col items-center gap-2 mb-8">
      {/* Label */}
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.07em] text-brand-muted">
        Input mode
      </p>

      {/* Toggle card */}
      <div className="flex items-stretch gap-1.5 p-1 bg-[#EDE9F7] rounded-[14px]">
        {MODES.map(({ key, label, description, icon: Icon }) => {
          const isActive = inputMode === key;
          return (
            <button
              key={key}
              onClick={() => setInputMode(key)}
              aria-pressed={isActive}
              className={`
                relative flex items-center gap-3 px-5 py-3 rounded-[10px]
                transition-all duration-200 select-none group
                ${isActive
                  ? "bg-white shadow-[0_1px_8px_rgba(124,92,191,0.18)] border border-brand-border"
                  : "hover:bg-white/50 border border-transparent"
                }
              `}
            >
              {/* Icon container */}
              <span
                className={`
                  flex items-center justify-center w-8 h-8 rounded-[8px]
                  shrink-0 transition-all duration-200
                  ${isActive
                    ? "bg-gradient-to-br from-brand-navy to-brand-purple text-white shadow-purple"
                    : "bg-[#DDD4F5] text-brand-muted group-hover:bg-[#CEC3EF] group-hover:text-brand-navy"
                  }
                `}
              >
                <Icon size={15} strokeWidth={2} />
              </span>

              {/* Text */}
              <span className="flex flex-col items-start gap-0.5">
                <span
                  className={`
                    text-[0.84rem] font-semibold leading-none transition-colors duration-200
                    ${isActive ? "text-brand-navy" : "text-brand-muted group-hover:text-brand-navy"}
                  `}
                >
                  {label}
                </span>
                <span
                  className={`
                    text-[0.7rem] leading-none transition-colors duration-200
                    ${isActive ? "text-brand-purple" : "text-brand-muted/70 group-hover:text-brand-muted"}
                  `}
                >
                  {description}
                </span>
              </span>

              {/* Active indicator dot */}
              {isActive && (
                <span className="absolute bottom-1.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-brand-purple" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
