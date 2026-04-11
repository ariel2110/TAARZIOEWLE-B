import { useEffect, useState } from 'react';
import { Button, Card, Input, Select } from '../components/ui';
import { analyzeFeedback, createFeedback, getFeedback, type Feedback } from '../services/queries';

export default function FeedbackPage() {
  const [items, setItems] = useState<Feedback[]>([]);
  const [targetType, setTargetType] = useState('draft_site');
  const [quickRating, setQuickRating] = useState('needs_improvement');
  const [openFeedback, setOpenFeedback] = useState('');

  const load = () => getFeedback().then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);

  async function submit() {
    await createFeedback({ target_type: targetType, quick_rating: quickRating, open_feedback: openFeedback || null });
    setOpenFeedback('');
    load();
  }

  async function analyze(id: number) {
    await analyzeFeedback(id);
    load();
  }

  return (
    <div>
      <h2>Feedback Intelligence</h2>
      <p className="muted">Quick feedback + open feedback + CEO interpretation.</p>
      <Card>
        <div className="grid-two">
          <div>
            <label>Target type</label>
            <Select value={targetType} onChange={(e) => setTargetType(e.target.value)}>
              <option value="draft_site">Draft site</option>
              <option value="outreach_message">Outreach message</option>
              <option value="ceo_report">CEO report</option>
              <option value="recommendation">Recommendation</option>
              <option value="system_general">System general</option>
            </Select>
          </div>
          <div>
            <label>Quick feedback</label>
            <Select value={quickRating} onChange={(e) => setQuickRating(e.target.value)}>
              <option value="good_as_is">Good as-is</option>
              <option value="needs_improvement">Needs improvement</option>
              <option value="not_a_fit">Not a fit</option>
            </Select>
          </div>
        </div>
        <label>Open feedback</label>
        <Input value={openFeedback} onChange={(e) => setOpenFeedback(e.target.value)} placeholder="Write freely: what should improve, change, or be remembered next time?" />
        <div style={{ marginTop: 12 }}><Button onClick={submit}>Submit feedback</Button></div>
      </Card>

      <div className="list-grid">
        {items.map((item) => (
          <Card key={item.id}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
              <strong>{item.target_type} #{item.id}</strong>
              <span className="badge">{item.quick_rating}</span>
            </div>
            <p>{item.open_feedback || '—'}</p>
            <p className="muted">Status: {item.feedback_status} · Category: {item.analysis_category || '—'} · Scope: {item.suggested_scope || '—'}</p>
            {item.ceo_response ? <div className="card subtle"><strong>CEO response:</strong><p>{item.ceo_response}</p></div> : null}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <Button onClick={() => analyze(item.id)}>Analyze</Button>
              {item.action_hint ? <span className="badge">{item.action_hint}</span> : null}
              {item.preference_candidate ? <span className="badge accent">Preference candidate</span> : null}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
