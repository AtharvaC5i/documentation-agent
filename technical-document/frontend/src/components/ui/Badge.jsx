const VARIANTS = {
  gray: "badge-gray",
  green: "badge-green",
  amber: "badge-amber",
  red: "badge-red",
  blue: "badge-blue",
  teal: "badge-teal",
};

export default function Badge({ variant = "gray", children, className = "" }) {
  return (
    <span className={`${VARIANTS[variant] ?? VARIANTS.gray} ${className}`}>
      {children}
    </span>
  );
}
