const SIZE_MAP = {
  sm: "w-3.5 h-3.5 border",
  md: "w-5 h-5 border-2",
  lg: "w-7 h-7 border-2",
};

export default function Spinner({ size = "md", className = "" }) {
  return (
    <span
      className={`
        ${SIZE_MAP[size] ?? SIZE_MAP.md}
        inline-block rounded-full
        border-current border-t-transparent
        animate-spin flex-shrink-0
        ${className}
      `}
      role="status"
      aria-label="Loading"
    />
  );
}
