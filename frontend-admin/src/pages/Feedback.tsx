import { useEffect, useState } from 'react';
import { Button, Card, Input, Select, InfoTip } from '../components/ui';
import { useLang } from '../i18n';
import { analyzeFeedback, createFeedback, getFeedback, type Feedback } from '../services/queries';

export default function FeedbackPage() {
  const [items, setItems] = useState<Feedback[]>([]);
  const [targetType, setTargetType] = useState('draft_site');
  const [quickRating, setQuickRating] = useState('needs_improvement');
  const [openFeedback, setOpenFeedback] = useState('');
  const { t } = useLang();

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
      <h2>{t('feedback_intelligence')} <InfoTip text="רשום פידבק על דראפטים, הודעות, דוחות — AI מנתח ומציע פעולות שיפור" /></h2>
      <p className="muted">{t('feedback_subtitle')}</p>
      <Card>
        <div className="grid-two">
          <div>
            <label>{t('target_type')}</label>
            <Select value={targetType} onChange={(e) => setTargetType(e.target.value)}>
              <option value="draft_site">{t('draft_site')}</option>
              <option value="outreach_message">{t('outreach_message')}</option>
              <option value="ceo_report">{t('ceo_report')}</option>
              <option value="recommendation">{t('recommendation')}</option>
              <option value="system_general">{t('system_general')}</option>
            </Select>
          </div>
          <div>
            <label>{t('quick_feedback')}</label>
            <Select value={quickRating} onChange={(e) => setQuickRating(e.target.value)}>
              <option value="good_as_is">{t('good_as_is')}</option>
              <option value="needs_improvement">{t('needs_improvement')}</option>
              <option value="not_a_fit">{t('not_a_fit')}</option>
            </Select>
          </div>
        </div>
        <label>{t('open_feedback')}</label>
        <Input value={openFeedback} onChange={(e) => setOpenFeedback(e.target.value)} placeholder={t('open_feedback_ph')} />
        <div style={{ marginTop: 12 }}><Button onClick={submit}>{t('submit_feedback')}</Button></div>
      </Card>

      <div className="list-grid">
        {items.map((item) => (
          <Card key={item.id}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
              <strong>{item.target_type} #{item.id}</strong>
              <span className="badge">{item.quick_rating}</span>
            </div>
            <p>{item.open_feedback || '—'}</p>
            <p className="muted">{t('status_label')}: {item.feedback_status} · {t('category')}: {item.analysis_category || '—'} · {t('scope_label')}: {item.suggested_scope || '—'}</p>
            {item.ceo_response ? <div className="card subtle"><strong>{t('ceo_response')}:</strong><p>{item.ceo_response}</p></div> : null}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <Button onClick={() => analyze(item.id)}>{t('analyze')}</Button>
              {item.action_hint ? <span className="badge">{item.action_hint}</span> : null}
              {item.preference_candidate ? <span className="badge accent">{t('preference_candidate')}</span> : null}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
