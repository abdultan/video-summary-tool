import { useState, useEffect, useRef } from "react";
import Chatbot from "./Chatbot";
import ProgressBar from "./ProgressBar";

function getYoutubeId(url) {
  const regExp =
    /^.*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#&?]*).*/;
  const match = url.match(regExp);
  return match && match[1].length === 11 ? match[1] : null;
}

const TRANSCRIPT_PREVIEW_LENGTH = 600;

export default function VideoSummaryMain() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [showFullTranscript, setShowFullTranscript] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    // Component unmount olduğunda WebSocket bağlantısını kapat
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    setProgress(0);
    setStatus("Video işleniyor...");

    try {
      // WebSocket bağlantısını başlat
      wsRef.current = new WebSocket("ws://34.38.135.187:8000/ws/progress");

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setProgress(data.progress);
        setStatus(data.status);

        if (data.progress === 100) {
          wsRef.current.close();
        }
      };

      wsRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
        setError("İlerleme takibi bağlantısında hata oluştu.");
      };

      const formData = new FormData();
      formData.append("url", url);
      const token = localStorage.getItem("token");
      const res = await fetch("http://34.38.135.187:8000/analyze/", {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });

      if (!res.ok) throw new Error("Sunucu hatası");
      const data = await res.json();
      setResult({
        transcript: data.transcript || "Transkript bulunamadı.",
        summary: data.summary || "Özet bulunamadı.",
        title: data.title || url || "Başlık bulunamadı.",
      });
    } catch (err) {
      setError(
        "Bir hata oluştu. Lütfen geçerli bir YouTube linki girin veya daha sonra tekrar deneyin."
      );
      if (wsRef.current) {
        wsRef.current.close();
      }
    }
    setLoading(false);
  };

  const videoId = getYoutubeId(url);
  const thumbnail = videoId
    ? `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`
    : null;

  // Transkript kısaltma
  const transcript =
    result?.transcript ||
    "Henüz transkript yok. Video analiz edildiğinde burada gözükecek.";
  const isLongTranscript = transcript.length > TRANSCRIPT_PREVIEW_LENGTH;
  const transcriptToShow =
    showFullTranscript || !isLongTranscript
      ? transcript
      : transcript.slice(0, TRANSCRIPT_PREVIEW_LENGTH) + "...";

  return (
    <section className="w-full max-w-[1600px] mx-auto flex flex-col gap-8 mt-8">
      <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
        {/* Sol Sütun: Thumbnail ve Transkript */}
        <div className="flex flex-col gap-6 items-center">
          <div className="bg-white rounded-xl shadow-lg p-4 flex justify-center min-h-[160px] items-center w-full max-w-xs">
            {thumbnail ? (
              <img
                src={thumbnail}
                alt="Video thumbnail"
                className="rounded-lg shadow-md max-h-60 object-contain mx-auto"
                style={{ width: "100%", maxWidth: 300 }}
              />
            ) : (
              <span className="text-gray-400 text-center w-full">
                Henüz video resmi yok
              </span>
            )}
          </div>
          <div className="bg-gray-50 p-4 rounded-lg shadow-inner min-h-[120px] w-full max-w-xs">
            <h3 className="font-semibold text-gray-700 mb-1">Transkript</h3>
            <p className="text-gray-700 text-sm whitespace-pre-line">
              {transcriptToShow}
            </p>
            {isLongTranscript && (
              <button
                className="mt-2 text-blue-600 hover:underline text-xs font-medium"
                onClick={() => setShowFullTranscript((v) => !v)}
              >
                {showFullTranscript ? "Küçült" : "Devamını oku"}
              </button>
            )}
          </div>
        </div>
        {/* Orta Sütun: Analiz ve Chatbot */}
        <div className="flex flex-col gap-6 items-center">
          <div className="bg-white rounded-xl shadow-lg p-8 flex flex-col gap-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-gray-800 mb-2 text-center">
              YouTube Video Analizi
            </h2>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="YouTube video linkini girin..."
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                disabled={loading}
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition-all disabled:opacity-60"
                disabled={loading || !url}
              >
                {loading ? "Yükleniyor..." : "Özetle"}
              </button>
            </form>
            {loading && (
              <div className="mt-4">
                <ProgressBar progress={progress} status={status} />
              </div>
            )}
            {error && (
              <div className="text-red-600 text-sm text-center mt-2">
                {error}
              </div>
            )}
          </div>
          <div className="bg-gray-50 rounded-xl shadow-inner p-6 min-h-[120px] w-full max-w-md">
            <h3 className="font-semibold text-gray-700 mb-2">Chatbot</h3>
            <Chatbot
              title={result?.title || ""}
              summary={result?.summary || ""}
              transcript={result?.transcript || ""}
            />
          </div>
        </div>
        {/* Sağ Sütun: Özet */}
        <div className="flex flex-col gap-6 items-center">
          <div className="bg-white rounded-xl shadow-lg p-6 min-h-[120px] w-full max-w-xs">
            <h3 className="font-semibold text-gray-700 mb-2">Özet</h3>
            <p className="text-gray-700 text-base whitespace-pre-line">
              {result?.summary ||
                "Henüz özet yok. Video analiz edildiğinde burada gözükecek."}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
