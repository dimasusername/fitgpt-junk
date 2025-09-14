/**
 * API client for conversation and session management
 */

import { getApiUrl } from '@/lib/config';

export interface SessionSummary {
    session_id: string;
    query: string;
    success: boolean;
    tool_calls: number;
    session_start: string;
    last_activity: string;
}

export interface AgentQueryRequest {
    query: string;
    session_id?: string;
    context?: Record<string, unknown>;
    stream?: boolean;
}

export interface AgentQueryResponse {
    session_id: string;
    query: string;
    answer: string | null;
    success: boolean;
    error: string | null;
    reasoning_steps: number;
    tool_calls: number;
    session_duration: number;
    detailed_reasoning: Array<{
        step: number;
        thought: string;
        action: string;
        observation: string;
        tools_used: string[];
    }>;
    timestamp: string;
}

class ApiClient {
    private baseUrl: string;

    constructor() {
        this.baseUrl = getApiUrl('/api');
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }

        return response.json();
    }

    // Session management
    async listActiveSessions(): Promise<SessionSummary[]> {
        return this.request<SessionSummary[]>('/agent/sessions');
    }

    async getSession(sessionId: string): Promise<Record<string, unknown>> {
        return this.request(`/agent/sessions/${sessionId}`);
    }

    async clearSession(sessionId: string): Promise<{ message: string; session_id: string }> {
        return this.request(`/agent/sessions/${sessionId}`, {
            method: 'DELETE',
        });
    }

    async clearAllSessions(): Promise<{ message: string; sessions_cleared: number }> {
        return this.request('/agent/sessions', {
            method: 'DELETE',
        });
    }

    // Agent queries
    async processQuery(request: AgentQueryRequest): Promise<AgentQueryResponse> {
        return this.request<AgentQueryResponse>('/agent/query', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    }

    // Streaming queries
    async *processQueryStreaming(request: AgentQueryRequest): AsyncGenerator<Record<string, unknown>, void, unknown> {
        const url = `${this.baseUrl}/agent/query/stream`;

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`Streaming request failed: ${response.status} ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
            throw new Error('Response body is not readable');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { value, done } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // Process complete lines
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6); // Remove 'data: ' prefix

                        if (data.trim() === '') continue;

                        try {
                            const parsed = JSON.parse(data);

                            if (parsed.type === 'stream_complete') {
                                return;
                            }

                            yield parsed;
                        } catch {
                            console.warn('Failed to parse SSE data:', data);
                        }
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }

    // Health check
    async getHealth(): Promise<Record<string, unknown>> {
        return this.request('/health');
    }

    async getAgentHealth(): Promise<Record<string, unknown>> {
        return this.request('/agent/health');
    }

    // Monitoring
    async getMonitoringStats(): Promise<Record<string, unknown>> {
        return this.request('/agent/monitoring');
    }

    // Tools
    async listAvailableTools(): Promise<Record<string, unknown>> {
        return this.request('/agent/tools');
    }
}

// Export a singleton instance
export const apiClient = new ApiClient();

// Helper function to check if API is available
export async function checkApiAvailability(): Promise<boolean> {
    try {
        await apiClient.getHealth();
        return true;
    } catch {
        console.warn('API is not available');
        return false;
    }
}
