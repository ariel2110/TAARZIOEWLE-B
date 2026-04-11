import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { Card, SectionTitle } from '../components/ui';
import { googleLogin } from '../services/queries';

export default function LoginPage() {
    const navigate = useNavigate();
    const [error, setError] = useState('');

    const handleSuccess = async (credentialResponse: { credential?: string }) => {
        if (!credentialResponse.credential) { setError('לא התקבל טוקן מGoogle'); return; }
        try {
            await googleLogin(credentialResponse.credential);
            navigate('/', { replace: true });
        } catch {
            setError('הכניסה נכשלה. ודא שהמייל שלך מורשה.');
        }
    };

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
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <GoogleLogin
                            onSuccess={handleSuccess}
                            onError={() => setError('Google login נכשל. נסה שוב.')}
                            useOneTap
                        />
                    </div>
                </Card>
            </div>
        </div>
    );
}
