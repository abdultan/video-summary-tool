export default function Navbar() {
  return (
    <nav className="w-full sticky top-0 z-30 bg-gradient-to-r from-indigo-600 to-blue-500 shadow-md">
      <div
        className="max-w-7xl mx-auto px-4 flex items-center justify-center"
        style={{ height: "72px" }}
      >
        <div className="text-white font-bold text-2xl tracking-tight select-none text-center w-full">
          Video Summary Tool
        </div>
      </div>
    </nav>
  );
}
