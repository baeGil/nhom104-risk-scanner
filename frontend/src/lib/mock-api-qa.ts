export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  intents?: IntentResult[];
  provisions?: Provision[];
  citations?: Citation[];
  timestamp: string;
}

export interface IntentResult {
  type: string;
  confidence: number;
}

export interface Provision {
  documentName: string;
  articleNumber: string;
  text: string;
  verified: boolean;
  citation?: string;
}

export interface Citation {
  displayText: string;
  uid: string;
  verified: boolean;
  reason?: string;
  documentTitle?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  lastMessage?: string;
  lastMessageAt?: string | null;
  tabId?: string | null;
}

const mockResponses: Record<string, Omit<Message, "id" | "timestamp">> = {
  default: {
    role: "assistant",
    content: "Theo Điều 17 Luật Doanh nghiệp 2020, doanh nghiệp được quyền tự do kinh doanh trong các ngành, nghề mà luật không cấm. Cụ thể:\n\n1. Doanh nghiệp có quyền kinh doanh ngành, nghề mà luật không cấm.\n2. Ngành, nghề cấm kinh doanh được quy định tại Điều 6 của Luật này.\n3. Doanh nghiệp phải đáp ứng điều kiện kinh doanh đối với ngành, nghề có điều kiện.",
    intents: [
      { type: "LOOKUP", confidence: 0.95 },
      { type: "QA", confidence: 0.92 },
    ],
    provisions: [
      {
        documentName: "Luật Doanh nghiệp 2020",
        articleNumber: "Điều 17",
        text: "Doanh nghiệp có quyền tự do kinh doanh trong những ngành, nghề mà luật không cấm.",
        verified: true,
      },
    ],
  },
};

let conversationCounter = 0;

export function createConversation(): Conversation {
  conversationCounter++;
  return {
    id: `conv_${conversationCounter}`,
    title: "Cuộc trò chuyện mới",
    messages: [],
    createdAt: new Date().toISOString(),
  };
}

export async function sendMessage(
  conversationId: string | null,
  tabId: string,
  content: string,
  onToken: (token: string) => void,
  onConversationId?: (conversationId: string) => void,
  onMetadata?: (metadata: { intents?: IntentResult[]; provisions?: Provision[] }) => void
): Promise<{ conversationId: string; message: Message }> {
  await new Promise((r) => setTimeout(r, 500));

  const convId = conversationId || `conv_${tabId}`;
  onConversationId?.(convId);

  const response = mockResponses.default;
  const fullContent = response.content;
  onMetadata?.({ intents: response.intents, provisions: response.provisions });

  // Simulate streaming
  const tokens = fullContent.split(" ");
  for (const token of tokens) {
    onToken(token + " ");
    await new Promise((r) => setTimeout(r, 50 + Math.random() * 80));
  }

  return {
    conversationId: convId,
    message: {
      id: `msg_${Date.now()}`,
      role: "assistant",
      content: fullContent,
      intents: response.intents,
      provisions: response.provisions,
      timestamp: new Date().toISOString(),
    },
  };
}

export function getConversations(): Conversation[] {
  return [];
}

export function getConversation(id: string): Conversation {
  return {
    id,
    title: "Cuộc trò chuyện mới",
    messages: [],
    createdAt: new Date().toISOString(),
  };
}

export function getTabConversation(tabId: string): Conversation | null {
  return null;
}

export function renameConversation(id: string, title: string): Conversation {
  return {
    id,
    title,
    messages: [],
    createdAt: new Date().toISOString(),
  };
}

export function deleteConversation(id: string): void {
  // Mock deletion
}
