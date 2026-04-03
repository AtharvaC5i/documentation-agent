import React from "react";
import { Check } from "lucide-react";

const STEPS = [
  { key: "upload",     label: "Upload" },
  { key: "extraction", label: "Extract" },
  { key: "conflicts",  label: "Conflicts" },
  { key: "sections",   label: "Sections" },
  { key: "generation", label: "Generate" },
  { key: "review",     label: "Review" },
  { key: "complete",   label: "Done" },
];

export default function StepIndicator({ current }) {
  const currentIdx = STEPS.findIndex((s) => s.key === current);
  return (
    <div className="steps mb-6">
      {STEPS.map((step, i) => {
        const done   = i < currentIdx;
        const active = i === currentIdx;
        return (
          <React.Fragment key={step.key}>
            <div className={`step${active ? " active" : done ? " done" : ""}`}>
              <div className="step-num">
                {done ? <Check size={11} strokeWidth={3} /> : i + 1}
              </div>
              <span style={{ whiteSpace: "nowrap" }}>{step.label}</span>
            </div>
            {i < STEPS.length - 1 && <div className="step-line" />}
          </React.Fragment>
        );
      })}
    </div>
  );
}
