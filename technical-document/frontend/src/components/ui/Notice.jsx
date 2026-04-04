import { CircleCheck, CircleAlert, AlertTriangle, Info, X } from "lucide-react";
import { useState } from "react";

const CONFIG = {
  ok: { cls: "notice-ok", Icon: CircleCheck },
  error: { cls: "notice-error", Icon: CircleAlert },
  warn: { cls: "notice-warn", Icon: AlertTriangle },
  info: { cls: "notice-info", Icon: Info },
};

export default function Notice({
  kind = "info",
  children,
  dismissible = false,
  className = "",
}) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;

  const { cls, Icon } = CONFIG[kind] ?? CONFIG.info;

  return (
    <div className={`${cls} ${className}`} role="alert">
      <Icon size={15} className="flex-shrink-0 mt-0.5" aria-hidden="true" />
      <span className="flex-1 leading-relaxed">{children}</span>
      {dismissible && (
        <button
          onClick={() => setDismissed(true)}
          className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity ml-1"
          aria-label="Dismiss"
        >
          <X size={13} />
        </button>
      )}
    </div>
  );
}
