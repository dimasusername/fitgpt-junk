"use client";

import { useState, useCallback, useEffect } from "react";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

interface Conversation {
    id: string;
    title: string;
    lastMessage: string;
    timestamp: Date;
    messageCount: number;
    messages: Message[];
}

interface UseConversationManagerReturn {
    currentConversationId: string | null;
    conversations: Map<string, Conversation>;
    currentMessages: Message[];
    isLoading: boolean;
    streamingMessage: { content: string; isStreaming: boolean };
    setStreamingMessage: (message: { content: string; isStreaming: boolean }) => void;
    setIsLoading: (loading: boolean) => void;
    createNewConversation: () => string;
    selectConversation: (id: string) => void;
    deleteConversation: (id: string) => void;
    addMessage: (message: Message, conversationId?: string) => void;
    updateConversationTitle: (id: string, title: string) => void;
}

const WELCOME_MESSAGE: Message = {
    id: "welcome",
    role: "assistant",
    content: "Hello! I'm your AI assistant, rebuilt with the latest technologies. How can I help you today?",
    timestamp: new Date(2024, 0, 1), // Fixed date to prevent hydration mismatch
};

export function useConversationManager(): UseConversationManagerReturn {
    const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
    const [conversations, setConversations] = useState<Map<string, Conversation>>(new Map());
    const [isLoading, setIsLoading] = useState(false);
    const [streamingMessage, setStreamingMessage] = useState<{
        content: string;
        isStreaming: boolean;
    }>({ content: "", isStreaming: false });

    // Initialize with default conversation or load from localStorage
    useEffect(() => {
        const savedConversations = localStorage.getItem('fitgpt_conversations');
        const savedCurrentId = localStorage.getItem('fitgpt_current_conversation');

        if (savedConversations) {
            try {
                const parsed = JSON.parse(savedConversations);
                const conversationsMap = new Map<string, Conversation>();

                Object.entries(parsed).forEach(([id, conv]) => {
                    const typedConv = conv as Conversation & { timestamp: string; messages: (Message & { timestamp: string })[] };
                    conversationsMap.set(id, {
                        ...typedConv,
                        timestamp: new Date(typedConv.timestamp),
                        messages: typedConv.messages.map((msg) => ({
                            ...msg,
                            timestamp: new Date(msg.timestamp),
                        })),
                    });
                });

                setConversations(conversationsMap);

                if (savedCurrentId && conversationsMap.has(savedCurrentId)) {
                    setCurrentConversationId(savedCurrentId);
                } else if (conversationsMap.size > 0) {
                    // Select the most recent conversation
                    const mostRecent = Array.from(conversationsMap.values())
                        .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())[0];
                    setCurrentConversationId(mostRecent.id);
                } else {
                    const createNewConversationSync = (): string => {
                        const id = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                        const newConversation: Conversation = {
                            id,
                            title: "New Conversation",
                            lastMessage: "",
                            timestamp: new Date(),
                            messageCount: 1,
                            messages: [WELCOME_MESSAGE],
                        };
                        setConversations(new Map().set(id, newConversation));
                        return id;
                    };

                    const defaultConversationId = createNewConversationSync();
                    setCurrentConversationId(defaultConversationId);
                }
            } catch (error) {
                console.error('Failed to parse saved conversations:', error);
                const createNewConversationSync = (): string => {
                    const id = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                    const newConversation: Conversation = {
                        id,
                        title: "New Conversation",
                        lastMessage: "",
                        timestamp: new Date(),
                        messageCount: 1,
                        messages: [WELCOME_MESSAGE],
                    };
                    setConversations(new Map().set(id, newConversation));
                    return id;
                };

                const defaultConversationId = createNewConversationSync();
                setCurrentConversationId(defaultConversationId);
            }
        } else {
            const createNewConversationSync = (): string => {
                const id = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                const newConversation: Conversation = {
                    id,
                    title: "New Conversation",
                    lastMessage: "",
                    timestamp: new Date(),
                    messageCount: 1,
                    messages: [WELCOME_MESSAGE],
                };
                setConversations(new Map().set(id, newConversation));
                return id;
            };

            const defaultConversationId = createNewConversationSync();
            setCurrentConversationId(defaultConversationId);
        }
    }, []);

    // Save conversations to localStorage whenever they change
    useEffect(() => {
        if (conversations.size > 0) {
            const conversationsObj = Object.fromEntries(
                Array.from(conversations.entries()).map(([id, conv]) => [
                    id,
                    {
                        ...conv,
                        timestamp: conv.timestamp.toISOString(),
                        messages: conv.messages.map(msg => ({
                            ...msg,
                            timestamp: msg.timestamp.toISOString(),
                        })),
                    },
                ])
            );

            localStorage.setItem('fitgpt_conversations', JSON.stringify(conversationsObj));
        }
    }, [conversations]);

    // Save current conversation ID
    useEffect(() => {
        if (currentConversationId) {
            localStorage.setItem('fitgpt_current_conversation', currentConversationId);
        }
    }, [currentConversationId]);

    const createNewConversation = useCallback((): string => {
        const id = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const newConversation: Conversation = {
            id,
            title: "New Conversation",
            lastMessage: "",
            timestamp: new Date(),
            messageCount: 1,
            messages: [WELCOME_MESSAGE],
        };

        setConversations(prev => new Map(prev.set(id, newConversation)));
        return id;
    }, []);

    const selectConversation = useCallback((id: string) => {
        if (conversations.has(id)) {
            setCurrentConversationId(id);
        }
    }, [conversations]);

    const deleteConversation = useCallback((id: string) => {
        setConversations(prev => {
            const newMap = new Map(prev);
            newMap.delete(id);
            return newMap;
        });

        // If we deleted the current conversation, create a new one
        if (currentConversationId === id) {
            const newConversationId = createNewConversation();
            setCurrentConversationId(newConversationId);
        }
    }, [currentConversationId, createNewConversation]);

    const addMessage = useCallback((message: Message, conversationId?: string) => {
        const targetId = conversationId || currentConversationId;
        if (!targetId) return;

        setConversations(prev => {
            const newMap = new Map(prev);
            const conversation = newMap.get(targetId);
            if (conversation) {
                const updatedConversation: Conversation = {
                    ...conversation,
                    messages: [...conversation.messages, message],
                    messageCount: conversation.messages.length + 1,
                    lastMessage: message.content.substring(0, 100),
                    timestamp: new Date(),
                };

                // Auto-generate title from first user message
                if (conversation.title === "New Conversation" && message.role === "user") {
                    updatedConversation.title = message.content.length > 40
                        ? message.content.substring(0, 40) + "..."
                        : message.content;
                }

                newMap.set(targetId, updatedConversation);
            }
            return newMap;
        });
    }, [currentConversationId]);

    const updateConversationTitle = useCallback((id: string, title: string) => {
        setConversations(prev => {
            const newMap = new Map(prev);
            const conversation = newMap.get(id);
            if (conversation) {
                newMap.set(id, { ...conversation, title });
            }
            return newMap;
        });
    }, []);

    const currentMessages = currentConversationId
        ? conversations.get(currentConversationId)?.messages || []
        : [];

    return {
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
        updateConversationTitle,
    };
}
