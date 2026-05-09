"use client";

import { useEffect, useRef, useState } from "react";

interface PDFViewerProps {
  url: string;
  highlights?: { text: string; riskLevel: string }[];
}

export function PDFViewer({ url }: PDFViewerProps) {
  const [error, setError] = useState(false);
  const embedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!embedRef.current) return;

    const container = embedRef.current;
    container.innerHTML = "";

    const embed = document.createElement("embed");
    embed.src = url;
    embed.type = "application/pdf";
    embed.style.width = "100%";
    embed.style.height = "100%";
    embed.style.border = "none";

    embed.onerror = () => {
      setError(true);
    };

    container.appendChild(embed);
  }, [url]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="font-body text-accent mb-2">Không thể tải PDF</p>
          <p className="font-body text-sm text-fg/40">Thử tải file lên lại</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={embedRef} className="overflow-auto h-full w-full" />
  );
}
