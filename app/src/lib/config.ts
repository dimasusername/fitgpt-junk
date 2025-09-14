/**
 * Application configuration utilities
 * Handles environment-specific settings and validation
 */

export interface AppConfig {
    appUrl: string;
    apiUrl: string;
    environment: 'development' | 'production' | 'test';
    isDevelopment: boolean;
    isProduction: boolean;
}

/**
 * Get application configuration from environment variables
 */
export function getConfig(): AppConfig {
    const environment = (process.env.NODE_ENV as AppConfig['environment']) || 'development';

    // Default URLs for development
    const defaultAppUrl = 'http://localhost:3000';
    const defaultApiUrl = 'http://localhost:8000';

    const appUrl = process.env.NEXT_PUBLIC_APP_URL || defaultAppUrl;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || defaultApiUrl;

    return {
        appUrl,
        apiUrl,
        environment,
        isDevelopment: environment === 'development',
        isProduction: environment === 'production',
    };
}

/**
 * Validate required environment variables
 */
export function validateConfig(): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!process.env.NEXT_PUBLIC_APP_URL && process.env.NODE_ENV === 'production') {
        errors.push('NEXT_PUBLIC_APP_URL is required in production');
    }

    if (!process.env.NEXT_PUBLIC_API_URL && process.env.NODE_ENV === 'production') {
        errors.push('NEXT_PUBLIC_API_URL is required in production');
    }

    return {
        isValid: errors.length === 0,
        errors,
    };
}

/**
 * Get API endpoint URL with path
 */
export function getApiUrl(path: string = ''): string {
    const config = getConfig();
    const baseUrl = config.apiUrl.endsWith('/') ? config.apiUrl.slice(0, -1) : config.apiUrl;
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${baseUrl}${cleanPath}`;
}

/**
 * Check if we're running in a browser environment
 */
export function isBrowser(): boolean {
    return typeof window !== 'undefined';
}

/**
 * Get build information
 */
export function getBuildInfo() {
    return {
        version: process.env.npm_package_version || '0.1.0',
        buildTime: process.env.BUILD_TIME || new Date().toISOString(),
        nodeEnv: process.env.NODE_ENV || 'development',
    };
}