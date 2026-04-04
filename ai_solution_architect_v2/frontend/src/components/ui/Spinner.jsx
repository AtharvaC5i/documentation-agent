export default function Spinner({ size = "md" }) {
  const sizeMap = { sm: "w-4 h-4", md: "w-5 h-5", lg: "w-6 h-6" };
  return (
    <span
      className={`inline-block rounded-full border-2 border-transparent border-t-current animate-spin ${sizeMap[size]}`}
      role="status"
      aria-label="Loading"
    />
  );
}
