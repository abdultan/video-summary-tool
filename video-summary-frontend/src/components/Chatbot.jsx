import { useState, useRef, useEffect } from "react";

export default function Chatbot({ title, summary, transcript }) {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Video ile ilgili her türlü soruyu sorabilirsiniz." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const chatEndRef = useRef(null);

  useEffect(() => {
    // Her yeni mesajda en sona scroll
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setError("");
    const userMessage = { from: "user", text: input };
    setMessages((msgs) => [...msgs, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://34.38.135.187:8000/qa/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          summary,
          transcript,
          question: input,
        }),
      });
      if (!res.ok) throw new Error("Sunucu hatası veya bağlantı problemi.");
      const data = await res.json();
      if (!data.answer) {
        setMessages((msgs) => [
          ...msgs,
          { from: "bot", text: "Yanıt alınamadı, lütfen tekrar deneyin." },
        ]);
      } else {
        setMessages((msgs) => [...msgs, { from: "bot", text: data.answer }]);
      }
    } catch (err) {
      setMessages((msgs) => [
        ...msgs,
        { from: "bot", text: "Bir hata oluştu. Lütfen tekrar deneyin." },
      ]);
      setError(
        "Bir hata oluştu. Lütfen bağlantınızı ve sunucu durumunu kontrol edin."
      );
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-80 max-h-96">
      <div className="flex-1 overflow-y-auto space-y-2 mb-2 pr-2 bg-gray-50 rounded-lg p-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${
              msg.from === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`px-4 py-2 rounded-lg max-w-xs text-sm shadow-sm ${
                msg.from === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-800 border border-gray-200"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="px-4 py-2 rounded-lg bg-white text-gray-800 text-sm shadow-sm animate-pulse border border-gray-200">
              Yazıyor...
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>
      {error && (
        <div className="text-red-600 text-xs text-center mb-1">{error}</div>
      )}
      <form onSubmit={handleSend} className="flex gap-2 mt-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Video ile ilgili sorunuzu yazın..."
          className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
          disabled={loading || !transcript}
        />
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-all"
          disabled={loading || !input.trim() || !transcript}
        >
          Gönder
        </button>
      </form>
    </div>
  );
}
