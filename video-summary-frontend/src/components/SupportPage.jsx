import React from "react";

export default function SupportPage() {
  return (
    <div className="p-8 max-w-xl">
      <h2 className="text-2xl font-bold mb-4">Destek</h2>
      <p className="mb-2">
        Herhangi bir sorunuz veya geri bildiriminiz varsa, lütfen bizimle
        iletişime geçin:
      </p>
      <ul className="list-disc pl-6 mb-4">
        <li>
          E-posta:{" "}
          <a
            href="mailto:destek@videosummary.com"
            className="text-blue-600 underline"
          >
            destek@videosummary.com
          </a>
        </li>
      </ul>
      <p>En kısa sürede size geri dönüş yapacağız.</p>
    </div>
  );
}
