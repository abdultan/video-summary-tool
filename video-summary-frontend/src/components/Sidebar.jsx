export default function Sidebar() {
  return (
    <aside className="h-full self-stretch w-56 bg-white rounded-xl shadow-md p-6 flex flex-col justify-between select-none">
      <nav className="flex flex-col gap-2">
        <button className="text-left px-3 py-2 rounded-lg font-medium bg-blue-600 text-white shadow-sm">
          Video Analiz
        </button>
        <button className="text-left px-3 py-2 rounded-lg font-medium hover:bg-gray-100 transition">
          Geçmiş
        </button>
        <button className="text-left px-3 py-2 rounded-lg font-medium hover:bg-gray-100 transition">
          Destek
        </button>
      </nav>
      <div className="flex flex-col gap-2 mt-8">
        <button className="bg-white/10 hover:bg-blue-50 text-blue-600 border border-blue-100 px-4 py-2 rounded-lg font-medium transition-colors duration-200 shadow-sm">
          Kayıt Ol
        </button>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors duration-200 shadow-sm">
          Giriş Yap
        </button>
      </div>
    </aside>
  );
}
