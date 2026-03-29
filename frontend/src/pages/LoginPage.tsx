import { useNavigate } from 'react-router-dom';
import { AlertCircle, Shield, User, Crown } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
    const navigate = useNavigate();
    const [error, setError] = useState('');
    const [loading, setLoading] = useState('');
    const { refreshUser } = useAuth();

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

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: "'Inter', sans-serif"
        }}>
            <div style={{
                background: 'rgba(255,255,255,0.05)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '24px',
                padding: '48px 40px',
                width: '100%',
                maxWidth: '420px',
                textAlign: 'center',
                boxShadow: '0 25px 50px rgba(0,0,0,0.4)'
            }}>
                {/* Logo / Title */}
                <div style={{ marginBottom: '8px' }}>
                    <span style={{
                        fontSize: '32px',
                        fontWeight: '800',
                        background: 'linear-gradient(90deg, #60a5fa, #a78bfa)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent'
                    }}>
                        FWMS
                    </span>
                </div>
                
                <p style={{
                    color: '#94a3b8',
                    fontSize: '13px',
                    marginBottom: '4px',
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase'
                }}>
                    Hindustan Institute of Technology and Science
                </p>
                
                <p style={{
                    color: '#64748b',
                    fontSize: '12px',
                    marginBottom: '40px'
                }}>
                    Department of Computer Applications
                </p>
                
                <div style={{
                    width: '48px',
                    height: '2px',
                    background: 'linear-gradient(90deg, #60a5fa, #a78bfa)',
                    margin: '0 auto 32px'
                }} />
                
                <p style={{
                    color: '#cbd5e1',
                    fontSize: '15px',
                    marginBottom: '28px',
                    fontWeight: '500'
                }}>
                    Faculty Workload Management System
                </p>

                {error && (
                    <div style={{
                        padding: '12px',
                        marginBottom: '20px',
                        borderRadius: '8px',
                        background: 'rgba(239, 68, 68, 0.15)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        color: '#fca5a5',
                        fontSize: '13px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        textAlign: 'left',
                    }}>
                        <AlertCircle size={16} style={{ flexShrink: 0 }} />
                        {error}
                    </div>
                )}

                {/* Google Sign In button - OAuth logic untouched */}
                <div style={{
                    background: 'white',
                    borderRadius: '12px',
                    padding: '2px',
                    boxShadow: '0 4px 15px rgba(96,165,250,0.2)'
                }}>
                    <button
                        onClick={handleGoogleLogin}
                        disabled={!!loading}
                        style={{
                            width: '100%',
                            padding: '14px',
                            background: 'white',
                            border: 'none',
                            borderRadius: '10px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '12px',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            fontSize: '15px',
                            fontWeight: 600,
                            color: '#1f2937',
                            transition: 'all 0.2s',
                        }}
                        onMouseEnter={(e) => {
                            if (!loading) {
                                e.currentTarget.style.background = '#f9fafb';
                            }
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'white';
                        }}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        {loading === 'google' ? 'Signing in...' : 'Sign in with Google'}
                    </button>
                </div>

                <p style={{
                    color: '#475569',
                    fontSize: '11px',
                    marginTop: '24px'
                }}>
                    Sign in with your @hindustanuniv.ac.in account
                </p>

                {/* Dev mode section - conditionally rendered */}
                {import.meta.env.VITE_DEV_MODE === 'true' && (
                    <div style={{
                        marginTop: '32px',
                        paddingTop: '24px',
                        borderTop: '1px solid rgba(255,255,255,0.1)',
                    }}>
                        <p style={{
                            fontSize: '11px',
                            color: '#64748b',
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
                                    background: 'rgba(255,255,255,0.1)',
                                    border: '1px solid rgba(255,255,255,0.2)',
                                    borderRadius: '8px',
                                    color: '#cbd5e1',
                                    fontSize: '12px',
                                    fontWeight: 500,
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '4px',
                                    transition: 'all 0.2s'
                                }}
                                onMouseEnter={(e) => {
                                    if (!loading) {
                                        e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
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
                                    background: 'rgba(255,255,255,0.1)',
                                    border: '1px solid rgba(255,255,255,0.2)',
                                    borderRadius: '8px',
                                    color: '#cbd5e1',
                                    fontSize: '12px',
                                    fontWeight: 500,
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '4px',
                                    transition: 'all 0.2s'
                                }}
                                onMouseEnter={(e) => {
                                    if (!loading) {
                                        e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
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
                                    background: 'rgba(255,255,255,0.1)',
                                    border: '1px solid rgba(255,255,255,0.2)',
                                    borderRadius: '8px',
                                    color: '#cbd5e1',
                                    fontSize: '12px',
                                    fontWeight: 500,
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '4px',
                                    transition: 'all 0.2s'
                                }}
                                onMouseEnter={(e) => {
                                    if (!loading) {
                                        e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
                                    }
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
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
