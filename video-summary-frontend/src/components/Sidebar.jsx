import React from "react";
import { Link, useLocation } from "react-router-dom";

export default function Sidebar({ isLoggedIn, onLogoutClick }) {
  const location = useLocation();
  const activeClass =
    "bg-blue-100 text-blue-700 font-semibold border-l-4 border-blue-500";

  return (
    <aside className="w-56 bg-white shadow-md flex flex-col py-8 px-4 gap-4 h-full">
      <nav className="flex flex-col gap-2">
        <Link
          to="/"
          className={`rounded px-3 py-2 transition-all ${
            location.pathname === "/" ? activeClass : "hover:bg-gray-100"
          }`}
        >
          Video Analiz
        </Link>
        {isLoggedIn && (
          <Link
            to="/history"
            className={`rounded px-3 py-2 transition-all ${
              location.pathname === "/history"
                ? activeClass
                : "hover:bg-gray-100"
            }`}
          >
            Geçmiş
          </Link>
        )}
        <Link
          to="/support"
          className={`rounded px-3 py-2 transition-all ${
            location.pathname === "/support" ? activeClass : "hover:bg-gray-100"
          }`}
        >
          Destek
        </Link>
      </nav>
      <div className="flex-1" />
      <div className="flex flex-col gap-2">
        {!isLoggedIn ? (
          <>
            <Link
              to="/login"
              className={`rounded px-3 py-2 transition-all ${
                location.pathname === "/login"
                  ? activeClass
                  : "hover:bg-gray-100"
              }`}
            >
              Giriş Yap
            </Link>
            <Link
              to="/register"
              className={`rounded px-3 py-2 transition-all ${
                location.pathname === "/register"
                  ? activeClass
                  : "hover:bg-gray-100"
              }`}
            >
              Kayıt Ol
            </Link>
          </>
        ) : (
          <button
            onClick={onLogoutClick}
            className="rounded px-3 py-2 bg-red-100 text-red-700 hover:bg-red-200 transition-all"
          >
            Çıkış Yap
          </button>
        )}
      </div>
    </aside>
  );
}
