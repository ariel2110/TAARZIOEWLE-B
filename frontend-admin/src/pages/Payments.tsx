import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle } from '../components/ui';
import { Payment, getPayments, confirmPayment, movePaymentToActivation } from '../services/queries';

export default function PaymentsPage() {
    const [items, setItems] = useState<Payment[]>([]);
    const load = () => getPayments().then(setItems).catch(console.error);
    useEffect(() => { load(); }, []);

    return (
        <Card>
            <SectionTitle>Payments</SectionTitle>
            <div className="table-list">
                {items.map(p => (
                    <div key={p.id}>
                        <strong>Payment #{p.id}</strong>
                        <div className="muted">
                            business_id {p.business_id ?? '—'} · ₪{p.amount} · {p.internal_status}
                        </div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                            {p.internal_status === 'pending' && (
                                <Button onClick={() => confirmPayment(p.id).then(load)}>Confirm payment</Button>
                            )}
                            {(p.internal_status === 'confirmed' || p.internal_status === 'pending') && (
                                <Button onClick={() => movePaymentToActivation(p.id).then(load)}>Move to activation</Button>
                            )}
                        </div>
                    </div>
                ))}
                {items.length === 0 && <p className="muted">No payments found.</p>}
            </div>
        </Card>
    );
}
