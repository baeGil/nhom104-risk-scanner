"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { WobblyButton } from "@/components/ui/wobbly-button";
import { WobblyCard } from "@/components/ui/wobbly-card";
import { ChatBubble } from "@/components/qa/chat-bubble";
import { sendMessage, createConversation, type Message, type Conversation } from "@/lib/mock-api-qa";
import { Send, Plus, Trash2, MessageSquare } from "lucide-react";

export default function LegalQAPage() {
  const [conversation, setConversation] = useState<Conversation>(() => createConversation());
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation.messages, streamingContent]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setConversation((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage],
    }));

    const question = input;
    setInput("");
    setIsStreaming(true);
    setStreamingContent("");

    const assistantMessage = await sendMessage(
      conversation.id,
      question,
      (token) => {
        setStreamingContent((prev) => prev + token);
      }
    );

    setConversation((prev) => ({
      ...prev,
      messages: [...prev.messages, assistantMessage],
    }));

    setIsStreaming(false);
    setStreamingContent("");
  };

  const handleNewConversation = () => {
    setConversation(createConversation());
    setStreamingContent("");
    setIsStreaming(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <MessageSquare className="w-6 h-6 text-secondary" strokeWidth={2.5} />
          <h1 className="font-heading text-3xl text-fg">{conversation.title}</h1>
        </div>
        <WobblyButton variant="secondary" size="sm" onClick={handleNewConversation}>
          <Plus className="w-4 h-4 mr-2" />
          Mới
        </WobblyButton>
      </div>

      {/* Messages */}
      <WobblyCard className="flex-1 overflow-y-auto mb-4">
        {conversation.messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <MessageSquare className="w-16 h-16 text-fg/20 mb-4" strokeWidth={1.5} />
            <h3 className="font-heading text-2xl text-fg mb-2">Hỏi đáp pháp lý</h3>
            <p className="font-body text-fg/60 max-w-md">
              Đặt câu hỏi về pháp luật Việt Nam. AI sẽ phân tích và trả lời kèm trích dẫn văn bản pháp lý.
            </p>
            <div className="mt-6 flex flex-wrap gap-2 justify-center">
              {[
                "Điều 17 Luật Doanh nghiệp quy định gì?",
                "Luật DN 2020 còn hiệu lực không?",
                "Thủ tục đăng ký doanh nghiệp cần những gì?",
              ].map((q) => (
                <button
                  key={q}
                  className="font-body text-sm text-secondary border border-secondary/30 px-3 py-2 hover:bg-secondary/10 transition-colors"
                  style={{ borderRadius: "60px 4px 45px 4px / 4px 45px 4px 60px" }}
                  onClick={() => { setInput(q); }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {conversation.messages.map((msg) => (
              <ChatBubble key={msg.id} message={msg} />
            ))}
            {isStreaming && streamingContent && (
              <ChatBubble
                message={{
                  id: "streaming",
                  role: "assistant",
                  content: streamingContent,
                  timestamp: new Date().toISOString(),
                }}
                isStreaming
              />
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </WobblyCard>

      {/* Input */}
      <div className="flex gap-3">
        <input
          className="flex-1 font-body text-lg border-2 border-fg bg-white px-4 py-3 focus:border-secondary focus:ring-2 focus:ring-secondary/20 focus:outline-none"
          style={{ borderRadius: "120px 8px 90px 8px / 8px 90px 8px 120px" }}
          placeholder="Nhập câu hỏi pháp lý..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          disabled={isStreaming}
        />
        <WobblyButton onClick={handleSend} disabled={isStreaming || !input.trim()}>
          <Send className="w-5 h-5" />
        </WobblyButton>
      </div>
    </div>
  );
}
