import { useEffect, useState } from 'react';
import { Card, SectionTitle } from '../components/ui';
import { Customer, getCustomers } from '../services/queries';

export default function CustomersPage() {
    const [items, setItems] = useState<Customer[]>([]);
    const load = () => getCustomers().then(setItems).catch(console.error);
    useEffect(() => { load(); }, []);

    return (
        <Card>
            <SectionTitle>Customers</SectionTitle>
            <div className="table-list">
                {items.map(c => (
                    <div key={c.id}>
                        <strong>{c.contact_name || c.email || c.phone || `Customer #${c.id}`}</strong>
                        <div className="muted">
                            id {c.id} · {c.phone || '—'} · {c.email || '—'} · pkg {c.package_name || '—'}
                            {' · '}{c.is_active ? 'active' : 'inactive'}
                            {c.must_change_password && ' · must change password'}
                        </div>
                        <div className="muted" style={{ fontSize: 12 }}>
                            business_id {c.business_id ?? '—'} · draft_site_id {c.draft_site_id ?? '—'} · active_site_id {c.active_site_id ?? '—'}
                        </div>
                    </div>
                ))}
                {items.length === 0 && <p className="muted">No customers found.</p>}
            </div>
        </Card>
    );
}
