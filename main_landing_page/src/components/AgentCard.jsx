import { ArrowUpRight } from "lucide-react";

const accentConfig = {
  teal: {
    numberColor: "text-teal-600",
    taglineBg: "bg-teal-50",
    taglineText: "text-teal-700",
    taglineBorder: "border-teal-100",
    dotColor: "bg-teal-500",
    techBg: "bg-teal-50 text-teal-700 border-teal-100",
    linkColor: "text-teal-700 hover:text-teal-900",
    topBorder: "bg-teal-600",
    hoverBorder: "hover:border-teal-200",
  },
  indigo: {
    numberColor: "text-indigo-500",
    taglineBg: "bg-indigo-50",
    taglineText: "text-indigo-700",
    taglineBorder: "border-indigo-100",
    dotColor: "bg-indigo-500",
    techBg: "bg-indigo-50 text-indigo-700 border-indigo-100",
    linkColor: "text-indigo-700 hover:text-indigo-900",
    topBorder: "bg-indigo-500",
    hoverBorder: "hover:border-indigo-200",
  },
  violet: {
    numberColor: "text-violet-500",
    taglineBg: "bg-violet-50",
    taglineText: "text-violet-700",
    taglineBorder: "border-violet-100",
    dotColor: "bg-violet-500",
    techBg: "bg-violet-50 text-violet-700 border-violet-100",
    linkColor: "text-violet-700 hover:text-violet-900",
    topBorder: "bg-violet-500",
    hoverBorder: "hover:border-violet-200",
  },
};

export default function AgentCard({ agent }) {
  const { number, title, tagline, description, features, tech, url, accent } =
    agent;
  const c = accentConfig[accent];

  return (
    <div
      className={`group relative flex flex-col border border-gray-200 ${c.hoverBorder} rounded-2xl bg-white hover:shadow-lg transition-all duration-200 overflow-hidden`}
    >
      {/* Top accent bar */}
      <div className={`h-0.5 w-full ${c.topBorder} flex-shrink-0`} />

      <div className="flex flex-col p-7">
        {/* Number */}
        <span
          className={`text-xs font-bold tracking-widest uppercase mb-3 ${c.numberColor}`}
        >
          {number}
        </span>

        {/* Tagline pill — now on its own line, left-aligned, width fits content */}
        <span
          className={`
            self-start text-xs font-medium px-2.5 py-1 rounded-full mb-5
            border ${c.taglineBg} ${c.taglineText} ${c.taglineBorder}
            leading-tight whitespace-nowrap overflow-hidden text-ellipsis max-w-full
          `}
        >
          {tagline}
        </span>

        {/* Title */}
        <h3 className="text-lg font-bold text-gray-900 tracking-tight mb-3 leading-snug">
          {title}
        </h3>

        {/* Description */}
        <p className="text-sm text-gray-500 leading-relaxed mb-6">
          {description}
        </p>

        {/* Features */}
        <ul className="space-y-2.5 mb-7">
          {features.map((feature, i) => (
            <li
              key={i}
              className="flex items-start gap-2.5 text-sm text-gray-600"
            >
              <span
                className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${c.dotColor}`}
              />
              {feature}
            </li>
          ))}
        </ul>

        {/* Tech badges */}
        <div className="flex flex-wrap gap-1.5 mb-6">
          {tech.map((t) => (
            <span
              key={t}
              className={`text-xs font-medium px-2 py-0.5 rounded border ${c.techBg}`}
            >
              {t}
            </span>
          ))}
        </div>

        {/* Divider */}
        <div className="border-t border-gray-100 mb-5" />

        {/* CTA */}
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className={`inline-flex items-center gap-1.5 text-sm font-semibold transition-all duration-150 ${c.linkColor}`}
        >
          Open agent
          <ArrowUpRight
            size={15}
            strokeWidth={2.5}
            className="group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform duration-150"
          />
        </a>
      </div>
    </div>
  );
}
