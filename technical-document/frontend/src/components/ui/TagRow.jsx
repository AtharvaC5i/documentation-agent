export default function TagRow({ label, items = [], className = "" }) {
  if (!items?.length) return null;

  return (
    <div className={`flex items-center gap-2 flex-wrap ${className}`}>
      {label && (
        <span className="text-[11px] font-bold uppercase tracking-widest text-text-faint">
          {label}
        </span>
      )}
      {items.map((item) => (
        <span key={item} className="tag">
          {item}
        </span>
      ))}
    </div>
  );
}
