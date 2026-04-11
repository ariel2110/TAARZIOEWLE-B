
import { useEffect, useState } from 'react';
import { Button, Card, Input, SectionTitle } from '../components/ui';
import { Digest, Health, QueueSummary, getDigest, getHealth, getQueueSummary, createCeoTask, addCeoDecisionNote } from '../services/queries';

export default function CEOConsolePage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [queues, setQueues] = useState<QueueSummary[]>([]);
  const [note, setNote] = useState('');
  const [result, setResult] = useState('');
  useEffect(() => {
    Promise.all([getDigest(), getHealth(), getQueueSummary()]).then(([d, h, q]) => { setDigest(d); setHealth(h); setQueues(q); }).catch(console.error);
  }, []);
  return (
    <div className="grid">
      <Card dark>
        <SectionTitle>CEO Console</SectionTitle>
        <p>{digest?.executive_summary}</p>
        <h3>Recommended Actions</h3>
        <ul>{digest?.recommended_actions?.map(x => <li key={x}>{x}</li>)}</ul>
        <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
          <Button onClick={() => createCeoTask('ceo_console', 'Work outreach-ready queue', 'Generated from CEO console').then((x:any) => setResult(JSON.stringify(x)))}>Make outreach task</Button>
          <Button onClick={() => createCeoTask('ceo_console', 'Review approval queue', 'Generated from CEO console').then((x:any) => setResult(JSON.stringify(x)))}>Make approval task</Button>
        </div>
      </Card>
      {result ? <Card><SectionTitle>Last CEO Action</SectionTitle><p>{result}</p></Card> : null}
      <div className="two-col">
        <Card>
          <SectionTitle>System Health</SectionTitle>
          <p><strong>Status:</strong> {health?.overall_status || health?.status}</p>
          <ul>{health?.drivers?.map(x => <li key={x}>{x}</li>)}</ul>
          <p><strong>Pressure notes</strong></p>
          <ul>{digest?.pressure_notes?.map(x => <li key={x}>{x}</li>)}</ul>
        </Card>
        <Card>
          <SectionTitle>Queue Pressure</SectionTitle>
          <div className="table-list">
            {queues.map(q => <div key={q.queue_type}><strong>{q.label}</strong><div className="muted">{q.count} items</div></div>)}
          </div>
        </Card>
      </div>
      <Card>
        <SectionTitle>Decision Notes</SectionTitle>
        <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Write a free-form decision, preference, or instruction for the CEO layer" />
        <div style={{ marginTop: 8 }}><Button onClick={() => addCeoDecisionNote(note).then((x:any) => setResult(JSON.stringify(x)))}>Add note</Button></div>
      </Card>
    </div>
  );
}
