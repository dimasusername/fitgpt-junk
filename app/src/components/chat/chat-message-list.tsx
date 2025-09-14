"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatBubble } from "./chat-bubble";
import { ChatLoading } from "./chat-loading";
import { useEffect, useRef } from "react";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

interface ChatMessageListProps {
    messages: Message[];
    streamingMessage?: {
        content: string;
        isStreaming: boolean;
    };
    isLoading?: boolean;
}

export function ChatMessageList({ messages, streamingMessage, isLoading = false }: ChatMessageListProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, streamingMessage, isLoading]);

    return (
        <ScrollArea className="flex-1 px-0">
            <div className="space-y-0">
                {messages.map((message) => (
                    <ChatBubble key={message.id} message={message} />
                ))}

                {streamingMessage?.isStreaming && (
                    <ChatBubble
                        message={{
                            id: "streaming",
                            role: "assistant",
                            content: streamingMessage.content,
                            timestamp: new Date(),
                        }}
                        isStreaming={true}
                    />
                )}

                {isLoading && !streamingMessage?.isStreaming && <ChatLoading />}

                <div ref={bottomRef} />
            </div>
        </ScrollArea>
    );
}
