import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, SectionTitle } from '../components/ui';
import { ensureDevLogin } from '../services/queries';

export default function LoginPage() {
    const navigate = useNavigate();
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleDevLogin = async () => {
        setLoading(true);
        setError('');
        try {
            await ensureDevLogin();
            navigate('/', { replace: true });
        } catch {
            setError('Login failed. Check that the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
            <div style={{ minWidth: 320 }}>
            <Card>
                <SectionTitle>LocalBiz Admin v27</SectionTitle>
                <p className="muted" style={{ marginBottom: 24 }}>Sign in to access the admin control room.</p>
                {error && <p style={{ color: '#c00', marginBottom: 12 }}>{error}</p>}
                <Button onClick={handleDevLogin} disabled={loading}>
                    {loading ? 'Signing in…' : 'Dev Login'}
                </Button>
            </Card>
            </div>
        </div>
    );
}
