export const KEY_NAMES = ["C","C♯","D","D♯","E","F","F♯","G","G♯","A","A♯","B"];
export const MODE_NAMES = { 0: "minor", 1: "major" };

export function getRelativeKey(key, mode) {
  if (mode === 0) return { key: (key + 3) % 12, mode: 1 };
  return { key: (key + 9) % 12, mode: 0 };
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
