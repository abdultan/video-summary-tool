import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import VideoSummaryMain from "./components/VideoSummaryMain";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
      <Navbar />
      <div className="flex flex-row gap-6 w-full items-stretch h-[calc(100vh-72px)]">
        <Sidebar />
        <main className="flex-1 flex flex-col items-start justify-start">
          <VideoSummaryMain />
        </main>
        {/* Sağ taraf şimdilik boş */}
      </div>
    </div>
  );
}
