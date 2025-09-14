"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot } from "lucide-react";

export function ChatLoading() {
    return (
        <div className="flex w-full gap-3 px-4 py-6">
            <Avatar className="h-8 w-8 shrink-0">
                <AvatarFallback className="bg-primary text-primary-foreground">
                    <Bot className="h-4 w-4" />
                </AvatarFallback>
            </Avatar>

            <div className="flex max-w-[85%] flex-col gap-2">
                <div className="rounded-2xl bg-muted px-4 py-3">
                    <div className="flex items-center gap-1">
                        <div className="h-2 w-2 bg-muted-foreground/60 rounded-full animate-pulse"></div>
                        <div className="h-2 w-2 bg-muted-foreground/60 rounded-full animate-pulse" style={{ animationDelay: "0.2s" }}></div>
                        <div className="h-2 w-2 bg-muted-foreground/60 rounded-full animate-pulse" style={{ animationDelay: "0.4s" }}></div>
                    </div>
                </div>
            </div>
        </div>
    );
}
