"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Plus, MessageSquare, Trash2 } from "lucide-react";

interface Conversation {
    id: string;
    title: string;
    lastMessage: string;
    timestamp: Date;
    messageCount: number;
}

interface ConversationSidebarProps {
    currentConversationId?: string | null;
    onConversationSelect: (id: string) => void;
    onNewConversation: () => void;
    onDeleteConversation: (id: string) => void;
}

export function ConversationSidebar({
    currentConversationId,
    onConversationSelect,
    onNewConversation,
    onDeleteConversation,
}: ConversationSidebarProps) {
    const [conversations, setConversations] = useState<Conversation[]>([]);

    // Load conversations from localStorage (since backend doesn't persist conversations yet)
    useEffect(() => {
        const savedConversations = localStorage.getItem('conversations');
        if (savedConversations) {
            try {
                const parsed = JSON.parse(savedConversations).map((conv: Conversation) => ({
                    ...conv,
                    timestamp: new Date(conv.timestamp)
                }));
                setConversations(parsed);
            } catch (error) {
                console.error('Failed to parse saved conversations:', error);
                setConversations([]);
            }
        }
    }, []);

    // Save conversations to localStorage
    const saveConversations = (convs: Conversation[]) => {
        localStorage.setItem('conversations', JSON.stringify(convs));
        setConversations(convs);
    };

    const handleNewConversation = () => {
        const newConversation: Conversation = {
            id: `conv_${Date.now()}`,
            title: "New Conversation",
            lastMessage: "",
            timestamp: new Date(),
            messageCount: 0,
        };

        const updated = [newConversation, ...conversations];
        saveConversations(updated);
        onNewConversation();
        onConversationSelect(newConversation.id);
    };

    const handleDeleteConversation = (id: string) => {
        const updated = conversations.filter(conv => conv.id !== id);
        saveConversations(updated);
        onDeleteConversation(id);
    };

    const updateConversation = useCallback((id: string, updates: Partial<Conversation>) => {
        const updated = conversations.map(conv =>
            conv.id === id ? { ...conv, ...updates } : conv
        );
        saveConversations(updated);
    }, [conversations]);

    // Expose update function to parent components
    useEffect(() => {
        (window as unknown as Record<string, unknown>).updateConversation = updateConversation;
        return () => {
            delete (window as unknown as Record<string, unknown>).updateConversation;
        };
    }, [conversations, updateConversation]);

    const formatTimestamp = (timestamp: Date) => {
        const now = new Date();
        const diff = now.getTime() - timestamp.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) {
            return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (days === 1) {
            return 'Yesterday';
        } else if (days < 7) {
            return `${days} days ago`;
        } else {
            return timestamp.toLocaleDateString();
        }
    };

    return (
        <Card className="h-full w-80 flex flex-col border-r rounded-none md:rounded-l-lg">
            <div className="p-4 border-b">
                <Button
                    onClick={handleNewConversation}
                    className="w-full justify-start gap-2"
                    variant="outline"
                >
                    <Plus size={16} />
                    New Conversation
                </Button>
            </div>

            <ScrollArea className="flex-1 p-2">
                <div className="space-y-2">
                    {conversations.length === 0 ? (
                        <div className="p-4 text-center text-muted-foreground">
                            <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
                            <p className="text-sm">No conversations yet</p>
                            <p className="text-xs">Start a new conversation to begin</p>
                        </div>
                    ) : (
                        conversations.map((conversation) => (
                            <div
                                key={conversation.id}
                                className={`group p-3 rounded-lg border cursor-pointer transition-all hover:bg-accent/50 ${currentConversationId === conversation.id
                                    ? 'bg-accent border-accent-foreground/20'
                                    : 'border-border/50'
                                    }`}
                                onClick={() => onConversationSelect(conversation.id)}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-medium text-sm truncate">
                                            {conversation.title}
                                        </h3>
                                        {conversation.lastMessage && (
                                            <p className="text-xs text-muted-foreground truncate mt-1">
                                                {conversation.lastMessage}
                                            </p>
                                        )}
                                        <div className="flex items-center justify-between mt-2">
                                            <span className="text-xs text-muted-foreground">
                                                {formatTimestamp(conversation.timestamp)}
                                            </span>
                                            <span className="text-xs text-muted-foreground">
                                                {conversation.messageCount} messages
                                            </span>
                                        </div>
                                    </div>

                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 ml-2"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteConversation(conversation.id);
                                        }}
                                    >
                                        <Trash2 size={12} />
                                    </Button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </ScrollArea>

            <div className="p-4 border-t">
                <div className="text-xs text-muted-foreground">
                    {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
                </div>
            </div>
        </Card>
    );
}
