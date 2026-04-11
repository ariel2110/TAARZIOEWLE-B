
import { useEffect, useState } from 'react';
import { Button, Card, SectionTitle, InfoTip } from '../components/ui';
import { useLang } from '../i18n';
import { Approval, ApprovalDetail, getApprovals, getApprovalDetail, approve, reject, applyApproval, createCeoTask } from '../services/queries';

export default function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([]);
  const [selected, setSelected] = useState<ApprovalDetail | null>(null);
  const [execMsg, setExecMsg] = useState<string | null>(null);
  const { t } = useLang();
  const load = () => getApprovals().then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);
  async function openDetail(id: number) { setSelected(await getApprovalDetail(id)); }

  async function handleExecute(id: number) {
    setExecMsg(null);
    try {
      const res = await applyApproval(id);
      setExecMsg(res.execution?.message ?? '✅ בוצע');
    } catch (e: unknown) {
      setExecMsg('שגיאה בביצוע: ' + (e instanceof Error ? e.message : String(e)));
    }
    load();
  }

  return (
    <div className="two-col">
      <Card>
        <SectionTitle>{t('approval_queue')} <InfoTip text="שינויים המחכים לאישור אריאל לפני ביצוע — כולל שינויי תבניות, קמפיינים והפעלות AI" /></SectionTitle>
        {execMsg && (
          <div style={{ padding: '10px 14px', marginBottom: 12, background: execMsg.startsWith('שגיאה') ? '#fdecea' : '#e6f9ee', borderRadius: 6, fontSize: 14, whiteSpace: 'pre-wrap' }}>
            {execMsg}
          </div>
        )}
        <div className="table-list">
          {items.map(a => (
            <div key={a.id}>
              <strong>{a.title}</strong>
              <div className="muted">{a.approval_type} · {a.status}</div>
              {a.summary && <div style={{ margin: '6px 0' }}>{a.summary}</div>}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <Button onClick={() => openDetail(a.id)}>{t('open_detail')}</Button>
                {a.status !== 'applied' && a.status !== 'rejected' && (
                  <Button onClick={() => approve(a.id).then(load)}>{t('approve')}</Button>
                )}
                {a.status === 'approved' && (
                  <Button
                    style={{ background: '#1a7f4b', color: '#fff' }}
                    onClick={() => handleExecute(a.id)}
                  >
                    {t('execute')}
                  </Button>
                )}
                {a.status !== 'applied' && a.status !== 'rejected' && (
                  <Button onClick={() => reject(a.id).then(load)}>{t('reject')}</Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <SectionTitle>{t('approval_detail')}</SectionTitle>
        {selected ? (
          <div className="table-list">
            <div><strong>{selected.title}</strong><div className="muted">{selected.approval_type} · {selected.status} · {t('confidence')} {selected.confidence_score ?? '—'}</div></div>
            <div><strong>{t('why')}</strong><p>{selected.rationale || selected.summary || '—'}</p></div>
            <div><strong>{t('evidence')}</strong><pre>{JSON.stringify(selected.evidence_json || {}, null, 2)}</pre></div>
            <div className="grid-two">
              <div><strong>{t('before')}</strong><pre>{JSON.stringify(selected.before_json || {}, null, 2)}</pre></div>
              <div><strong>{t('after')}</strong><pre>{JSON.stringify(selected.after_json || {}, null, 2)}</pre></div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {selected.status !== 'applied' && selected.status !== 'rejected' && (
                <Button onClick={() => approve(selected.id).then(load)}>{t('approve')}</Button>
              )}
              {selected.status === 'approved' && (
                <Button
                  style={{ background: '#1a7f4b', color: '#fff' }}
                  onClick={() => handleExecute(selected.id)}
                >
                  {t('execute')}
                </Button>
              )}
              {selected.status !== 'applied' && selected.status !== 'rejected' && (
                <Button onClick={() => reject(selected.id).then(load)}>{t('reject')}</Button>
              )}
              <Button onClick={() => createCeoTask('approval_detail', `Review rollout for ${selected.title}`, 'Approval detail created a CEO follow-up task')}>{t('create_ceo_task')}</Button>
            </div>
          </div>
        ) : <p className="muted">{t('select_approval')}</p>}
      </Card>
    </div>
  );
}
