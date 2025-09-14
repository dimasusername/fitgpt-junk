"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send } from "lucide-react";
import { useState, KeyboardEvent } from "react";

interface ChatInputProps {
    onSendMessage: (message: string) => void;
    disabled?: boolean;
    placeholder?: string;
}

export function ChatInput({
    onSendMessage,
    disabled = false,
    placeholder = "Type your message here...",
}: ChatInputProps) {
    const [input, setInput] = useState("");

    const handleSubmit = () => {
        if (!input.trim() || disabled) return;

        onSendMessage(input.trim());
        setInput("");
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="flex gap-2 p-4 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex-1 relative">
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={placeholder}
                    disabled={disabled}
                    className="pr-12"
                />
                <Button
                    onClick={handleSubmit}
                    disabled={!input.trim() || disabled}
                    size="sm"
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                >
                    <Send className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}
