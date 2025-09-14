"use client";

import { useState } from "react";
import { ChatHeader } from "@/components/chat/chat-header";
import { ChatMessageList } from "@/components/chat/chat-message-list";
import { ChatInput } from "@/components/chat/chat-input";
import { ConversationSidebar } from "@/components/conversation/conversation-sidebar";
import { Card } from "@/components/ui/card";
import { useConversationManager } from "@/hooks/use-conversation-manager";
import { Button } from "@/components/ui/button";
import { Menu, X } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

// Mock responses for testing
const mockResponses = [
  "I'm a modern AI assistant built with the latest Next.js 15 and React 19! How can I help you today?",
  "That's an interesting question! Let me think about that for a moment...",
  "I understand you're looking for information. Here's what I can tell you:",
  "Great question! Based on my knowledge, I can provide you with the following insights:",
  "I'd be happy to help you with that. Let me break this down for you:",
  `Here's a detailed response to your query:

**Key Points:**
- Point 1: This is important information
- Point 2: Another crucial detail
- Point 3: Final consideration

Would you like me to elaborate on any of these?`,
  `Here's an example of code formatting:

\`\`\`typescript
function modernExample() {
  console.log('This is a TypeScript example!');
  return 'Hello from Next.js 15!';
}
\`\`\`

This demonstrates how I can format code in my responses with proper syntax highlighting.`,
  "I can help with various topics including programming, general knowledge, analysis, and more. What would you like to explore?",
];

export default function Home() {
  const {
    currentConversationId,
    conversations,
    currentMessages,
    isLoading,
    streamingMessage,
    setStreamingMessage,
    setIsLoading,
    createNewConversation,
    selectConversation,
    deleteConversation,
    addMessage,
  } = useConversationManager();

  const [sidebarVisible, setSidebarVisible] = useState(true);

  const handleSendMessage = async (content: string) => {
    if (isLoading || !currentConversationId) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setIsLoading(true);

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    // Start streaming response
    const response = mockResponses[Math.floor(Math.random() * mockResponses.length)];
    setStreamingMessage({ content: "", isStreaming: true });
    setIsLoading(false);

    // Simulate streaming
    for (let i = 0; i <= response.length; i++) {
      setStreamingMessage({
        content: response.slice(0, i),
        isStreaming: true,
      });
      await new Promise((resolve) => setTimeout(resolve, 20 + Math.random() * 30));
    }

    // Complete the message
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: response,
      timestamp: new Date(),
    };

    addMessage(assistantMessage);
    setStreamingMessage({ content: "", isStreaming: false });
  };

  const handleNewConversation = () => {
    const newId = createNewConversation();
    selectConversation(newId);
  };

  const handleConversationSelect = (id: string) => {
    selectConversation(id);
    // Hide sidebar on mobile after selection
    if (window.innerWidth < 768) {
      setSidebarVisible(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-background">
      {/* Mobile sidebar toggle */}
      <div className="md:hidden absolute top-4 left-4 z-50">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSidebarVisible(!sidebarVisible)}
        >
          {sidebarVisible ? <X size={16} /> : <Menu size={16} />}
        </Button>
      </div>

      {/* Sidebar */}
      <div className={`${sidebarVisible ? 'translate-x-0' : '-translate-x-full'
        } transition-transform duration-300 ease-in-out fixed md:relative z-40 h-full`}>
        <ConversationSidebar
          currentConversationId={currentConversationId}
          onConversationSelect={handleConversationSelect}
          onNewConversation={handleNewConversation}
          onDeleteConversation={deleteConversation}
        />
      </div>

      {/* Overlay for mobile */}
      {sidebarVisible && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setSidebarVisible(false)}
        />
      )}

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Card className="flex flex-col h-full rounded-none border-0 md:border md:rounded-r-lg">
          <ChatHeader
            messageCount={currentMessages.length - 1}
            conversationTitle={conversations.get(currentConversationId || '')?.title}
          />

          <div className="flex-1 overflow-hidden">
            <ChatMessageList
              messages={currentMessages}
              streamingMessage={streamingMessage.isStreaming ? streamingMessage : undefined}
              isLoading={isLoading}
            />
          </div>

          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={isLoading || streamingMessage.isStreaming}
            placeholder="Ask me anything..."
          />
        </Card>
      </div>
    </div>
  );
}
