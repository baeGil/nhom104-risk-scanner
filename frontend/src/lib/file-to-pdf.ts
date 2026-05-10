import { marked } from "marked";

export async function fileToPdfBlob(file: File): Promise<Blob> {
  const html2pdf = (await import("html2pdf.js")).default;
  const ext = file.name.toLowerCase().split(".").pop();

  let htmlContent = "";

  if (ext === "txt") {
    const text = await file.text();
    htmlContent = `<pre style="font-family: monospace; white-space: pre-wrap; font-size: 14px; line-height: 1.6;">${escapeHtml(text)}</pre>`;
  } else if (ext === "md") {
    const text = await file.text();
    htmlContent = marked.parse(text) as string;
  } else if (ext === "docx") {
    const mammoth = await import("mammoth");
    const arrayBuffer = await file.arrayBuffer();
    const result = await mammoth.convertToHtml({ arrayBuffer });
    htmlContent = result.value;
  } else if (ext === "doc") {
    const text = await file.text();
    const stripped = text
      .replace(/\{\\[^{}]*\}/g, "")
      .replace(/\\[a-z]+\d*\s?/gi, "")
      .replace(/[{}]/g, "")
      .replace(/\n+/g, "\n")
      .trim();
    htmlContent = `<pre style="font-family: monospace; white-space: pre-wrap; font-size: 14px; line-height: 1.6;">${escapeHtml(stripped)}</pre>`;
  }

  const container = document.createElement("div");
  container.innerHTML = htmlContent;
  container.style.padding = "40px";
  container.style.fontFamily = "Arial, sans-serif";
  container.style.fontSize = "14px";
  container.style.lineHeight = "1.6";
  container.style.color = "#333";
  container.style.maxWidth = "800px";
  container.style.margin = "0 auto";
  document.body.appendChild(container);

  const opt = {
    margin: [10, 10, 10, 10] as [number, number, number, number],
    filename: `${file.name}.pdf`,
    image: { type: "jpeg" as const, quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: "mm" as const, format: "a4" as const, orientation: "portrait" as const },
  };

  const pdfBlob = await html2pdf().set(opt).from(container).outputPdf("blob");
  document.body.removeChild(container);

  return pdfBlob;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
