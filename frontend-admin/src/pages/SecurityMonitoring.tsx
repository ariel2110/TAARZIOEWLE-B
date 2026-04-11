import { useEffect, useState } from 'react';
import { Card, SectionTitle, InfoTip } from '../components/ui';
import { useLang } from '../i18n';
import { getSecuritySummary, getSecurityTimeline, getSuspicion, SecuritySummary, SecurityTimelineItem, SuspicionItem } from '../services/queries';

export default function SecurityMonitoring(){
  const [summary, setSummary] = useState<SecuritySummary | null>(null);
  const [timeline, setTimeline] = useState<SecurityTimelineItem[]>([]);
  const [suspicion, setSuspicion] = useState<SuspicionItem[]>([]);
  const { t } = useLang();
  useEffect(() => {
    Promise.all([getSecuritySummary(), getSecurityTimeline(), getSuspicion()]).then(([s,tl,sp]) => {
      setSummary(s); setTimeline(tl.items || []); setSuspicion(sp.items || []);
    }).catch(console.error);
  }, []);
  return <div className="grid">
    <SectionTitle>{t('security_monitoring')} <InfoTip text="יומן פעילות, כשלות כניסה, חסימות IP ורשימת חשד לפי סיכון" /></SectionTitle>
    <div className="cards">
      <Card><div className="muted">{t('overall')}</div><div style={{fontSize:24,fontWeight:700}}>{summary?.overall_status || t('unknown_status')}</div></Card>
      <Card><div className="muted">{t('login_failures')}</div><div style={{fontSize:24,fontWeight:700}}>{summary?.login_failures || 0}</div></Card>
      <Card><div className="muted">{t('blocked_logins')}</div><div style={{fontSize:24,fontWeight:700}}>{summary?.blocked_logins || 0}</div></Card>
      <Card><div className="muted">{t('rate_limited')}</div><div style={{fontSize:24,fontWeight:700}}>{summary?.rate_limited_events || 0}</div></Card>
    </div>
    <div className="two-col">
      <Card>
        <SectionTitle>{t('suspicion_watchlist')}</SectionTitle>
        <div className="table-list">
          {suspicion.slice(0,10).map(item => <div key={item.customer_phone}><strong>{item.customer_phone}</strong><div className="muted">{t('score_label')} {item.suspicion_score} · {item.suspicion_tier} · {t('failures_label')} {item.login_failures} · {t('blocked_label')} {item.blocked_logins}</div></div>)}
        </div>
      </Card>
      <Card>
        <SectionTitle>{t('security_timeline')}</SectionTitle>
        <div className="table-list">
          {timeline.slice(0,12).map((item, idx) => <div key={idx}><strong>{item.label}</strong><div className="muted">{item.type} · {item.phone || '—'} · {item.detail || '—'}</div></div>)}
        </div>
      </Card>
    </div>
  </div>
}
