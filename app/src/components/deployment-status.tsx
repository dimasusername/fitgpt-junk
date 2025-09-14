"use client";

import { useState, useEffect } from 'react';

interface HealthStatus {
    status: 'healthy' | 'degraded' | 'unhealthy';
    timestamp: string;
    version: string;
    environment: string;
    config: {
        appUrl: string;
        apiUrl: string;
        hasApiUrl: boolean;
        isDevelopment: boolean;
        isProduction: boolean;
    };
    validation?: {
        isValid: boolean;
        errors: string[];
    };
}

export function DeploymentStatus() {
    const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    useEffect(() => {
        if (!mounted) return;

        const checkHealth = async () => {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                setHealthStatus(data);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to check health');
            } finally {
                setLoading(false);
            }
        };

        checkHealth();

        // Check health every 30 seconds
        const interval = setInterval(checkHealth, 30000);
        return () => clearInterval(interval);
    }, [mounted]);

    // Prevent hydration mismatch by not rendering until mounted
    if (!mounted) {
        return (
            <div className="text-sm text-muted-foreground">
                Checking deployment status...
            </div>
        );
    }

    if (loading) {
        return (
            <div className="text-sm text-muted-foreground">
                Checking deployment status...
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-sm text-destructive">
                ⚠️ Health check failed: {error}
            </div>
        );
    }

    if (!healthStatus) {
        return null;
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'healthy':
                return 'text-green-600';
            case 'degraded':
                return 'text-yellow-600';
            case 'unhealthy':
                return 'text-red-600';
            default:
                return 'text-gray-600';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'healthy':
                return '✅';
            case 'degraded':
                return '⚠️';
            case 'unhealthy':
                return '❌';
            default:
                return '❓';
        }
    };

    return (
        <div className="text-xs space-y-1">
            <div className={`flex items-center gap-1 ${getStatusColor(healthStatus.status)}`}>
                <span>{getStatusIcon(healthStatus.status)}</span>
                <span className="font-medium">
                    {healthStatus.status.charAt(0).toUpperCase() + healthStatus.status.slice(1)}
                </span>
                <span className="text-muted-foreground">
                    v{healthStatus.version} ({healthStatus.environment})
                </span>
            </div>

            {healthStatus.validation && !healthStatus.validation.isValid && (
                <div className="text-yellow-600 text-xs">
                    Configuration issues: {healthStatus.validation.errors.join(', ')}
                </div>
            )}

            <div className="text-muted-foreground">
                API: {healthStatus.config.hasApiUrl ? '✅ Configured' : '⚠️ Not configured'}
            </div>
        </div>
    );
}