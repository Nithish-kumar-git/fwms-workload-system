import { useNavigate } from 'react-router-dom';
import { BookOpen, AlertCircle } from 'lucide-react';
import { useState } from 'react';

export default function LoginPage() {
    const navigate = useNavigate();
    const [error, setError] = useState('');
    const [loading, setLoading] = useState('');

    const handleGoogleLogin = async () => {
        setError('');
        setLoading('google');
        try {
            const res = await fetch('/api/auth/login');
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

    const handleDevLogin = async () => {
        setError('');
        setLoading('dev');
        try {
            const res = await fetch('/api/auth/dev-login', { method: 'POST' });
            const data = await res.json();
            if (!res.ok) {
                setError(data.detail || `Dev login failed (${res.status})`);
                return;
            }
            if (data.token) {
                localStorage.setItem('jwt_token', data.token);
                navigate('/dashboard');
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
            minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
        }}>
            <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', maxWidth: '420px', width: '100%' }}>
                <div style={{
                    width: '4rem', height: '4rem', borderRadius: '1rem',
                    background: 'var(--gradient-accent)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 1.5rem',
                    boxShadow: '0 0 30px rgba(124, 58, 237, 0.3)',
                }}>
                    <BookOpen size={28} color="white" />
                </div>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.5rem' }}>
                    Faculty Workload
                </h1>
                <p style={{ color: 'var(--color-text-muted)', marginBottom: '2rem', fontSize: '0.875rem' }}>
                    Management System
                </p>

                {error && (
                    <div style={{
                        padding: '0.75rem', marginBottom: '1rem', borderRadius: 'var(--radius)',
                        background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', fontSize: '0.8125rem',
                        display: 'flex', alignItems: 'center', gap: '0.5rem', textAlign: 'left',
                    }}>
                        <AlertCircle size={16} style={{ flexShrink: 0 }} />
                        {error}
                    </div>
                )}

                <button
                    onClick={handleGoogleLogin}
                    className="btn btn-primary"
                    disabled={!!loading}
                    style={{ width: '100%', justifyContent: 'center', padding: '0.75rem', marginBottom: '0.75rem' }}
                >
                    {loading === 'google' ? 'Redirecting...' : 'Sign in with Google'}
                </button>

                <button
                    onClick={handleDevLogin}
                    className="btn btn-outline"
                    disabled={!!loading}
                    style={{ width: '100%', justifyContent: 'center', padding: '0.75rem' }}
                >
                    {loading === 'dev' ? 'Logging in...' : 'Dev Mode (Local Only)'}
                </button>

                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem', marginTop: '1.5rem' }}>
                    Dev Mode uses DEV_AUTH_BYPASS — disabled in production
                </p>
            </div>
        </div>
    );
}
