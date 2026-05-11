import MiniBar from './MiniBar.jsx';

const REASON_STYLE = {
  "Same key":     { bg: "#3b1f6e", color: "#c4b5fd", dot: "#a78bfa" },
  "Relative key": { bg: "#064e3b", color: "#6ee7b7", dot: "#34d399" },
  "Parallel key": { bg: "#1e3a5f", color: "#93c5fd", dot: "#60a5fa" },
  "Perfect fifth up": { bg: "#3b2a00", color: "#fde68a", dot: "#f59e0b" },
  "Perfect fifth down": { bg: "#2a1b00", color: "#fbbf24", dot: "#f59e0b" },
  "Pitch tolerance": { bg: "#0f3d2e", color: "#a7f3d0", dot: "#22c55e" },
  "Relative pitch tolerance": { bg: "#153b5d", color: "#93c5fd", dot: "#60a5fa" },
};

export default function ResultsTable({ results, onSelectSong }) {
  if (results.length === 0) {
    return (
      <div style={{ textAlign: "center", color: "#334155", padding: "3rem", fontSize: "0.85rem" }}>
        No matches found — try widening the BPM range, increasing semitone tolerance, or enabling circle of fifths.
      </div>
    );
  }

  const cols = ["Track", "Artist", "Key", "Match", "Pitch", "BPM", "Δ", "Pop", "Energy", "Dance", "Valence"];

  return (
    <div style={{ overflowX: "auto", borderRadius: 12, border: "1px solid #1e1b4b" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
        <thead>
          <tr style={{ background: "#0d0b1e", borderBottom: "1px solid #1e1b4b" }}>
            {cols.map(h => (
              <th key={h} style={{
                padding: "0.65rem 0.85rem", textAlign: "left",
                color: "#4c1d95", fontWeight: 500,
                letterSpacing: "0.08em", fontSize: "0.68rem",
                textTransform: "uppercase", whiteSpace: "nowrap"
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => {
            const rs = REASON_STYLE[r.reason] || {};
            return (
              <tr
                key={i}
                onClick={() => onSelectSong(r)}
                title="Click to use this song as reference"
                style={{
                  borderBottom: "1px solid #0f0d22",
                  cursor: "pointer",
                  background: i % 2 === 0 ? "#09091a" : "#080810",
                  transition: "background 0.15s",
                }}
                onMouseEnter={e => e.currentTarget.style.background = "#12102a"}
                onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? "#09091a" : "#080810"}
              >
                <td style={{ padding: "0.55rem 0.85rem", color: "#e2e8f0", maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={r.name}>{r.name}</td>
                <td style={{ padding: "0.55rem 0.85rem", color: "#64748b", maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={r.artist}>{r.artist}</td>
                <td style={{ padding: "0.55rem 0.85rem", color: "#94a3b8", whiteSpace: "nowrap" }}>{r.keyLabel}</td>
                <td style={{ padding: "0.55rem 0.85rem" }}>
                  <span style={{ background: rs.bg, color: rs.color, borderRadius: 5, padding: "0.18rem 0.5rem", fontSize: "0.7rem", whiteSpace: "nowrap", letterSpacing: "0.05em" }}>
                    <span style={{ display: "inline-block", width: 6, height: 6, borderRadius: "50%", background: rs.dot, marginRight: 5, verticalAlign: "middle" }} />
                    {r.reason}
                  </span>
                </td>
                <td style={{ padding: "0.55rem 0.85rem", whiteSpace: "nowrap" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <MiniBar value={r.pitchMeterValue ?? 0} color="#60a5fa" />
                    <span style={{ color: "#94a3b8", fontSize: "0.75rem", minWidth: 38, textAlign: "right" }}>
                      {r.pitchShiftText ?? "0"} semis
                    </span>
                  </div>
                </td>
                <td style={{ padding: "0.55rem 0.85rem", color: "#a78bfa" }}>
                  {r.tempo.toFixed(0)}
                  {r.bpmVariant && (
                    <span style={{ marginLeft: 5, background: "#1a2a1a", color: "#4ade80", border: "1px solid #16532444", borderRadius: 4, padding: "0.1rem 0.35rem", fontSize: "0.68rem" }}>{r.bpmVariant}</span>
                  )}
                </td>
                <td style={{ padding: "0.55rem 0.85rem", color: "#334155" }}>±{r.tempoDiff.toFixed(1)}</td>
                <td style={{ padding: "0.55rem 0.85rem" }}><MiniBar value={r.popularity / 100} color="#7c3aed" /></td>
                <td style={{ padding: "0.55rem 0.85rem" }}><MiniBar value={r.energy} color="#f59e0b" /></td>
                <td style={{ padding: "0.55rem 0.85rem" }}><MiniBar value={r.danceability} color="#10b981" /></td>
                <td style={{ padding: "0.55rem 0.85rem" }}><MiniBar value={r.valence} color="#ec4899" /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
