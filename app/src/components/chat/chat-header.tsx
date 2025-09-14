"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { MessageSquare } from "lucide-react";
import { DeploymentStatus } from "@/components/deployment-status";
import { getConfig } from "@/lib/config";

interface ChatHeaderProps {
    messageCount: number;
    conversationTitle?: string;
}

export function ChatHeader({ messageCount, conversationTitle }: ChatHeaderProps) {
    const [mounted, setMounted] = useState(false);
    const [isDevelopment, setIsDevelopment] = useState(false);

    useEffect(() => {
        setMounted(true);
        const config = getConfig();
        setIsDevelopment(config.isDevelopment);
    }, []);

    return (
        <Card className="border-b rounded-none border-l-0 border-r-0 border-t-0">
            <div className="flex items-center justify-between p-4">
                <div className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-primary" />
                    <h1 className="text-lg font-semibold">
                        {conversationTitle || "AI Assistant"}
                    </h1>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-sm text-muted-foreground">
                        {messageCount} message{messageCount !== 1 ? "s" : ""}
                    </div>
                    {mounted && isDevelopment && (
                        <div className="border-l pl-4">
                            <DeploymentStatus />
                        </div>
                    )}
                </div>
            </div>
        </Card>
    );
}
