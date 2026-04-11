
import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle } from '../components/ui';
import { Approval, ApprovalDetail, getApprovals, getApprovalDetail, approve, reject, createCeoTask } from '../services/queries';

export default function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([]);
  const [selected, setSelected] = useState<ApprovalDetail | null>(null);
  const load = () => getApprovals().then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);
  async function openDetail(id: number) { setSelected(await getApprovalDetail(id)); }
  return (
    <div className="two-col">
      <Card>
        <SectionTitle>Approval Queue</SectionTitle>
        <div className="table-list">
          {items.map(a => (
            <div key={a.id}>
              <strong>{a.title}</strong>
              <div className="muted">{a.approval_type} · {a.status}</div>
              {a.summary && <div style={{ margin:'6px 0' }}>{a.summary}</div>}
              <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
                <Button onClick={() => openDetail(a.id)}>Open detail</Button>
                <Button onClick={() => approve(a.id).then(load)}>Approve</Button>
                <Button onClick={() => reject(a.id).then(load)}>Reject</Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <SectionTitle>Approval Detail</SectionTitle>
        {selected ? (
          <div className="table-list">
            <div><strong>{selected.title}</strong><div className="muted">{selected.approval_type} · {selected.status} · confidence {selected.confidence_score ?? '—'}</div></div>
            <div><strong>Why</strong><p>{selected.rationale || selected.summary || '—'}</p></div>
            <div><strong>Evidence</strong><pre>{JSON.stringify(selected.evidence_json || {}, null, 2)}</pre></div>
            <div className="grid-two">
              <div><strong>Before</strong><pre>{JSON.stringify(selected.before_json || {}, null, 2)}</pre></div>
              <div><strong>After</strong><pre>{JSON.stringify(selected.after_json || {}, null, 2)}</pre></div>
            </div>
            <div style={{ display:'flex', gap:8 }}>
              <Button onClick={() => approve(selected.id).then(load)}>Approve</Button>
              <Button onClick={() => reject(selected.id).then(load)}>Reject</Button>
              <Button onClick={() => createCeoTask('approval_detail', `Review rollout for ${selected.title}`, 'Approval detail created a CEO follow-up task')}>Create CEO task</Button>
            </div>
          </div>
        ) : <p className="muted">Select an approval item to inspect before/after, rationale, evidence, and confidence.</p>}
      </Card>
    </div>
  );
}
