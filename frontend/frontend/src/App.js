import React, { useState } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [transcription, setTranscription] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  // Dosya seçimi
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  // Form gönderildiğinde
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); // Yükleme başladığında göster

    const formData = new FormData();
    formData.append("file", file);

    try {
      // 1. Adım: Dosya backend'e gönder
      const response = await fetch("http://34.38.135.187:8000/upload/", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setTranscription(data.transcription); // Transkripti göster

      // 2. Adım: Transkripti özetleme için backend'e gönder
      await getSummary(data.transcription); // Özetleme
    } catch (error) {
      console.error("Hata oluştu:", error);
    } finally {
      setLoading(false); // Yükleme tamamlandığında göster
    }
  };

  // Özetleme işlemi
  const getSummary = async (transcription) => {
    try {
      const response = await fetch("http://34.38.135.187:8000/summarize/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: transcription }), // JSON formatında text gönder
      });

      const data = await response.json();
      setSummary(data.summary); // Özet verisini al
    } catch (error) {
      console.error("Özetleme hatası:", error);
    }
  };

  return (
    <div className="App">
      <h1>Video Özetleme Aracı</h1>
      <form onSubmit={handleSubmit}>
        <input type="file" onChange={handleFileChange} />
        <button type="submit" disabled={loading}>
          Yükle ve Özetle
        </button>
      </form>
      {loading && <p>Yükleniyor...</p>} {/* Yükleniyor mesajı */}
      {transcription && (
        <div>
          <h2>Transkript:</h2>
          <p>{transcription}</p>
        </div>
      )}
      {summary && (
        <div>
          <h2>Özet:</h2>
          <p>{summary}</p>
        </div>
      )}
    </div>
  );
}

export default App;
