export const KEY_NAMES = ["C","C♯","D","D♯","E","F","F♯","G","G♯","A","A♯","B"];
export const MODE_NAMES = { 0: "minor", 1: "major" };

export function getRelativeKey(key, mode) {
  if (mode === 0) return { key: (key + 3) % 12, mode: 1 };
  return { key: (key + 9) % 12, mode: 0 };
}

function shiftKey(key, mode, semitones) {
  return { key: (key + semitones + 1200) % 12, mode };
}

function clampInt(value, min, max) {
  const n = typeof value === "number" ? value : parseInt(value, 10);
  if (Number.isNaN(n)) return min;
  return Math.max(min, Math.min(max, n));
}

/**
 * DJ-friendly key compatibility with optional circle-of-fifths neighbors and a semitone tolerance.
 *
 * Rules (ported from backend logic):
 * - Same key (same mode)
 * - Relative major/minor (opposite mode, same tonic pitch classes)
 * - Same mode: source key shifted by d semitones, for d in [-pitchSemitoneRange, pitchSemitoneRange]
 * - Relative mode: relative key shifted by d semitones (same idea, but relative mode)
 * - Optional: perfect fifth neighbors (source ± 7 semitones) when includeFifths=true
 *
 * Parallel keys (same tonic, opposite mode) are handled separately via includeParallel.
 */
export function getKeyCompatibilityMatch(
  songKey,
  songMode,
  refKey,
  refMode,
  pitchSemitoneRange = 1,
  includeFifths = true,
  includeParallel = false
) {
  const r = clampInt(pitchSemitoneRange, 0, 11);
  const rel = getRelativeKey(refKey, refMode);

  // 1) Exact match
  if (songKey === refKey && songMode === refMode) {
    return { compatible: true, reason: "Same key", pitchShift: 0 };
  }

  // 2) Exact relative match
  if (songKey === rel.key && songMode === rel.mode) {
    return { compatible: true, reason: "Relative key", pitchShift: 0 };
  }

  // 3) Perfect fifth neighbors (same mode only)
  if (includeFifths && songMode === refMode) {
    const fifthUp = shiftKey(refKey, refMode, 7).key;
    const fifthDown = shiftKey(refKey, refMode, -7).key;
    if (songKey === fifthUp) return { compatible: true, reason: "Perfect fifth up", pitchShift: 7 };
    if (songKey === fifthDown) return { compatible: true, reason: "Perfect fifth down", pitchShift: -7 };
  }

  // 4) Same mode pitch tolerance (ref shifted by d)
  if (songMode === refMode) {
    for (let d = -r; d <= r; d++) {
      if (songKey === shiftKey(refKey, refMode, d).key) {
        return { compatible: true, reason: "Pitch tolerance", pitchShift: d };
      }
    }
  }

  // 5) Relative mode pitch tolerance (relative shifted by d)
  if (songMode === rel.mode) {
    for (let d = -r; d <= r; d++) {
      if (songKey === shiftKey(rel.key, rel.mode, d).key) {
        return { compatible: true, reason: "Relative pitch tolerance", pitchShift: d };
      }
    }
  }

  // 6) Parallel keys (same tonic, opposite mode)
  if (includeParallel && songKey === refKey && songMode !== refMode) {
    return { compatible: true, reason: "Parallel key", pitchShift: 0 };
  }

  return { compatible: false, reason: null, pitchShift: null };
}

export function keyMatchReason(songKey, songMode, refKey, refMode) {
  if (songKey === refKey && songMode === refMode) return "Same key";
  const rel = getRelativeKey(refKey, refMode);
  if (songKey === rel.key && songMode === rel.mode) return "Relative key";
  if (songKey === refKey && songMode !== refMode) return "Parallel key";
  return null;
}

// Returns the closest BPM match across original, half, and double — and which variant matched
export function bpmMatch(songTempo, refTempo, range) {
  const candidates = [
    { tempo: songTempo,        label: null },
    { tempo: songTempo * 2,    label: "2x" },
    { tempo: songTempo / 2,    label: "½x" },
  ];
  let best = null;
  for (const c of candidates) {
    const diff = Math.abs(c.tempo - refTempo);
    if (diff <= range && (!best || diff < best.diff)) {
      best = { diff, label: c.label, adjustedTempo: c.tempo };
    }
  }
  return best; // null if no match
}

function splitCSVLine(line) {
  const cols = [];
  let cur = "", inQ = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQ && line[i + 1] === '"') { cur += '"'; i++; }
      else inQ = !inQ;
    } else if (ch === ',' && !inQ) {
      cols.push(cur.trim());
      cur = "";
    } else {
      cur += ch;
    }
  }
  cols.push(cur.trim());
  return cols;
}

export function parseCSV(text) {
  const lines = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim().split("\n");
  const rawHeaders = splitCSVLine(lines[0]).map(h => h.replace(/^"|"$/g, "").trim());

  const idx = (name) => rawHeaders.findIndex(h => h.toLowerCase() === name.toLowerCase());
  const iName   = idx("Track Name");
  const iArtist = idx("Artist Name(s)");
  const iAlbum  = idx("Album Name");
  const iTempo  = idx("Tempo");
  const iKey    = idx("Key");
  const iMode   = idx("Mode");
  const iPop    = idx("Popularity");
  const iEnergy = idx("Energy");
  const iDance  = idx("Danceability");
  const iVal    = idx("Valence");

  const getCol = (cols, i) => (i >= 0 && cols[i] != null) ? cols[i].replace(/^"|"$/g, "").trim() : "";

  const songs = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const cols = splitCSVLine(line);

    const tempo = parseFloat(getCol(cols, iTempo));
    const key   = Math.round(parseFloat(getCol(cols, iKey)));
    const mode  = Math.round(parseFloat(getCol(cols, iMode)));

    if (isNaN(tempo) || isNaN(key) || isNaN(mode)) continue;
    if (key < 0 || key > 11 || mode < 0 || mode > 1) continue;
    if (tempo < 20 || tempo > 300) continue;

    const name   = getCol(cols, iName) || "Unknown";
    const artist = getCol(cols, iArtist) || "Unknown";
    if (name === "Unknown" && artist === "Unknown") continue;

    songs.push({
      name,
      artist,
      album:        getCol(cols, iAlbum) || "",
      tempo,
      key,
      mode,
      keyLabel:     `${KEY_NAMES[key]} ${MODE_NAMES[mode]}`,
      popularity:   parseFloat(getCol(cols, iPop)) || 0,
      energy:       parseFloat(getCol(cols, iEnergy)) || 0,
      danceability: parseFloat(getCol(cols, iDance)) || 0,
      valence:      parseFloat(getCol(cols, iVal)) || 0,
    });
  }
  return songs;
}
