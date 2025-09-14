import { NextResponse } from 'next/server';
import { getConfig, validateConfig, getBuildInfo } from '@/lib/config';

export async function GET() {
    try {
        const config = getConfig();
        const validation = validateConfig();
        const buildInfo = getBuildInfo();

        const healthData = {
            status: validation.isValid ? 'healthy' : 'degraded',
            timestamp: new Date().toISOString(),
            version: buildInfo.version,
            environment: config.environment,
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            config: {
                appUrl: config.appUrl,
                apiUrl: config.apiUrl,
                hasApiUrl: !!config.apiUrl,
                isDevelopment: config.isDevelopment,
                isProduction: config.isProduction,
            },
            validation: {
                isValid: validation.isValid,
                errors: validation.errors,
            },
            build: buildInfo,
        };

        const statusCode = validation.isValid ? 200 : 503;

        return NextResponse.json(healthData, {
            status: statusCode,
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
            }
        });
    } catch (error) {
        return NextResponse.json(
            {
                status: 'unhealthy',
                error: error instanceof Error ? error.message : 'Unknown error',
                timestamp: new Date().toISOString(),
            },
            { status: 500 }
        );
    }
}

export async function HEAD() {
    return new Response(null, { status: 200 });
}