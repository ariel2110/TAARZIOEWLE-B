
import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle, InfoTip } from '../components/ui';
import { useLang } from '../i18n';
import { QueueSummary, QueueItem, getQueueSummary, getQueueItems, runQueueAction } from '../services/queries';

export default function QueuesPage() {
  const [summary, setSummary] = useState<QueueSummary[]>([]);
  const [selected, setSelected] = useState<string>('lead_review');
  const [items, setItems] = useState<QueueItem[]>([]);
  const [result, setResult] = useState('');
  const { t } = useLang();
  useEffect(() => { getQueueSummary().then(setSummary).catch(console.error); }, []);
  const loadItems = () => getQueueItems(selected).then(setItems).catch(console.error);
  useEffect(() => { loadItems(); }, [selected]);
  async function doAction(item: QueueItem, action: string) {
    await runQueueAction(selected, item.id, action);
    setResult(`פעולה "${action}" בוצעה עבור: ${item.title}`);
    loadItems();
    getQueueSummary().then(setSummary).catch(console.error);
  }
  return (
    <div className="two-col">
      <Card>
        <SectionTitle>{t('queue_summary')} <InfoTip text="ריכוז כל הפריטים הממתינים לפעולה — לחץ 'פתח' כדי לראות ולפעול" /></SectionTitle>
        <div className="table-list">
          {summary.map(q => (
            <div key={q.queue_type} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <strong>{q.label}</strong>
                <div className="muted">{q.queue_type}</div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <strong>{q.count}</strong>
                <Button onClick={() => setSelected(q.queue_type)}>{t('open')}</Button>
              </div>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <SectionTitle>{t('queue_items')} · {selected}</SectionTitle>
        {result ? <div className="card subtle"><p>{result}</p></div> : null}
        <div className="table-list">
          {items.map(i => (
            <div key={i.id}>
              <strong>{i.title}</strong>
              <div className="muted">{i.subtitle || '—'} · {t('priority_label')} {i.priority}</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {(i.available_actions || []).map(action => (
                  <Button key={action} onClick={() => doAction(i, action)}>{action}</Button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
