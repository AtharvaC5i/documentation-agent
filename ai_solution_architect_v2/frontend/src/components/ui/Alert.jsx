const styles = {
  success: {
    wrapper: "bg-[#F0FDF4] border border-[#A7F3D0]",
    text: "text-[#065F46]",
    icon: "✓",
  },
  error: {
    wrapper: "bg-[#FFF5F5] border border-[#FCA5A5]",
    text: "text-[#9B1C1C]",
    icon: "✕",
  },
  warning: {
    wrapper: "bg-[#FFFBEB] border border-[#FCD34D]",
    text: "text-[#92400E]",
    icon: "⚠",
  },
  info: {
    wrapper: "bg-[#EDE9F7] border border-brand-border",
    text: "text-brand-navy",
    icon: "ℹ",
  },
};

export default function Alert({ type = "info", message }) {
  const s = styles[type] ?? styles.info;
  return (
    <div
      className={`flex items-start gap-3 rounded-lg px-4 py-3 text-sm ${s.wrapper}`}
    >
      <span className={`mt-0.5 font-bold shrink-0 ${s.text}`}>{s.icon}</span>
      <span className={s.text}>{message}</span>
    </div>
  );
}
