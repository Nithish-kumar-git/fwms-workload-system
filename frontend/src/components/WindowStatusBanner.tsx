import { useEffect, useState, useRef } from 'react';
import { getPrefWindowStatus } from '../api/client';
import { Clock, CheckCircle2, CalendarClock, XCircle } from 'lucide-react';

interface WindowStatus {
    is_open: boolean;
    status: 'OPEN' | 'CLOSED' | 'SCHEDULED' | string;
    remaining_seconds: number | null;
    end_time: string | null;
    start_time: string | null;
}

function formatCountdown(totalSeconds: number): string {
    if (totalSeconds <= 0) return '0s';
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    if (h > 0) return `${h}h ${m}m ${s}s`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
}

const STATUS_CONFIG = {
    OPEN: {
        icon: CheckCircle2,
        label: 'OPEN',
        badgeClass: 'badge badge-success',
        borderColor: 'rgba(22, 163, 74, 0.2)',
        bgGlow: 'rgba(22, 163, 74, 0.04)',
        dotColor: '#16a34a',
    },
    SCHEDULED: {
        icon: CalendarClock,
        label: 'SCHEDULED',
        badgeClass: 'badge badge-warning',
        borderColor: 'rgba(245, 158, 11, 0.2)',
        bgGlow: 'rgba(245, 158, 11, 0.04)',
        dotColor: '#f59e0b',
    },
    CLOSED: {
        icon: XCircle,
        label: 'CLOSED',
        badgeClass: 'badge badge-danger',
        borderColor: 'rgba(220, 38, 38, 0.15)',
        bgGlow: 'rgba(220, 38, 38, 0.03)',
        dotColor: '#dc2626',
    },
} as const;

export default function WindowStatusBanner() {
    const [status, setStatus] = useState<WindowStatus | null>(null);
    const [countdown, setCountdown] = useState<number | null>(null);
    const [error, setError] = useState(false);
    const timerRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);


    useEffect(() => {
        const fetchStatus = () => {
            getPrefWindowStatus()
                .then((r) => {
                    setStatus(r.data);
                    setError(false);
                    if (r.data.is_open && r.data.remaining_seconds != null) {
                        setCountdown(Math.max(0, Math.floor(r.data.remaining_seconds)));
                    } else {
                        setCountdown(null);
                    }
                })
                .catch(() => setError(true));
        };
        fetchStatus();
        const poll = setInterval(fetchStatus, 10000);
        return () => clearInterval(poll);
    }, []);

    useEffect(() => {
        if (countdown == null || countdown <= 0) {
            if (timerRef.current) clearInterval(timerRef.current);
            return;
        }
        timerRef.current = setInterval(() => {
            setCountdown((prev) => {
                if (prev == null || prev <= 1) return 0;
                return prev - 1;
            });
        }, 1000);
        return () => { if (timerRef.current) clearInterval(timerRef.current); };
    }, [countdown != null && countdown > 0]);

    if (error || !status) return null;

    const stateKey = (status.status?.toUpperCase() ?? 'CLOSED') as keyof typeof STATUS_CONFIG;
    const config = STATUS_CONFIG[stateKey] || STATUS_CONFIG.CLOSED;
    const Icon = config.icon;

    return (
        <div
            id="window-status-banner"
            className="glass-card"
            style={{
                padding: '1rem 1.5rem',
                marginBottom: '1.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '1rem',
                borderColor: config.borderColor,
                background: config.bgGlow,
                animation: 'fadeIn 0.4s ease-out',
            }}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <Icon size={20} style={{ color: config.dotColor, flexShrink: 0 }} />
                <span style={{ fontWeight: 500, fontSize: '0.9375rem', color: '#374151' }}>
                    Preference Window
                </span>
                <span className={config.badgeClass}>
                    <span
                        style={{
                            width: 6, height: 6, borderRadius: '50%',
                            backgroundColor: config.dotColor, display: 'inline-block',
                            marginRight: 6,
                            animation: stateKey === 'OPEN' ? 'pulse-dot 2s ease-in-out infinite' : undefined,
                        }}
                    />
                    {config.label}
                </span>
            </div>

            {stateKey === 'OPEN' && countdown != null && countdown > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#6b7280', fontSize: '0.875rem' }}>
                    <Clock size={14} />
                    <span>Closes in <strong style={{ color: countdown < 300 ? '#dc2626' : '#16a34a' }}>{formatCountdown(countdown)}</strong></span>
                </div>
            )}

            {stateKey === 'OPEN' && countdown != null && countdown <= 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f59e0b', fontSize: '0.875rem' }}>
                    <Clock size={14} />
                    <span>Window expired — refreshing...</span>
                </div>
            )}

            {stateKey === 'SCHEDULED' && status.start_time && (
                <div style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                    Opens {new Date(status.start_time).toLocaleString()}
                </div>
            )}
        </div>
    );
}
