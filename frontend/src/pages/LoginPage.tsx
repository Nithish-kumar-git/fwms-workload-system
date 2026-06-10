import { useNavigate } from 'react-router-dom';
import { Shield, User, Crown, Rocket } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { demoLogin } from '../api/client';

type BackendStatus = 'checking' | 'online' | 'waking';

export default function LoginPage() {
    const navigate = useNavigate();
    const [error, setError] = useState('');
    const [loading, setLoading] = useState('');
    const [backendStatus, setBackendStatus] = useState<BackendStatus>('checking');
    const { refreshUser } = useAuth();

    // Backend health check on mount
    useEffect(() => {
        const checkHealth = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL;
                if (!apiUrl) {
                    setBackendStatus('online'); // Local dev, assume online
                    return;
                }

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);

                const response = await fetch(`${apiUrl}/api/health`, {
                    signal: controller.signal,
                });
                clearTimeout(timeoutId);

                if (response.ok) {
                    setBackendStatus('online');
                } else {
                    setBackendStatus('waking');
                }
            } catch (err) {
                // Timeout or network error - backend is waking
                setBackendStatus('waking');
            }
        };

        checkHealth();
    }, []);

    // Retry health check every 8 seconds when waking
    useEffect(() => {
        if (backendStatus !== 'waking') return;

        const intervalId = setInterval(async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL;
                if (!apiUrl) return;

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);

                const response = await fetch(`${apiUrl}/api/health`, {
                    signal: controller.signal,
                });
                clearTimeout(timeoutId);

                if (response.ok) {
                    setBackendStatus('online');
                }
            } catch {
                // Still waking, will retry
            }
        }, 8000);

        return () => clearInterval(intervalId);
    }, [backendStatus]);

    const handleGoogleLogin = async () => {
        setError('');
        setLoading('google');
        try {
            const apiUrl = import.meta.env.VITE_API_URL;
            if (!apiUrl) {
                throw new Error("VITE_API_URL is not defined");
            }
            const res = await fetch(`${apiUrl}/api/auth/login`);
            const data = await res.json();
            if (data.authorization_url) {
                window.location.href = data.authorization_url;
            } else {
                setError('Could not get Google login URL');
            }
        } catch {
            setError('Failed to connect to server');
        } finally {
            setLoading('');
        }
    };

    const handleDevLogin = async (staffId: number, label: string) => {
        setError('');
        setLoading(label);
        try {
            const apiUrl = import.meta.env.VITE_API_URL;
            if (!apiUrl) {
                throw new Error("VITE_API_URL is not defined");
            }
            const res = await fetch(`${apiUrl}/api/auth/dev-login/${staffId}`, { method: 'POST' });
            const data = await res.json();

            console.log(`DEV LOGIN (${label}): staff_id=${staffId}`, data);

            if (!res.ok) {
                setError(data.detail || `Dev login failed (${res.status})`);
                return;
            }
            if (data.token) {
                localStorage.setItem('jwt_token', data.token);
                await refreshUser();
                // Route by role
                switch (data.role) {
                    case 'hod': navigate('/hod-dashboard'); break;
                    case 'tt_coordinator': navigate('/dashboard'); break;
                    default: navigate('/faculty-dashboard'); break;
                }
            } else {
                setError('No token received from server');
            }
        } catch {
            setError('Failed to connect to server');
        } finally {
            setLoading('');
        }
    };

    const handleDemoLogin = async () => {
        setError('');
        setLoading('demo');
        try {
            const res = await demoLogin();
            const data = res.data;

            console.log('DEMO LOGIN:', data);

            if (data.access_token) {
                localStorage.setItem('jwt_token', data.access_token);
                await refreshUser();
                // Route by role
                const role = data.user?.role || 'hod';
                switch (role) {
                    case 'hod': navigate('/hod-dashboard'); break;
                    case 'tt_coordinator': navigate('/dashboard'); break;
                    default: navigate('/faculty-dashboard'); break;
                }
            } else {
                setError('No token received from server');
            }
        } catch (err) {
            console.error('Demo login error:', err);
            setError('Demo unavailable — try again');
        } finally {
            setLoading('');
        }
    };

    const isBackendReady = backendStatus === 'online';

    return (
        <div style={{
            minHeight: '100vh',
            background: '#ffffff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
        }}>
            {/* Wake-up banner */}
            {backendStatus === 'waking' && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    background: '#fef3c7',
                    borderBottom: '1px solid #fde68a',
                    padding: '12px 20px',
                    textAlign: 'center',
                    fontSize: '14px',
                    color: '#92400e',
                    zIndex: 1000,
                    animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                }}>
                    <style>{`
                        @keyframes pulse {
                            0%, 100% { opacity: 1; }
                            50% { opacity: 0.8; }
                        }
                    `}</style>
                    ⏳ Backend waking up — free tier cold start (~30 sec). Please wait...
                </div>
            )}

            <div style={{
                width: '340px',
                textAlign: 'center',
            }}>
                {/* Logo */}
                <div style={{
                    width: '56px',
                    height: '56px',
                    background: 'linear-gradient(135deg, #1d4ed8, #7c3aed)',
                    borderRadius: '14px',
                    margin: '0 auto 24px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}>
                    <span style={{
                        color: 'white',
                        fontWeight: '700',
                        fontSize: '18px'
                    }}>F</span>
                </div>

                <h1 style={{
                    fontSize: '22px',
                    fontWeight: '600',
                    color: '#111827',
                    margin: '0 0 6px',
                    letterSpacing: '-0.3px'
                }}>FWMS</h1>

                <p style={{
                    fontSize: '13px',
                    color: '#6b7280',
                    margin: '0 0 4px'
                }}>Hindustan Institute of Technology and Science</p>

                <p style={{
                    fontSize: '12px',
                    color: '#9ca3af',
                    margin: '0 0 36px'
                }}>Department of Computer Applications</p>

                {/* Error message */}
                {error && (
                    <div style={{
                        background: '#fef2f2',
                        border: '1px solid #fecaca',
                        borderRadius: '10px',
                        padding: '10px 14px',
                        marginBottom: '16px',
                        fontSize: '13px',
                        color: '#dc2626'
                    }}>
                        {error}
                    </div>
                )}

                {/* Google Sign In Button */}
                <button
                    onClick={handleGoogleLogin}
                    disabled={!!loading || !isBackendReady}
                    style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '10px',
                        padding: '11px 20px',
                        background: 'white',
                        border: '1px solid #d1d5db',
                        borderRadius: '10px',
                        fontSize: '14px',
                        fontWeight: '500',
                        color: '#374151',
                        cursor: (loading || !isBackendReady) ? 'not-allowed' : 'pointer',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                        opacity: !isBackendReady ? 0.6 : 1,
                    }}
                >
                    <img src="https://www.google.com/favicon.ico" width="16" height="16" alt="Google" />
                    {!isBackendReady ? 'Connecting...' : (loading === 'google' ? 'Signing in...' : 'Sign in with Google')}
                </button>

                <p style={{
                    fontSize: '11px',
                    color: '#d1d5db',
                    marginTop: '20px'
                }}>@hindustanuniv.ac.in accounts only</p>

                {/* Demo Login Button */}
                <div style={{ marginTop: '24px' }}>
                    <button
                        onClick={handleDemoLogin}
                        disabled={!!loading || !isBackendReady}
                        style={{
                            width: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '10px',
                            padding: '11px 20px',
                            background: 'white',
                            border: '1px solid #e5e7eb',
                            borderRadius: '10px',
                            fontSize: '14px',
                            fontWeight: '500',
                            color: '#6b7280',
                            cursor: (loading || !isBackendReady) ? 'not-allowed' : 'pointer',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                            opacity: !isBackendReady ? 0.6 : 1,
                        }}
                    >
                        <Rocket size={16} />
                        {!isBackendReady ? 'Connecting...' : (loading === 'demo' ? 'Loading demo...' : 'Try Demo — No login required')}
                    </button>

                    <p style={{
                        fontSize: '11px',
                        color: '#9ca3af',
                        marginTop: '8px',
                        fontStyle: 'italic'
                    }}>
                        Full HOD access • <a 
                            href="https://github.com/Nithish-kumar-git/fwms-workload-system" 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{ color: '#6b7280', textDecoration: 'underline' }}
                        >Read the code on GitHub</a>
                    </p>
                </div>

                {/* Dev mode section */}
                {import.meta.env.VITE_DEV_MODE === 'true' && (
                    <div style={{
                        marginTop: '32px',
                        paddingTop: '24px',
                        borderTop: '1px solid #e5e7eb',
                    }}>
                        <p style={{
                            fontSize: '11px',
                            color: '#9ca3af',
                            marginBottom: '12px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                        }}>
                            Development Mode
                        </p>

                        <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                                onClick={() => handleDevLogin(16, 'hod')}
                                disabled={!!loading}
                                style={{
                                    flex: 1,
                                    padding: '8px',
                                    background: 'white',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px',
                                    color: '#374151',
                                    fontSize: '12px',
                                    fontWeight: 500,
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '4px',
                                }}
                            >
                                <Crown size={14} />
                                {loading === 'hod' ? '…' : 'HOD'}
                            </button>

                            <button
                                onClick={() => handleDevLogin(22, 'coordinator')}
                                disabled={!!loading}
                                style={{
                                    flex: 1,
                                    padding: '8px',
                                    background: 'white',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px',
                                    color: '#374151',
                                    fontSize: '12px',
                                    fontWeight: 500,
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '4px',
                                }}
                            >
                                <Shield size={14} />
                                {loading === 'coordinator' ? '…' : 'Coordinator'}
                            </button>

                            <button
                                onClick={() => handleDevLogin(17, 'faculty')}
                                disabled={!!loading}
                                style={{
                                    flex: 1,
                                    padding: '8px',
                                    background: 'white',
                                    border: '1px solid #e5e7eb',
                                    borderRadius: '8px',
                                    color: '#374151',
                                    fontSize: '12px',
                                    fontWeight: 500,
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '4px',
                                }}
                            >
                                <User size={14} />
                                {loading === 'faculty' ? '…' : 'Faculty'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
