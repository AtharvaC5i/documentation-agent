import { useAppStore } from "../../store/useAppStore";

function FieldLabel({ children, optional = false }) {
  return (
    <p className="text-[0.78rem] font-semibold uppercase tracking-[0.06em] text-brand-navy mb-1.5">
      {children}
      {optional && (
        <span className="font-normal normal-case tracking-normal text-brand-muted ml-1">
          (optional)
        </span>
      )}
    </p>
  );
}

function StyledTextarea({ value, onChange, placeholder, rows = 12 }) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      className="
        w-full bg-white border border-brand-border rounded-[10px]
        px-4 py-3 text-[0.88rem] text-[#1A1A2E] font-sans
        resize-y shadow-sm
        placeholder:text-brand-muted
        focus:outline-none focus:border-brand-purple focus:ring-2 focus:ring-brand-purple/10
        transition-all duration-200
      "
    />
  );
}

export default function TextInputPanel() {
  const { brdText, setBrdText, techDocText, setTechDocText } = useAppStore();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <FieldLabel>Business Requirement Document</FieldLabel>
        <StyledTextarea
          value={brdText}
          onChange={setBrdText}
          placeholder="Describe the project goal, users, features, constraints…"
        />
      </div>

      <div>
        <FieldLabel optional>Technical Documentation</FieldLabel>
        <StyledTextarea
          value={techDocText}
          onChange={setTechDocText}
          placeholder="Existing systems, APIs, data models, infrastructure constraints…"
        />
      </div>
    </div>
  );
}
