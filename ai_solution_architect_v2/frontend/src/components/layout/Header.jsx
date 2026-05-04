// src/components/layout/Header.jsx
import { Sparkles } from "lucide-react";

export default function Header() {
  return (
    <div className="flex flex-col items-center text-center mb-10 gap-4">
      {/* Eyebrow badge */}

      {/* Main title */}
      <div className="flex flex-col items-center gap-2">
        <h1 className="font-serif text-[2.6rem] font-normal leading-tight tracking-tight text-brand-navy">
          PPT
          <span className="relative mx-2.5">
            <span className="relative z-10 text-brand-purple">Forge</span>
            {/* Underline accent */}
            <span className="absolute left-0 -bottom-1 w-full h-[3px] rounded-full bg-gradient-to-r from-brand-navy to-brand-purple" />
          </span>
          AI
        </h1>

        {/* Subtitle */}
        <p className="text-brand-muted text-[1rem] font-normal max-w-[520px] leading-relaxed">
          Turn your BRD and technical docs into a{" "}
          <span className="text-brand-purple font-medium">
            consulting-quality architecture deck
          </span>{" "}
          in seconds.
        </p>
      </div>
    </div>
  );
}
