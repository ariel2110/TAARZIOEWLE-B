import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { Card, SectionTitle } from '../components/ui';
import { googleLogin, ensureDevLogin } from '../services/queries';

export default function LoginPage() {
    const navigate = useNavigate();
    const [error, setError] = useState('');
    const [autoLogging, setAutoLogging] = useState(false);

    // Auto-login with dev token if configured (admin-only deployment)
    useEffect(() => {
        const devToken = import.meta.env.VITE_ADMIN_DEV_TOKEN;
        if (!devToken) return;
        setAutoLogging(true);
        ensureDevLogin()
            .then(() => {
                if (localStorage.getItem('admin_access_token')) {
                    navigate('/', { replace: true });
                } else {
                    setAutoLogging(false);
                }
            })
            .catch(() => setAutoLogging(false));
    }, [navigate]);

    const handleSuccess = async (credentialResponse: { credential?: string }) => {
        if (!credentialResponse.credential) { setError('לא התקבל טוקן מGoogle'); return; }
        try {
            await googleLogin(credentialResponse.credential);
            navigate('/', { replace: true });
        } catch {
            setError('הכניסה נכשלה. ודא שהמייל שלך מורשה.');
        }
    };

    const handleDevLogin = async () => {
        setAutoLogging(true);
        setError('');
        try {
            await ensureDevLogin();
            if (localStorage.getItem('admin_access_token')) {
                navigate('/', { replace: true });
            } else {
                setError('כניסה נכשלה — בדוק את ה-token ב-.env');
            }
        } catch {
            setError('כניסה ישירה נכשלה.');
        } finally {
            setAutoLogging(false);
        }
    };

    if (autoLogging) {
        return (
            <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f4f8' }}>
                <Card>
                    <div style={{ textAlign: 'center', padding: 32 }}>
                        <div style={{ fontSize: 32, marginBottom: 12 }}>⏳</div>
                        <p style={{ color: '#6366f1', fontWeight: 600 }}>מתחבר…</p>
                    </div>
                </Card>
            </div>
        );
    }

    return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f4f8' }}>
            <div style={{ minWidth: 340 }}>
                <Card>
                    <div style={{ textAlign: 'center', marginBottom: 24 }}>
                        <div style={{ fontSize: 40 }}>🏢</div>
                        <SectionTitle>SiteNest Admin</SectionTitle>
                        <p style={{ color: '#666', marginTop: 4 }}>כניסה לממשק ניהול</p>
                    </div>
                    {error && <p style={{ color: '#c00', marginBottom: 16, textAlign: 'center' }}>{error}</p>}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, alignItems: 'center' }}>
                        <GoogleLogin
                            onSuccess={handleSuccess}
                            onError={() => setError('Google login נכשל. נסה שוב.')}
                            useOneTap
                        />
                        {import.meta.env.VITE_ADMIN_DEV_TOKEN && (
                            <button
                                onClick={handleDevLogin}
                                style={{
                                    background: '#6366f1', color: '#fff', border: 'none', borderRadius: 8,
                                    padding: '10px 24px', fontWeight: 600, fontSize: 14, cursor: 'pointer', width: '100%',
                                }}
                            >
                                ⚡ כניסה ישירה (Ariel)
                            </button>
                        )}
                    </div>
                </Card>
            </div>
        </div>
    );
}
