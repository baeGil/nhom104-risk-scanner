import { useState } from "react";
import { cn } from "@/lib/utils";
import { WOBBLY_MD } from "@/lib/radius";
import { WobblyBadge } from "@/components/ui/wobbly-badge";
import type { Message } from "@/lib/mock-api-qa";

interface ChatBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export function ChatBubble({ message, isStreaming }: ChatBubbleProps) {
  const isUser = message.role === "user";
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  const toggleCitation = (citationText: string) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [citationText]: !prev[citationText],
    }));
  };

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div className="max-w-2xl w-full">
        {/* Intent tags for assistant messages */}
        {!isUser && message.intents && message.intents.length > 0 && (
          <div className="flex gap-2 mb-2 ml-2">
            {message.intents.map((intent) => (
              <WobblyBadge key={intent.type} variant="default">
                {intent.type} ({Math.round(intent.confidence * 100)}%)
              </WobblyBadge>
            ))}
          </div>
        )}

        {/* Message bubble */}
        <div
          className={cn(
            "p-4 border-2 font-body text-lg leading-relaxed",
            isUser
              ? "bg-secondary text-white border-secondary"
              : "bg-white text-fg border-fg"
          )}
          style={{
            borderRadius: isUser
              ? "120px 8px 90px 120px / 8px 90px 8px 120px"
              : "8px 120px 120px 8px / 90px 8px 120px 8px",
          }}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
          {isStreaming && (
            <span className="inline-block w-2 h-5 bg-fg ml-1 animate-pulse" />
          )}
        </div>

        {/* Compact Clickable Citation Badges */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-3">
            <div className="flex flex-wrap gap-2">
              {message.citations.map((citation, i) => {
                const isExpanded = !!expandedCitations[citation.displayText];
                return (
                  <button
                    key={`${citation.uid}-${i}`}
                    onClick={() => toggleCitation(citation.displayText)}
                    className="focus:outline-none transition-all duration-200 active:scale-95 text-left"
                  >
                    <WobblyBadge
                      variant={citation.verified ? "secondary" : "default"}
                      className={cn(
                        "cursor-pointer select-none py-1.5 px-3 flex items-center gap-1.5 hover:opacity-90",
                        isExpanded && "ring-2 ring-fg ring-offset-2 scale-105"
                      )}
                    >
                      <span>{citation.verified ? "✓" : "?"}</span>
                      <span>{citation.displayText}</span>
                      <span className="text-[10px] opacity-75 ml-1">
                        {isExpanded ? "▲" : "▼"}
                      </span>
                    </WobblyBadge>
                  </button>
                );
              })}
            </div>

            {/* Revealed White Provision Cards underneath the badges row */}
            <div className="mt-3 space-y-2">
              {message.citations.map((citation, i) => {
                const isExpanded = !!expandedCitations[citation.displayText];
                if (!isExpanded) return null;

                const matchingProvision = message.provisions?.find(
                  (p) => p.citation === citation.displayText
                );
                if (!matchingProvision) return null;

                return (
                  <div
                    key={`expanded-${citation.uid}-${i}`}
                    className="bg-white border-2 border-fg/30 p-4 animate-in fade-in slide-in-from-top-2 duration-200"
                    style={{ borderRadius: "60px 4px 45px 4px / 4px 45px 4px 60px" }}
                  >
                    <div className="flex items-center gap-2 mb-2 border-b pb-1.5 border-fg/10">
                      <span className="font-heading text-sm text-secondary">
                        📎 {matchingProvision.documentName} {matchingProvision.articleNumber && `— ${matchingProvision.articleNumber}`}
                      </span>
                      <WobblyBadge variant={matchingProvision.verified ? "secondary" : "default"}>
                        {matchingProvision.verified ? "✓ VERIFIED" : "? UNVERIFIED"}
                      </WobblyBadge>
                      {citation.reason && (
                        <span className="text-[11px] text-fg/50 italic ml-auto truncate max-w-[50%]" title={citation.reason}>
                          Lý do: {citation.reason}
                        </span>
                      )}
                    </div>
                    <p className="font-body text-sm text-fg/80 leading-relaxed whitespace-pre-line">
                      {matchingProvision.text}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
