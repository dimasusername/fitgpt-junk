"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

interface MarkdownRendererProps {
    content: string;
    className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
    return (
        <div className={cn("prose prose-sm dark:prose-invert max-w-none", className)}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    code: ({ className, children, ...props }) => {
                        const match = /language-(\w+)/.exec(className || "");
                        const isInline = !props.node || props.node.tagName !== "pre";

                        if (isInline) {
                            return (
                                <code
                                    className={cn(
                                        "relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm",
                                        className
                                    )}
                                    {...props}
                                >
                                    {children}
                                </code>
                            );
                        }

                        return (
                            <div className="relative">
                                <pre className="overflow-x-auto rounded-lg bg-muted p-4">
                                    <code
                                        className={cn("font-mono text-sm", className)}
                                        {...props}
                                    >
                                        {children}
                                    </code>
                                </pre>
                                {match && (
                                    <div className="absolute top-2 right-2 rounded bg-muted-foreground/10 px-2 py-1 text-xs text-muted-foreground">
                                        {match[1]}
                                    </div>
                                )}
                            </div>
                        );
                    },
                    blockquote: ({ children }) => (
                        <blockquote className="border-l-4 border-muted-foreground/25 pl-4 italic">
                            {children}
                        </blockquote>
                    ),
                    ul: ({ children }) => (
                        <ul className="list-disc pl-6 space-y-1">{children}</ul>
                    ),
                    ol: ({ children }) => (
                        <ol className="list-decimal pl-6 space-y-1">{children}</ol>
                    ),
                    li: ({ children }) => (
                        <li className="text-sm">{children}</li>
                    ),
                    h1: ({ children }) => (
                        <h1 className="text-lg font-semibold mt-4 mb-2">{children}</h1>
                    ),
                    h2: ({ children }) => (
                        <h2 className="text-base font-semibold mt-3 mb-2">{children}</h2>
                    ),
                    h3: ({ children }) => (
                        <h3 className="text-sm font-semibold mt-2 mb-1">{children}</h3>
                    ),
                    p: ({ children }) => (
                        <p className="text-sm leading-relaxed mb-2 last:mb-0">{children}</p>
                    ),
                    a: ({ children, href }) => (
                        <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary underline hover:no-underline"
                        >
                            {children}
                        </a>
                    ),
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}