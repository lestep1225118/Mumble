import { useState, useCallback, useMemo } from "react";
import { parseCSV, keyMatchReason, bpmMatch, getRelativeKey, KEY_NAMES, MODE_NAMES } from "./utils.js";
import UploadZone from "./UploadZone.jsx";
import ResultsTable from "./ResultsTable.jsx";

const MANUAL_SENTINEL = "__manual__";

export default function App() {
  const [songs, setSongs] = useState(null);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState("");
  const [bpmRange, setBpmRange] = useState(10);
  const [includeParallel, setIncludeParallel] = useState(false);
  const [sortBy, setSortBy] = useState("tempoDiff");
  const [filterReason, setFilterReason] = useState("all");
  const [mode, setMode] = useState("song"); // "song" | "manual"

  // Manual mode state
  const [manualKey, setManualKey] = useState(7);   // G
  const [manualMode, setManualMode] = useState(0); // minor
  const [manualBpm, setManualBpm] = useState(120);

  const handleCSV = useCallback((text) => {
    const parsed = parseCSV(text);
    setSongs(parsed);
    setSelected(null);
    setSearch("");
    setFilterReason("all");
    setMode("song");
  }, []);

  // Build a synthetic "selected" object for manual mode
  const effectiveSelected = useMemo(() => {
    if (mode === "manual") {
      return {
        name: "Manual entry",
        artist: "",
        key: manualKey,
        mode: manualMode,
        tempo: manualBpm,
        keyLabel: `${KEY_NAMES[manualKey]} ${MODE_NAMES[manualMode]}`,
        _isManual: true,
      };
    }
    return selected;
  }, [mode, manualKey, manualMode, manualBpm, selected]);

  const filtered = useMemo(() => {
    if (!songs || !effectiveSelected) return [];
    return songs
      .filter(s => !effectiveSelected._isManual ? s !== selected : true)
      .map(s => {
        const reason = keyMatchReason(s.key, s.mode, effectiveSelected.key, effectiveSelected.mode);
        if (!reason) return null;
        if (!includeParallel && reason === "Parallel key") return null;
        const bpm = bpmMatch(s.tempo, effectiveSelected.tempo, bpmRange);
        if (!bpm) return null;
        return { ...s, reason, tempoDiff: bpm.diff, bpmVariant: bpm.label, adjustedTempo: bpm.adjustedTempo };
      })
      .filter(Boolean)
      .filter(s => filterReason === "all" || s.reason === filterReason)
      .sort((a, b) => {
        if (sortBy === "tempoDiff") return a.tempoDiff - b.tempoDiff;
        if (sortBy === "popularity") return b.popularity - a.popularity;
        if (sortBy === "energy") return b.energy - a.energy;
        return 0;
      });
  }, [songs, effectiveSelected, selected, bpmRange, includeParallel, sortBy, filterReason]);

  const songSearch = useMemo(() => {
    if (!songs || !search) return [];
    const q = search.toLowerCase();
    return songs.filter(s =>
      s.name.toLowerCase().includes(q) || s.artist.toLowerCase().includes(q)
    ).slice(0, 8);
  }, [songs, search]);

  const relKey = effectiveSelected ? getRelativeKey(effectiveSelected.key, effectiveSelected.mode) : null;

  const pill = (label, color) => (
    <span key={label} style={{ background: "#1a1040", border: `1px solid ${color}33`, color, borderRadius: 6, padding: "0.25rem 0.65rem", fontSize: "0.78rem" }}>{label}</span>
  );

  const btn = (label, active, onClick) => (
    <button key={label} onClick={onClick} style={{
      background: active ? "#3b1f6e" : "none",
      border: `1px solid ${active ? "#7c3aed" : "#2d1f5e"}`,
      color: active ? "#c4b5fd" : "#475569",
      borderRadius: 6, padding: "0.2rem 0.6rem",
      fontSize: "0.75rem", cursor: "pointer", fontFamily: "inherit"
    }}>{label}</button>
  );

  const inputStyle = {
    background: "#080810", border: "1px solid #2d1f5e", borderRadius: 8,
    padding: "0.5rem 0.75rem", color: "#e2e8f0", fontSize: "0.85rem",
    fontFamily: "inherit", outline: "none",
  };

  const selectStyle = {
    ...inputStyle, cursor: "pointer", appearance: "none", paddingRight: "1.5rem",
  };

  return (
    <div style={{
      maxWidth: 1020, margin: "0 auto", padding: "2.5rem 1.5rem",
      backgroundImage: "radial-gradient(ellipse 80% 40% at 50% 0%, #1a0a3a 0%, transparent 70%)",
      minHeight: "100vh",
    }}>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <div style={{ fontSize: "0.65rem", letterSpacing: "0.2em", color: "#6b21a8", marginBottom: "0.4rem", textTransform: "uppercase" }}>
          Key / BPM Matcher
        </div>
        <h1 style={{ fontFamily: "'Syne', sans-serif", fontSize: "clamp(1.8rem, 5vw, 3rem)", fontWeight: 800, color: "#f1f5f9", lineHeight: 1, letterSpacing: "-0.02em" }}>
          MUMBLE
        </h1>
      </div>

      {!songs && <UploadZone onFile={handleCSV} />}

      {songs && (
        <>
          {/* Mode tabs */}
          <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
            {[["song", "Match by Song"], ["manual", "Match by Key & BPM"]].map(([v, l]) => (
              <button key={v} onClick={() => { setMode(v); setFilterReason("all"); }} style={{
                background: mode === v ? "#3b1f6e" : "#0d0b1e",
                border: `1px solid ${mode === v ? "#7c3aed" : "#1e1b4b"}`,
                color: mode === v ? "#c4b5fd" : "#475569",
                borderRadius: 8, padding: "0.45rem 1rem",
                fontSize: "0.82rem", cursor: "pointer", fontFamily: "inherit",
                transition: "all 0.15s",
              }}>{l}</button>
            ))}
            <button onClick={() => { setSongs(null); setSelected(null); }} style={{
              marginLeft: "auto", background: "none", border: "1px solid #2d1f5e",
              color: "#475569", borderRadius: 8, padding: "0.45rem 1rem",
              fontSize: "0.75rem", cursor: "pointer", fontFamily: "inherit",
            }}>↑ new csv</button>
          </div>

          {/* Reference panel */}
          <div style={{ background: "#0d0b1e", border: "1px solid #1e1b4b", borderRadius: 12, padding: "1.25rem", marginBottom: "1.25rem" }}>
            <div style={{ fontSize: "0.65rem", letterSpacing: "0.15em", color: "#6b21a8", marginBottom: "0.75rem", textTransform: "uppercase" }}>
              {mode === "song" ? "Reference Track" : "Manual Reference"}
            </div>

            {mode === "manual" ? (
              /* Manual inputs */
              <div style={{ display: "flex", gap: "1.25rem", flexWrap: "wrap", alignItems: "flex-end" }}>
                <div>
                  <label style={{ display: "block", fontSize: "0.68rem", color: "#6b21a8", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "0.4rem" }}>Key</label>
                  <div style={{ position: "relative" }}>
                    <select value={manualKey} onChange={e => setManualKey(Number(e.target.value))} style={selectStyle}>
                      {KEY_NAMES.map((k, i) => <option key={i} value={i}>{k}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "0.68rem", color: "#6b21a8", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "0.4rem" }}>Mode</label>
                  <select value={manualMode} onChange={e => setManualMode(Number(e.target.value))} style={selectStyle}>
                    <option value={0}>minor</option>
                    <option value={1}>major</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: "block", fontSize: "0.68rem", color: "#6b21a8", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "0.4rem" }}>BPM</label>
                  <input
                    type="number" min={20} max={300} value={manualBpm}
                    onChange={e => setManualBpm(Number(e.target.value))}
                    style={{ ...inputStyle, width: 80 }}
                  />
                </div>
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", paddingBottom: "0.1rem" }}>
                  {pill(`${KEY_NAMES[manualKey]} ${MODE_NAMES[manualMode]}`, "#a78bfa")}
                  {pill(`${manualBpm} BPM`, "#34d399")}
                  {relKey && pill(`rel: ${KEY_NAMES[relKey.key]} ${MODE_NAMES[relKey.mode]}`, "#60a5fa")}
                </div>
              </div>
            ) : (
              /* Song search */
              <>
                {selected && (
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap", marginBottom: "0.9rem" }}>
                    <div>
                      <div style={{ fontFamily: "'Syne', sans-serif", fontSize: "1.1rem", fontWeight: 700, color: "#e2e8f0" }}>{selected.name}</div>
                      <div style={{ color: "#64748b", fontSize: "0.82rem" }}>{selected.artist}</div>
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                      {pill(selected.keyLabel, "#a78bfa")}
                      {pill(`${selected.tempo.toFixed(0)} BPM`, "#34d399")}
                      {relKey && pill(`rel: ${KEY_NAMES[relKey.key]} ${MODE_NAMES[relKey.mode]}`, "#60a5fa")}
                    </div>
                  </div>
                )}
                {!selected && (
                  <div style={{ color: "#64748b", fontSize: "0.85rem", marginBottom: "0.75rem" }}>Search for a track to begin.</div>
                )}
                <div style={{ position: "relative" }}>
                  <input
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder="Search for any song in your playlist…"
                    style={{ width: "100%", ...inputStyle }}
                  />
                  {songSearch.length > 0 && (
                    <div style={{ position: "absolute", top: "calc(100% + 2px)", left: 0, right: 0, background: "#0f0d24", border: "1px solid #2d1f5e", borderRadius: 8, zIndex: 10, overflow: "hidden", boxShadow: "0 8px 24px #00000088" }}>
                      {songSearch.map((s, i) => (
                        <div
                          key={i}
                          onClick={() => { setSelected(s); setSearch(""); setFilterReason("all"); }}
                          style={{ padding: "0.6rem 0.9rem", cursor: "pointer", borderBottom: "1px solid #1a1640", transition: "background 0.15s" }}
                          onMouseEnter={e => e.currentTarget.style.background = "#1a1640"}
                          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                        >
                          <div style={{ color: "#e2e8f0", fontSize: "0.85rem" }}>{s.name}</div>
                          <div style={{ color: "#475569", fontSize: "0.75rem" }}>{s.artist} · {s.keyLabel} · {s.tempo.toFixed(0)} BPM</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Controls */}
          <div style={{ display: "flex", gap: "1.25rem", flexWrap: "wrap", alignItems: "center", marginBottom: "1.25rem", background: "#0d0b1e", border: "1px solid #1e1b4b", borderRadius: 12, padding: "0.9rem 1.25rem" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <span style={{ fontSize: "0.68rem", color: "#6b21a8", letterSpacing: "0.1em", textTransform: "uppercase" }}>±BPM</span>
              <input type="range" min={2} max={20} value={bpmRange} onChange={e => setBpmRange(Number(e.target.value))} style={{ width: 90 }} />
              <span style={{ color: "#a78bfa", fontSize: "0.85rem", minWidth: 20 }}>{bpmRange}</span>
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", cursor: "pointer", fontSize: "0.78rem", color: "#64748b" }}>
              <input type="checkbox" checked={includeParallel} onChange={e => setIncludeParallel(e.target.checked)} style={{ accentColor: "#7c3aed" }} />
              parallel keys
            </label>
            <div style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
              <span style={{ fontSize: "0.68rem", color: "#6b21a8", letterSpacing: "0.1em", textTransform: "uppercase", marginRight: 2 }}>Sort</span>
              {btn("Δ BPM", sortBy === "tempoDiff", () => setSortBy("tempoDiff"))}
              {btn("Pop", sortBy === "popularity", () => setSortBy("popularity"))}
              {btn("Energy", sortBy === "energy", () => setSortBy("energy"))}
            </div>
            <div style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
              <span style={{ fontSize: "0.68rem", color: "#6b21a8", letterSpacing: "0.1em", textTransform: "uppercase", marginRight: 2 }}>Filter</span>
              {btn("All", filterReason === "all", () => setFilterReason("all"))}
              {btn("Same", filterReason === "Same key", () => setFilterReason("Same key"))}
              {btn("Relative", filterReason === "Relative key", () => setFilterReason("Relative key"))}
              {includeParallel && btn("Parallel", filterReason === "Parallel key", () => setFilterReason("Parallel key"))}
            </div>
          </div>

          {/* Stats */}
          {effectiveSelected && (mode === "manual" || selected) && (
            <>
              <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem", flexWrap: "wrap" }}>
                {[
                  ["matches", filtered.length, "#c4b5fd"],
                  ["same key", filtered.filter(r => r.reason === "Same key").length, "#a78bfa"],
                  ["relative", filtered.filter(r => r.reason === "Relative key").length, "#34d399"],
                  ...(includeParallel ? [["parallel", filtered.filter(r => r.reason === "Parallel key").length, "#60a5fa"]] : []),
                ].map(([l, v, c]) => (
                  <div key={l} style={{ background: "#0d0b1e", border: "1px solid #1e1b4b", borderRadius: 8, padding: "0.5rem 1rem", minWidth: 80 }}>
                    <div style={{ fontFamily: "'Syne', sans-serif", fontSize: "1.4rem", fontWeight: 800, color: c, lineHeight: 1 }}>{v}</div>
                    <div style={{ fontSize: "0.65rem", color: "#475569", textTransform: "uppercase", letterSpacing: "0.1em", marginTop: 2 }}>{l}</div>
                  </div>
                ))}
                <div style={{ background: "#0d0b1e", border: "1px solid #1e1b4b", borderRadius: 8, padding: "0.5rem 1rem", minWidth: 80 }}>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontSize: "1.4rem", fontWeight: 800, color: "#94a3b8", lineHeight: 1 }}>{songs.length}</div>
                  <div style={{ fontSize: "0.65rem", color: "#475569", textTransform: "uppercase", letterSpacing: "0.1em", marginTop: 2 }}>total songs</div>
                </div>
              </div>
              <ResultsTable
                results={filtered}
                onSelectSong={(s) => {
                  if (mode === "song") { setSelected(s); setFilterReason("all"); }
                  else {
                    setManualKey(s.key);
                    setManualMode(s.mode);
                    setManualBpm(Math.round(s.tempo));
                  }
                }}
              />
            </>
          )}

          {mode === "song" && !selected && (
            <div style={{ textAlign: "center", color: "#334155", padding: "3rem", fontSize: "0.85rem" }}>
              Search for a track above to begin matching.
            </div>
          )}
        </>
      )}
    </div>
  );
}
