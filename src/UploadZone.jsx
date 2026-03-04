export default function UploadZone({ onFile }) {
  const handle = (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => onFile(ev.target.result);
    reader.readAsText(file);
  };

  return (
    <div
      onDrop={(e) => { e.preventDefault(); handle(e.dataTransfer.files[0]); }}
      onDragOver={(e) => e.preventDefault()}
      onClick={() => document.getElementById('csvIn').click()}
      style={{
        border: "1px dashed #3b1f6e",
        borderRadius: 12,
        padding: "4rem 2rem",
        textAlign: "center",
        cursor: "pointer",
        background: "#09091a",
        transition: "border-color 0.2s, background 0.2s",
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = "#7c3aed"; e.currentTarget.style.background = "#0d0b1f"; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = "#3b1f6e"; e.currentTarget.style.background = "#09091a"; }}
    >
      <div style={{ fontSize: "3rem", marginBottom: "1rem", opacity: 0.6 }}>◈</div>
      <p style={{ color: "#a78bfa", fontWeight: 500, fontFamily: "'Syne', sans-serif", fontSize: "1.1rem" }}>
        Drop your Spotify CSV export here
      </p>
      <p style={{ color: "#4c1d95", fontSize: "0.8rem", marginTop: "0.5rem" }}>or click to browse</p>
      <p style={{ color: "#1e1b4b", fontSize: "0.72rem", marginTop: "1.5rem" }}>
        Works with exports from Exportify, Soundiiz, or any Spotify playlist tool
      </p>
      <input id="csvIn" type="file" accept=".csv" onChange={e => handle(e.target.files[0])} style={{ display: "none" }} />
    </div>
  );
}
