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

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div className="max-w-2xl">
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

        {/* Provisions */}
        {!isUser && message.provisions && message.provisions.length > 0 && (
          <div className="mt-3 space-y-2">
            {message.provisions.map((p, i) => (
              <div
                key={i}
                className="bg-white border-2 border-fg/30 p-3"
                style={{ borderRadius: "60px 4px 45px 4px / 4px 45px 4px 60px" }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-heading text-sm text-secondary">
                    📎 {p.documentName}
                  </span>
                  <WobblyBadge variant={p.verified ? "secondary" : "default"}>
                    {p.verified ? "✓ VERIFIED" : "? UNVERIFIED"}
                  </WobblyBadge>
                </div>
                <p className="font-body text-sm text-fg/70">{p.text}</p>
              </div>
            ))}
          </div>
        )}

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.citations.map((citation, i) => (
              <WobblyBadge key={`${citation.uid}-${i}`} variant={citation.verified ? "secondary" : "default"}>
                {citation.verified ? "✓" : "?"} {citation.displayText}
              </WobblyBadge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
