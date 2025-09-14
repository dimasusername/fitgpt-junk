"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Copy, User, Bot } from "lucide-react";
import { forwardRef } from "react";
import { toast } from "sonner";
import { MarkdownRenderer } from "./markdown-renderer";

interface ChatBubbleProps {
    message: {
        id: string;
        role: "user" | "assistant";
        content: string;
        timestamp: Date;
    };
    isStreaming?: boolean;
}

export const ChatBubble = forwardRef<HTMLDivElement, ChatBubbleProps>(
    ({ message, isStreaming = false }, ref) => {
        const isUser = message.role === "user";

        const copyToClipboard = async () => {
            try {
                await navigator.clipboard.writeText(message.content);
                toast.success("Copied to clipboard");
            } catch {
                toast.error("Failed to copy");
            }
        };

        return (
            <div
                ref={ref}
                className={cn(
                    "flex w-full gap-3 px-4 py-6",
                    isUser ? "justify-end" : "justify-start"
                )}
            >
                {!isUser && (
                    <Avatar className="h-8 w-8 shrink-0">
                        <AvatarFallback className="bg-primary text-primary-foreground">
                            <Bot className="h-4 w-4" />
                        </AvatarFallback>
                    </Avatar>
                )}

                <div
                    className={cn(
                        "flex max-w-[85%] flex-col gap-2",
                        isUser && "items-end"
                    )}
                >
                    <div
                        className={cn(
                            "rounded-2xl px-4 py-3 text-sm",
                            isUser
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted text-muted-foreground"
                        )}
                    >
                        <MarkdownRenderer content={message.content} />
                        {isStreaming && (
                            <span className="ml-1 animate-pulse">▋</span>
                        )}
                    </div>

                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>
                            {message.timestamp.toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                            })}
                        </span>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0 opacity-60 hover:opacity-100"
                            onClick={copyToClipboard}
                        >
                            <Copy className="h-3 w-3" />
                        </Button>
                    </div>
                </div>

                {isUser && (
                    <Avatar className="h-8 w-8 shrink-0">
                        <AvatarFallback className="bg-secondary">
                            <User className="h-4 w-4" />
                        </AvatarFallback>
                    </Avatar>
                )}
            </div>
        );
    }
);

ChatBubble.displayName = "ChatBubble";
