import { apiRequest, apiSSE } from "./api-client";
import type { Message, IntentResult, Provision } from "./mock-api-qa";

export interface ChatRequest {
  message: string;
  conversationId?: string;
}

export interface ChatChunk {
  token: string;
  intents?: IntentResult[];
  provisions?: Provision[];
  done?: boolean;
}

export interface ChatResponse {
  messageId: string;
  content: string;
  intents: IntentResult[];
  provisions: Provision[];
}

export interface ConversationSummary {
  id: string;
  title: string;
  lastMessage: string;
  createdAt: string;
}

export async function sendMessage(
  conversationId: string,
  content: string,
  onToken: (token: string) => void
): Promise<Message> {
  let fullContent = "";
  let intents: IntentResult[] = [];
  let provisions: Provision[] = [];

  await apiSSE<ChatChunk>(
    "/api/qa/chat",
    { message: content, conversationId },
    (chunk) => {
      if (chunk.token) {
        fullContent += chunk.token;
        onToken(chunk.token);
      }
      if (chunk.intents) intents = chunk.intents;
      if (chunk.provisions) provisions = chunk.provisions;
    }
  );

  return {
    id: `msg_${Date.now()}`,
    role: "assistant",
    content: fullContent,
    intents,
    provisions,
    timestamp: new Date().toISOString(),
  };
}

export async function createConversation(): Promise<{ id: string }> {
  return apiRequest<{ id: string }>("/api/qa/conversations", {
    method: "POST",
    body: JSON.stringify({ title: "New conversation" }),
  });
}

export async function getConversations(): Promise<ConversationSummary[]> {
  return apiRequest<ConversationSummary[]>("/api/qa/conversations");
}

export async function deleteConversation(id: string): Promise<void> {
  await apiRequest(`/api/qa/conversations/${id}`, { method: "DELETE" });
}
