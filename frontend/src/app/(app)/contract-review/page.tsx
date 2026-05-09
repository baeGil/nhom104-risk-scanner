"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { WobblyBadge } from "@/components/ui/wobbly-badge";
import { Upload, FileText, CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronRight, Eye, ArrowLeft, FileText as FileTextIcon, Type, Loader2 } from "lucide-react";
import dynamic from "next/dynamic";
import { cn } from "@/lib/utils";
import { fileToPdfBlob } from "@/lib/file-to-pdf";

const PDFViewer = dynamic(() => import("@/components/contract/pdf-viewer").then(m => m.PDFViewer), { ssr: false });

type ViewMode = "upload" | "preview" | "analyzing" | "results";
type InputType = "file" | "text";

interface Clause {
  id: string;
  type: string;
  text: string;
  riskLevel: "low" | "medium" | "high";
}

interface ComplianceResult {
  violations: { clause: string; description: string; citation: string; verified: boolean }[];
  risks: string[];
  suggestions: string[];
}

const mockAnalysis = {
  clauses: [
    { id: "c1", type: "Thanh toán", text: "Bên A thanh toán cho Bên B số tiền 50 triệu đồng/tháng, chậm nhất ngày 05 hàng tháng. Quá hạn phạt 0.5%/ngày.", riskLevel: "low" as const },
    { id: "c2", type: "Phạt vi phạm", text: "Phạt 30% giá trị hợp đồng khi một bên vi phạm bất kỳ điều khoản nào.", riskLevel: "high" as const },
    { id: "c3", type: "Bảo hành", text: "Thời hạn bảo hành 12 tháng kể từ ngày bàn giao. Bên B chịu chi phí vận chuyển.", riskLevel: "medium" as const },
    { id: "c4", type: "Chấm dứt", text: "Hợp đồng tự động gia hạn hàng năm trừ khi một bên thông báo chấm dứt trước 30 ngày.", riskLevel: "low" as const },
    { id: "c5", type: "Bồi thường", text: "Bên vi phạm phải bồi thường toàn bộ thiệt hại thực tế phát sinh, không giới hạn.", riskLevel: "high" as const },
    { id: "c6", type: "Bảo mật", text: "Các bên cam kết bảo mật thông tin trong thời hạn hợp đồng và 24 tháng sau khi chấm dứt.", riskLevel: "low" as const },
    { id: "c7", type: "Giải quyết tranh chấp", text: "Tranh chấp được giải quyết tại Tòa án nhân dân nơi Bên A có trụ sở.", riskLevel: "medium" as const },
  ],
  compliance: {
    violations: [
      { clause: "Phạt vi phạm", description: "Mức phạt 30% vượt quá 8% giá trị phần nghĩa vụ bị vi phạm theo Luật Thương mại 2005", citation: "Điều 301 Luật Thương mại 2005", verified: true },
      { clause: "Bồi thường", description: "Điều khoản bồi thường không giới hạn có thể bị tuyên vô hiệu một phần", citation: "Điều 302 BLDS 2015", verified: true },
    ],
    risks: [
      "Mức phạt 30% quá cao, tòa án có thể giảm xuống",
      "Bồi thường không giới hạn khó được tòa án chấp nhận toàn bộ",
      "Điều khoản bảo hành chưa rõ ràng về phạm vi",
    ],
    suggestions: [
      "Giảm mức phạt vi phạm xuống tối đa 8% giá trị phần nghĩa vụ bị vi phạm",
      "Bổ sung giới hạn trách nhiệm bồi thường (ví dụ: tối đa 12 tháng giá trị hợp đồng)",
      "Làm rõ phạm vi bảo hành: loại trừ hỏng hóc do lỗi Bên A",
    ],
  },
};

const analyzeSteps = [
  { label: "Đang tải lên tài liệu", threshold: 20 },
  { label: "Đang đọc và trích xuất nội dung", threshold: 45 },
  { label: "Đang phân tích điều khoản", threshold: 70 },
  { label: "Đang đối chiếu pháp luật", threshold: 90 },
  { label: "Hoàn thành", threshold: 100 },
];

export default function ContractReviewPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("upload");
  const [inputType, setInputType] = useState<InputType>("file");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [textContent, setTextContent] = useState("");
  const [progress, setProgress] = useState(0);
  const [splitPosition, setSplitPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [expandedClauses, setExpandedClauses] = useState<Set<string>>(new Set());
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [compliance, setCompliance] = useState<ComplianceResult | null>(null);
  const [sourceName, setSourceName] = useState("");
  const [converting, setConverting] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const resetToUpload = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(null);
    setPreviewUrl(null);
    setTextContent("");
    setClauses([]);
    setCompliance(null);
    setSourceName("");
    setProgress(0);
    setViewMode("upload");
  };

  const handleFile = async (file: File) => {
    if (!file.name.match(/\.(pdf|docx|doc|txt|md)$/i)) {
      alert("Chỉ hỗ trợ file PDF, DOCX, DOC, TXT, MD");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert("File quá lớn. Tối đa 10MB");
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(file);
    setTextContent("");
    setPreviewUrl(null);
    setSourceName(file.name);

    const ext = file.name.toLowerCase().split(".").pop();

    if (ext === "pdf") {
      setPreviewUrl(URL.createObjectURL(file));
      setViewMode("preview");
    } else {
      setConverting(true);
      try {
        const pdfBlob = await fileToPdfBlob(file);
        setPreviewUrl(URL.createObjectURL(pdfBlob));
        setViewMode("preview");
      } catch (err) {
        console.error("Conversion failed:", err);
        alert("Không thể chuyển đổi file. Vui lòng thử lại.");
      } finally {
        setConverting(false);
      }
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, []);

  const handleSelectFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleAnalyze = async () => {
    if (!selectedFile && !textContent.trim()) return;

    setViewMode("analyzing");
    setProgress(0);

    const totalDuration = 4000;
    const startTime = Date.now();

    await new Promise<void>((resolve) => {
      const tick = () => {
        const elapsed = Date.now() - startTime;
        const pct = Math.min((elapsed / totalDuration) * 100, 100);
        setProgress(pct);
        if (pct < 100) {
          requestAnimationFrame(tick);
        } else {
          resolve();
        }
      };
      requestAnimationFrame(tick);
    });

    setClauses(mockAnalysis.clauses);
    setCompliance(mockAnalysis.compliance);
    setViewMode("results");
  };

  // Resizable split pane
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  useEffect(() => {
    if (!isDragging) return;
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const pct = Math.min(Math.max((x / rect.width) * 100, 20), 80);
      setSplitPosition(pct);
    };
    const handleMouseUp = () => setIsDragging(false);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging]);

  const toggleClause = (id: string) => {
    setExpandedClauses((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const riskColor = (level: string) => {
    if (level === "high") return "bg-accent/20 border-accent text-accent";
    if (level === "medium") return "bg-yellow-200/50 border-yellow-500 text-yellow-700";
    return "bg-green-100/50 border-green-500 text-green-700";
  };

  const highlightText = (text: string) => {
    if (!clauses.length) return text;
    let result = text;
    clauses.forEach((clause) => {
      const color = clause.riskLevel === "high" ? "bg-accent/30" : clause.riskLevel === "medium" ? "bg-yellow-200/50" : "bg-green-100/50";
      const border = clause.riskLevel === "high" ? "border-b-2 border-accent" : clause.riskLevel === "medium" ? "border-b-2 border-yellow-500" : "border-b-2 border-green-500";
      const escaped = clause.text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const regex = new RegExp(`(${escaped})`, "g");
      result = result.replace(regex, `<span class="${color} ${border} px-1 rounded">$1</span>`);
    });
    return result;
  };

  const currentStep = analyzeSteps.find((s) => progress < s.threshold) || analyzeSteps[analyzeSteps.length - 1];

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          {viewMode !== "upload" && (
            <button onClick={resetToUpload} className="flex items-center gap-2 font-body text-fg/60 hover:text-fg transition-colors">
              <ArrowLeft className="w-4 h-4" />
              Quay lại
            </button>
          )}
          <h1 className="font-heading text-3xl text-fg">Rà soát hợp đồng</h1>
        </div>
        {viewMode === "preview" && (
          <WobblyButton onClick={handleAnalyze} size="lg">
            <Eye className="w-5 h-5 mr-2" />
            Rà soát ngay
          </WobblyButton>
        )}
      </div>

      {/* Upload Zone */}
      {viewMode === "upload" && (
        <WobblyCard decoration="tape" className="flex-1 flex flex-col items-center justify-center">
          {/* Toggle: File / Text */}
          <div className="flex gap-2 mb-6">
            <button
              className={cn(
                "font-body text-lg px-6 py-2 border-2 transition-all",
                inputType === "file" ? "bg-fg text-white border-fg" : "border-fg/30 text-fg/60 hover:border-fg"
              )}
              style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
              onClick={() => setInputType("file")}
            >
              <FileTextIcon className="w-4 h-4 inline mr-2" />
              Tải file
            </button>
            <button
              className={cn(
                "font-body text-lg px-6 py-2 border-2 transition-all",
                inputType === "text" ? "bg-fg text-white border-fg" : "border-fg/30 text-fg/60 hover:border-fg"
              )}
              style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
              onClick={() => setInputType("text")}
            >
              <Type className="w-4 h-4 inline mr-2" />
              Dán văn bản
            </button>
          </div>

          {inputType === "file" ? (
            <div
              className={`border-2 border-dashed border-fg/40 rounded-lg p-16 text-center transition-colors w-full max-w-xl ${
                isDragging ? "bg-muted" : ""
              }`}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
            >
              <Upload className="w-20 h-20 mx-auto text-fg/30 mb-6" strokeWidth={1.5} />
              <h3 className="font-heading text-3xl text-fg mb-3">Kéo thả hợp đồng vào đây</h3>
              <p className="font-body text-lg text-fg/60 mb-8">Hỗ trợ PDF, DOCX, DOC, TXT, MD — tối đa 10MB</p>
              <input type="file" accept=".pdf,.docx,.doc,.txt,.md" className="hidden" ref={fileInputRef} onChange={handleSelectFile} />
              <WobblyButton size="lg" onClick={() => fileInputRef.current?.click()}>
                Chọn file
              </WobblyButton>
            </div>
          ) : (
            <div className="w-full max-w-2xl">
              <textarea
                className="w-full border-2 border-fg bg-white p-6 font-body text-lg resize-none focus:border-secondary focus:ring-2 focus:ring-secondary/20 focus:outline-none"
                style={{ borderRadius: "12px", minHeight: "300px" }}
                placeholder="Dán nội dung hợp đồng cần rà soát vào đây..."
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
              />
              <div className="mt-4 flex justify-between items-center">
                <span className="font-body text-sm text-fg/40">{textContent.length} ký tự</span>
                <WobblyButton size="lg" onClick={handleAnalyze} disabled={!textContent.trim()}>
                  <Eye className="w-5 h-5 mr-2" />
                  Rà soát ngay
                </WobblyButton>
              </div>
            </div>
          )}
        </WobblyCard>
      )}

      {/* Preview */}
      {viewMode === "preview" && (
        <WobblyCard className="flex-1 flex flex-col overflow-hidden">
          <div className="flex items-center gap-3 mb-4 pb-3 border-b border-fg/10">
            <FileText className="w-5 h-5 text-fg/40" />
            <span className="font-body text-lg text-fg">{sourceName}</span>
            {converting && (
              <span className="ml-auto font-body text-sm text-fg/60 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Đang chuyển đổi sang PDF...
              </span>
            )}
          </div>
          <div className="flex-1 overflow-auto bg-muted/30 border-2 border-fg/20 p-4" style={{ borderRadius: "8px" }}>
            {converting ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-fg/30" />
                  <p className="font-body text-fg/60">Đang chuyển đổi sang PDF...</p>
                </div>
              </div>
            ) : previewUrl ? (
              <PDFViewer url={previewUrl} />
            ) : (
              <div className="flex items-center justify-center h-full text-fg/40 font-body text-lg">
                Không thể xem trước định dạng này
              </div>
            )}
          </div>
        </WobblyCard>
      )}

      {/* Analyzing Progress */}
      {viewMode === "analyzing" && (
        <WobblyCard decoration="tack" className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-lg w-full">
            <h3 className="font-heading text-2xl text-fg mb-2">Đang phân tích hợp đồng</h3>
            <p className="font-body text-fg/60 mb-8">AI đang đọc và đối chiếu với pháp luật hiện hành...</p>

            {/* Progress bar */}
            <div className="w-full border-2 border-fg bg-white p-1.5 mb-3" style={{ borderRadius: "12px" }}>
              <motion.div
                className="h-5 bg-gradient-to-r from-secondary to-accent"
                style={{ borderRadius: "10px" }}
                animate={{ width: `${Math.min(progress, 100)}%` }}
                transition={{ duration: 0.2 }}
              />
            </div>
            <div className="flex justify-between items-center mb-8">
              <span className="font-body text-lg text-fg">{Math.round(Math.min(progress, 100))}%</span>
              <span className="font-body text-sm text-fg/60">{currentStep.label}</span>
            </div>

            {/* Steps */}
            <div className="space-y-3 text-left">
              {analyzeSteps.map((step, i) => {
                const isDone = progress >= step.threshold;
                const isActive = progress >= (i > 0 ? analyzeSteps[i - 1].threshold : 0) && progress < step.threshold;
                return (
                  <div key={step.label} className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors ${
                      isDone ? "bg-secondary text-white border-secondary" :
                      isActive ? "bg-fg text-white border-fg" :
                      "bg-white text-fg/30 border-fg/30"
                    }`} style={{ borderRadius: "50%" }}>
                      {isDone ? <CheckCircle className="w-4 h-4" /> : <div className="w-2 h-2 rounded-full bg-current" />}
                    </div>
                    <span className={`font-body text-lg ${isDone ? "text-secondary" : isActive ? "text-fg" : "text-fg/30"}`}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </WobblyCard>
      )}

      {/* Results: Split View */}
      {viewMode === "results" && (
        <div ref={containerRef} className="flex-1 flex gap-0 overflow-hidden">
          {/* Left: Preview */}
          <div className="overflow-hidden transition-all duration-300" style={{ width: `${splitPosition}%` }}>
            <WobblyCard className="h-full flex flex-col overflow-hidden">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-fg/10 flex-shrink-0">
                <Eye className="w-5 h-5 text-secondary" strokeWidth={2.5} />
                <h3 className="font-heading text-lg text-fg">Xem trước</h3>
                <span className="font-body text-sm text-fg/40 ml-auto">{sourceName}</span>
              </div>
              <div className="flex-1 overflow-auto bg-muted/30 border-2 border-fg/20 p-4" style={{ borderRadius: "8px" }}>
                {previewUrl ? (
                  <PDFViewer url={previewUrl} />
                ) : textContent ? (
                  <div
                    className="bg-white p-6 font-body text-fg/80 whitespace-pre-wrap leading-relaxed overflow-auto"
                    style={{ borderRadius: "8px", height: "100%" }}
                    dangerouslySetInnerHTML={{ __html: highlightText(textContent).replace(/\n/g, "<br/>") }}
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-fg/40 font-body text-lg">
                    Không thể xem trước
                  </div>
                )}
              </div>
            </WobblyCard>
          </div>

          {/* Resizable Divider */}
          <div
            className="w-2 bg-fg/10 hover:bg-secondary/50 cursor-col-resize transition-colors flex-shrink-0"
            onMouseDown={handleMouseDown}
          />

          {/* Right: Results */}
          <div className="overflow-hidden transition-all duration-300" style={{ width: `${100 - splitPosition}%` }}>
            <WobblyCard className="h-full flex flex-col overflow-hidden">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-fg/10 flex-shrink-0">
                <FileText className="w-5 h-5 text-accent" strokeWidth={2.5} />
                <h3 className="font-heading text-lg text-fg">Kết quả phân tích</h3>
                <WobblyBadge variant="accent" className="ml-auto">{clauses.length} điều khoản</WobblyBadge>
              </div>

              <div className="flex-1 overflow-auto space-y-4 pr-2">
                {/* Violations */}
                {compliance?.violations && compliance.violations.length > 0 && (
                  <div>
                    <h4 className="font-heading text-lg text-accent mb-2 flex items-center gap-2">
                      <XCircle className="w-5 h-5" />
                      Vi phạm ({compliance.violations.length})
                    </h4>
                    <div className="space-y-2">
                      {compliance.violations.map((v, i) => (
                        <div key={i} className="bg-postit border-2 border-accent/30 p-3" style={{ borderRadius: "60px 4px 45px 4px / 4px 45px 4px 60px" }}>
                          <div className="flex items-start gap-2">
                            <AlertTriangle className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
                            <div>
                              <h5 className="font-heading text-fg">{v.clause}</h5>
                              <p className="font-body text-sm text-fg/80">{v.description}</p>
                              <div className="mt-1 flex items-center gap-2">
                                <WobblyBadge variant={v.verified ? "secondary" : "default"}>
                                  {v.verified ? "✓ VERIFIED" : "? UNVERIFIED"}
                                </WobblyBadge>
                                <span className="font-body text-xs text-fg/50">{v.citation}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Risks */}
                {compliance?.risks && compliance.risks.length > 0 && (
                  <div>
                    <h4 className="font-heading text-lg text-yellow-600 mb-2 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      Rủi ro ({compliance.risks.length})
                    </h4>
                    <div className="space-y-2">
                      {compliance.risks.map((risk, i) => (
                        <div key={i} className="bg-yellow-50 border-2 border-yellow-300/50 p-3 font-body text-fg/80" style={{ borderRadius: "60px 4px 45px 4px / 4px 45px 4px 60px" }}>
                          <span className="text-yellow-600 mr-2">⚠</span>{risk}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Suggestions */}
                {compliance?.suggestions && compliance.suggestions.length > 0 && (
                  <div>
                    <h4 className="font-heading text-lg text-secondary mb-2 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Đề xuất ({compliance.suggestions.length})
                    </h4>
                    <div className="space-y-2">
                      {compliance.suggestions.map((s, i) => (
                        <div key={i} className="bg-blue-50 border-2 border-secondary/30 p-3 font-body text-fg/80" style={{ borderRadius: "60px 4px 45px 4px / 4px 45px 4px 60px" }}>
                          <span className="text-secondary mr-2">→</span>{s}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* All Clauses */}
                <div>
                  <h4 className="font-heading text-lg text-fg mb-2 flex items-center gap-2">
                    <FileText className="w-5 h-5" />
                    Tất cả điều khoản
                  </h4>
                  <div className="space-y-2">
                    {clauses.map((clause) => (
                      <div
                        key={clause.id}
                        className={`border-2 p-3 cursor-pointer transition-all ${riskColor(clause.riskLevel)}`}
                        style={{ borderRadius: "60px 4px 45px 4px / 4px 45px 4px 60px" }}
                        onClick={() => toggleClause(clause.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {expandedClauses.has(clause.id) ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                            <span className="font-bold">{clause.type}</span>
                            <WobblyBadge variant={clause.riskLevel === "low" ? "secondary" : clause.riskLevel === "medium" ? "postit" : "accent"}>
                              {clause.riskLevel === "low" ? "Thấp" : clause.riskLevel === "medium" ? "Trung bình" : "Cao"}
                            </WobblyBadge>
                          </div>
                        </div>
                        <AnimatePresence>
                          {expandedClauses.has(clause.id) && (
                            <motion.p className="mt-2 text-sm" initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}>
                              {clause.text}
                            </motion.p>
                          )}
                        </AnimatePresence>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </WobblyCard>
          </div>
        </div>
      )}
    </div>
  );
}
