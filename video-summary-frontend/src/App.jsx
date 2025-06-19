import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import VideoSummaryMain from "./components/VideoSummaryMain";
import RegisterForm from "./components/RegisterForm";
import LoginForm from "./components/LoginForm";
import HistoryPage from "./components/HistoryPage";
import SupportPage from "./components/SupportPage";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import { useState } from "react";

function AppContent() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem("token"));
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsLoggedIn(false);
    navigate("/login");
  };

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
      <Navbar />
      <div className="flex flex-row gap-6 w-full items-stretch h-[calc(100vh-72px)]">
        <Sidebar isLoggedIn={isLoggedIn} onLogoutClick={handleLogout} />
        <main className="flex-1 flex flex-col items-start justify-start">
          <Routes>
            <Route
              path="/"
              element={<VideoSummaryMain isLoggedIn={isLoggedIn} />}
            />
            <Route path="/history" element={<HistoryPage />} />
            <Route
              path="/login"
              element={<LoginForm onSuccess={handleLoginSuccess} />}
            />
            <Route
              path="/register"
              element={<RegisterForm onSuccess={() => navigate("/login")} />}
            />
            <Route path="/support" element={<SupportPage />} />
            <Route
              path="*"
              element={<div className="p-8">Sayfa bulunamadı.</div>}
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
