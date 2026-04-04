import { useAppStore } from "../../store/useAppStore";

const MODES = [
  { key: "paste", label: "✏️  Paste text" },
  { key: "upload", label: "📎  Upload files" },
];

export default function InputModeToggle() {
  const { inputMode, setInputMode } = useAppStore();

  return (
    <div className="flex gap-2 mb-6">
      {MODES.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => setInputMode(key)}
          className={`
            px-5 py-2 rounded-full text-sm font-medium border transition-all duration-200
            ${
              inputMode === key
                ? "bg-brand-navy text-white border-brand-navy shadow-sm"
                : "bg-white text-brand-navy border-brand-border hover:border-brand-purple hover:bg-brand-purple-light"
            }
          `}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
