const VARIANT_MAP = {
  default: "card",
  sm: "card-sm",
  lg: "card-lg",
  blue: "card bg-info-bg border-info-border",
  green: "card bg-success-bg border-success-border",
  amber: "card bg-warning-bg border-warning-border",
  red: "card bg-danger-bg border-danger-border",
};

export default function Card({
  variant = "default",
  children,
  className = "",
}) {
  return (
    <div
      className={`${VARIANT_MAP[variant] ?? VARIANT_MAP.default} ${className}`}
    >
      {children}
    </div>
  );
}
