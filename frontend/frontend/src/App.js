import React, { useState } from "react";

function App() {
  const [videoFile, setVideoFile] = useState(null);
  const [transcription, setTranscription] = useState("");
  const [summary, setSummary] = useState("");
  const [filename, setFilename] = useState("");

  const handleFileChange = (e) => {
    setVideoFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!videoFile) return;

    const formData = new FormData();
    formData.append("file", videoFile);

    // 1. Videoyu yükle
    const uploadRes = await fetch("http://localhost:8000/upload/", {
      method: "POST",
      body: formData,
    });
    const uploadData = await uploadRes.json();
    setFilename(uploadData.filename);

    // 2. Sesi çıkar
    await fetch(
      `http://localhost:8000/extract-audio/?filename=${uploadData.filename}`,
      {
        method: "POST",
      }
    );

    // 3. Metne çevir
    const transRes = await fetch(
      `http://localhost:8000/transcribe-audio/?filename=${uploadData.filename}`,
      {
        method: "POST",
      }
    );
    const transData = await transRes.json();
    setTranscription(transData.text);

    // 4. Özet al
    const sumRes = await fetch("http://localhost:8000/summarize/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: transData.text }),
    });
    const sumData = await sumRes.json();
    setSummary(sumData.summary);
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>🎬 Video Özetleyici</h1>
      <input type="file" accept="video/*" onChange={handleFileChange} />
      <button onClick={handleUpload} style={{ marginLeft: "1rem" }}>
        Yükle ve Özetle
      </button>

      {transcription && (
        <>
          <h3>🔤 Transkripsiyon</h3>
          <p>{transcription}</p>
        </>
      )}

      {summary && (
        <>
          <h3>📝 Özet</h3>
          <p>
            <strong>{summary}</strong>
          </p>
        </>
      )}
    </div>
  );
}

export default App;
