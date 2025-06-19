import React, { useEffect, useState } from "react";

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) throw new Error("Giriş yapmalısınız.");
        const res = await fetch("http://34.38.135.187:8000/history/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Geçmiş yüklenemedi.");
        const data = await res.json();
        setHistory(data);
      } catch (err) {
        setError(err.message);
      }
      setLoading(false);
    };
    fetchHistory();
  }, []);

  if (loading) return <div className="p-6">Geçmiş yükleniyor...</div>;
  if (error) return <div className="p-6 text-red-500">Hata: {error}</div>;

  return (
    <div className="p-6 w-full">
      <h2 className="text-2xl font-bold mb-6">Geçmiş</h2>
      {history.length === 0 ? (
        <p>Henüz özetlenmiş video yok.</p>
      ) : (
        <ul className="space-y-4">
          {history.map((item, idx) => (
            <li key={idx} className="bg-white p-4 rounded-lg shadow-md">
              <div className="font-semibold text-blue-600 mb-2">
                {item.title || "Başlıksız Video"}
              </div>
              <div className="text-gray-700 text-sm mb-1">{item.summary}</div>
              <div className="text-gray-500 text-xs">{item.created_at}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
