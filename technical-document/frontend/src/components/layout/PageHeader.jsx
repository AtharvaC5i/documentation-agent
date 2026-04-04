export default function PageHeader({
  title,
  subtitle,
  action,
  className = "",
}) {
  return (
    <div className={`mb-6 ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-text tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm text-text-muted mt-1 leading-relaxed">
              {subtitle}
            </p>
          )}
        </div>
        {action && <div className="flex-shrink-0 mt-0.5">{action}</div>}
      </div>
      <div className="h-px bg-divider mt-4" />
    </div>
  );
}
