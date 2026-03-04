export default function MiniBar({ value, color }) {
  return (
    <div style={{ width: 48, height: 6, background: "#1e293b", borderRadius: 3, overflow: "hidden" }}>
      <div style={{
        width: `${Math.min(100, Math.round(value * 100))}%`,
        height: "100%",
        background: color,
        borderRadius: 3,
        transition: "width 0.3s"
      }} />
    </div>
  );
}
