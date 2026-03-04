# Mumble

**Mumble** is a web app that finds harmonically compatible songs in your Spotify playlist. Pick a reference track (or enter key and BPM manually), and Mumble shows you all tracks that match by key and tempo—same key, relative key, or parallel key—so you can build smooth DJ sets or practice playlists.

![Node](https://img.shields.io/badge/node-%3E%3D18-339933?logo=node.js)  
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)  
![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite)

---

## Features

- **Spotify CSV import** — Export a playlist via [Exportify](https://exportify.net), drop the CSV, and Mumble parses keys, BPM, and metadata.
- **Reference by song or by key** — Choose a track from your list as the reference, or enter key and BPM manually.
- **Harmonic matching** — Filters by same key, relative key, and (optionally) parallel key.
- **BPM range** — Adjustable ±BPM tolerance; supports half-time and double-time (e.g. 70 BPM matches 140).
- **Sort & filter** — Sort by BPM difference, popularity, or energy; filter by match type.
- **Pivot on any row** — Click a result to use it as the new reference track.

---

## Requirements

- [Node.js](https://nodejs.org/) **v18 or newer**

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/lestep1225118/Mumble.git
cd Mumble
npm install
```

### 2. Run the app

```bash
npm run dev
```

Then open **http://localhost:5274** in your browser (port is set in `vite.config.js`; Vite will prompt if it’s in use).

### 3. Use it

1. Export a Spotify playlist as CSV (e.g. with [Exportify](https://exportify.net)).
2. Drag and drop the CSV onto Mumble (or click to browse).
3. Search for a song to set as the reference track, or switch to **Match by Key & BPM** and enter key, mode, and BPM.
4. Browse matches, adjust ±BPM and “parallel keys” as needed, and click any row to pivot to that track as the new reference.

---

## Key matching logic

| Type        | Description | Example                |
|------------|-------------|------------------------|
| **Same key**   | Same key and mode | G minor → G minor       |
| **Relative key** | Same scale, different tonic | G minor ↔ B♭ major      |
| **Parallel key** | Same root, opposite mode (optional) | G minor ↔ G major |

Relative keys share the same set of notes (e.g. A minor and C major). Parallel keys share the same root (e.g. A minor and A major). You can toggle “parallel keys” on or off in the controls.

---

## Project structure

```
Mumble/
├── index.html          # Entry HTML
├── package.json        # Dependencies and scripts
├── vite.config.js      # Vite config (port, React plugin)
├── src/
│   ├── main.jsx        # React mount
│   ├── App.jsx         # Main app: upload, reference, filters, table
│   ├── index.css       # Global styles
│   ├── UploadZone.jsx  # CSV drop zone
│   ├── ResultsTable.jsx # Match table and row click
│   ├── MiniBar.jsx     # Mini stats bar (if used)
│   └── utils.js        # CSV parse, key/BPM matching
└── README.md
```

---

## Scripts

| Command         | Description                    |
|----------------|--------------------------------|
| `npm run dev`  | Start dev server (default port 5274) |
| `npm run build`| Production build to `dist/`    |
| `npm run preview` | Serve production build locally |

---

## Exporting from Spotify

Spotify doesn’t offer CSV export in-app. Use a third-party exporter that includes **Track Name**, **Artist**, **Key**, **Mode**, **Tempo**, and optionally **Energy**, **Popularity**, etc. Mumble expects column names like:

- `Track Name`, `Artist Name(s)`, `Album Name`
- `Tempo`, `Key`, `Mode`
- `Popularity`, `Energy`, `Danceability`, `Valence` (optional)

[Exportify](https://exportify.net) and [Soundiiz](https://soundiiz.com) produce CSVs that work with Mumble.

---

## License

MIT.

---

## Repository

**Mumble** — [https://github.com/lestep1225118/Mumble](https://github.com/lestep1225118/Mumble)
