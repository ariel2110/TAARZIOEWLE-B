import { useEffect, useState } from 'react';
import { SectionTitle } from '../components/ui';
import {
  AgentGlobalStats, AgentStatusItem, AgentRunLog,
  getAgentGlobalStats, getAgentStatus, getAgentRecentRuns,
} from '../services/queries';

// ─── Stat box ───────────────────────────────────────────────────────────────

function StatBox({
  icon, value, label, color = '#1f2937', sub,
}: { icon: string; value: string; label: string; color?: string; sub?: string }) {
  return (
    <div style={{
      background: 'white', border: '2px solid #e5e7eb', borderRadius: 14,
      padding: '18px 20px', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
      flex: '1 1 150px', minWidth: 140,
    }}>
      <div style={{ fontSize: 26, marginBottom: 4 }}>{icon}</div>
      <div style={{ fontSize: 24, fontWeight: 800, color }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{sub}</div>}
      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 3 }}>{label}</div>
    </div>
  );
}

// ─── Agent card ─────────────────────────────────────────────────────────────

function AgentCard({ a }: { a: AgentStatusItem }) {
  const fmtILS = (v: number) => v.toFixed(3) === '0.000' && v > 0 ? v.toFixed(5) : v.toFixed(2);
  const priceLabel =
    typeof a.pricing_input_per_1m === 'number'
      ? `$${a.pricing_input_per_1m} / $${a.pricing_output_per_1m} per 1M`
      : String(a.pricing_input_per_1m);

  return (
    <div style={{
      background: 'white', border: `2px solid ${a.configured ? a.color : '#e5e7eb'}`,
      borderRadius: 14, padding: '16px 18px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
      opacity: a.configured ? 1 : 0.65, flex: '1 1 200px', minWidth: 200,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 22 }}>{a.emoji}</span>
        <span style={{ fontWeight: 700, fontSize: 15 }}>{a.label}</span>
        <span style={{
          marginRight: 'auto', fontSize: 10, padding: '2px 7px', borderRadius: 20,
          background: a.configured ? '#dcfce7' : '#fee2e2',
          color: a.configured ? '#166534' : '#991b1b', fontWeight: 600,
        }}>
          {a.configured ? '✓ פעיל' : '✗ לא מוגדר'}
        </span>
      </div>
      <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>{a.model || '—'}</div>
      <div style={{ fontSize: 10, color: '#9ca3af', marginBottom: 12 }}>{priceLabel}</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 12px', fontSize: 12 }}>
        <div>
          <div style={{ color: '#9ca3af', fontSize: 10 }}>החודש</div>
          <div style={{ fontWeight: 700, color: '#111' }}>₪{fmtILS(a.cost_ils_this_month)}</div>
          <div style={{ color: '#6b7280' }}>{a.calls_this_month.toLocaleString()} קריאות</div>
        </div>
        <div>
          <div style={{ color: '#9ca3af', fontSize: 10 }}>סה"כ</div>
          <div style={{ fontWeight: 700, color: '#111' }}>₪{fmtILS(a.cost_ils_all_time)}</div>
          <div style={{ color: '#6b7280' }}>{a.calls_all_time.toLocaleString()} קריאות</div>
        </div>
        <div style={{ gridColumn: '1/-1', marginTop: 4 }}>
          <div style={{ color: '#9ca3af', fontSize: 10 }}>עלות ממוצעת לקריאה</div>
          <div style={{ fontWeight: 700, color: a.color }}>
            ₪{fmtILS(a.projected_cost_per_call_ils)}
          </div>
          {a.avg_input_tokens > 0 && (
            <div style={{ color: '#9ca3af', fontSize: 10 }}>
              {Math.round(a.avg_input_tokens).toLocaleString()} in / {Math.round(a.avg_output_tokens).toLocaleString()} out tokens
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Spend bar ───────────────────────────────────────────────────────────────

function SpendBar({ breakdown }: { breakdown: AgentGlobalStats['agent_breakdown'] }) {
  const total = breakdown.reduce((s, a) => s + a.cost_ils, 0);
  if (total === 0) return (
    <div style={{ color: '#9ca3af', fontSize: 13, padding: '12px 0' }}>אין נתוני הוצאה עדיין</div>
  );
  return (
    <div>
      {/* Stacked bar */}
      <div style={{ display: 'flex', height: 24, borderRadius: 8, overflow: 'hidden', marginBottom: 12 }}>
        {breakdown.filter(a => a.cost_ils > 0).map(a => (
          <div
            key={a.agent}
            title={`${a.label}: ₪${a.cost_ils.toFixed(3)}`}
            style={{ width: `${(a.cost_ils / total) * 100}%`, background: a.color, transition: 'width 0.4s' }}
          />
        ))}
      </div>
      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 18px' }}>
        {breakdown.map(a => (
          <div key={a.agent} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12 }}>
            <span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 3, background: a.color }} />
            <span>{a.emoji} {a.label}</span>
            <span style={{ fontWeight: 700 }}>₪{a.cost_ils.toFixed(3)}</span>
            <span style={{ color: '#9ca3af' }}>({((a.cost_ils / total) * 100).toFixed(1)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Recent runs table ───────────────────────────────────────────────────────

const AGENTS_ALL = [
  { value: '', label: 'כל הסוכנים' },
  { value: 'claude', label: '🤖 Claude' },
  { value: 'gpt', label: '🟢 GPT' },
  { value: 'gemini', label: '💎 Gemini' },
  { value: 'grok', label: '⚡ Grok' },
  { value: 'serper', label: '🔍 Serper' },
  { value: 'apify', label: '🕷️ Apify' },
];

function RecentRunsTable({ runs }: { runs: AgentRunLog[] }) {
  if (runs.length === 0) return (
    <div style={{ color: '#9ca3af', fontSize: 13, padding: '12px 0' }}>אין ריצות אחרונות</div>
  );
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #e5e7eb', textAlign: 'right' }}>
            {['זמן', 'סוכן', 'מודל', 'שלב', 'עסק', 'Tokens In', 'Tokens Out', 'עלות ₪'].map(h => (
              <th key={h} style={{ padding: '6px 10px', color: '#6b7280', fontWeight: 600, whiteSpace: 'nowrap' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {runs.map(r => (
            <tr key={r.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
              <td style={{ padding: '6px 10px', color: '#9ca3af', whiteSpace: 'nowrap' }}>
                {r.created_at ? new Date(r.created_at).toLocaleString('he-IL', { hour12: false, timeStyle: 'short', dateStyle: 'short' }) : '—'}
              </td>
              <td style={{ padding: '6px 10px', whiteSpace: 'nowrap' }}>{r.agent_name}</td>
              <td style={{ padding: '6px 10px', color: '#6b7280', whiteSpace: 'nowrap' }}>{r.model_name || '—'}</td>
              <td style={{ padding: '6px 10px', color: '#6b7280', whiteSpace: 'nowrap' }}>{r.stage || r.task_type || '—'}</td>
              <td style={{ padding: '6px 10px', color: '#6b7280' }}>{r.business_id ?? '—'}</td>
              <td style={{ padding: '6px 10px', textAlign: 'left' }}>{r.input_tokens.toLocaleString()}</td>
              <td style={{ padding: '6px 10px', textAlign: 'left' }}>{r.output_tokens.toLocaleString()}</td>
              <td style={{ padding: '6px 10px', fontWeight: 700, color: '#0f172a', textAlign: 'left' }}>
                ₪{r.cost_ils < 0.01 ? r.cost_ils.toFixed(5) : r.cost_ils.toFixed(3)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function AgentsDashboard() {
  const [global, setGlobal] = useState<AgentGlobalStats | null>(null);
  const [agents, setAgents] = useState<{ agents: AgentStatusItem[]; usd_to_ils: number } | null>(null);
  const [runs, setRuns] = useState<AgentRunLog[]>([]);
  const [filterAgent, setFilterAgent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [g, a, r] = await Promise.all([
          getAgentGlobalStats(),
          getAgentStatus(),
          getAgentRecentRuns(),
        ]);
        setGlobal(g); setAgents(a); setRuns(r);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'שגיאה בטעינת נתונים');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleAgentFilter = async (agent: string) => {
    setFilterAgent(agent);
    try {
      const r = await getAgentRecentRuns(agent || undefined);
      setRuns(r);
    } catch { /* silent */ }
  };

  if (loading) return (
    <div style={{ padding: 40, textAlign: 'center', color: '#6b7280', fontSize: 16 }}>
      ⏳ טוען נתוני סוכני AI...
    </div>
  );
  if (error) return (
    <div style={{ padding: 40, textAlign: 'center', color: '#dc2626' }}>
      ❌ {error}
    </div>
  );

  const g = global!;
  const marginColor = g.margin_pct >= 70 ? '#166534' : g.margin_pct >= 40 ? '#ca8a04' : '#dc2626';

  return (
    <div dir="rtl" style={{ padding: '24px 28px', maxWidth: 1200, margin: '0 auto' }}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800 }}>📡 כלכלת יחידה — סוכני AI</h1>
          <div style={{ color: '#6b7280', fontSize: 13, marginTop: 4 }}>
            מעקב עלויות API בזמן אמת · {g.period}
          </div>
        </div>
        <button
          onClick={() => window.location.reload()}
          style={{ padding: '8px 14px', border: '1px solid #e5e7eb', borderRadius: 8, background: 'white', cursor: 'pointer', fontSize: 13, color: '#374151' }}
        >
          🔄 רענן
        </button>
      </div>

      {/* ── KPI stat boxes ── */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, marginBottom: 32 }}>
        <StatBox
          icon="💰"
          value={`₪${g.net_profit_ils.toFixed(0)}`}
          label="רווח נקי החודש"
          color={g.net_profit_ils >= 0 ? '#166534' : '#dc2626'}
        />
        <StatBox
          icon="📈"
          value={`₪${g.total_revenue_ils.toFixed(0)}`}
          label="הכנסות החודש"
          color="#1d4ed8"
        />
        <StatBox
          icon="🔧"
          value={`₪${g.total_api_cost_ils.toFixed(2)}`}
          label="עלות API החודש"
          sub={`$${(g.total_api_cost_ils / (agents?.usd_to_ils ?? 3.7)).toFixed(3)}`}
          color="#7c3aed"
        />
        <StatBox
          icon="📊"
          value={`${g.margin_pct.toFixed(1)}%`}
          label="מרג'ין"
          color={marginColor}
        />
        <StatBox
          icon="🏗️"
          value={String(g.sites_built)}
          label="אתרים שנבנו החודש"
        />
      </div>

      {/* ── Agent spend breakdown ── */}
      <div style={{ background: 'white', border: '2px solid #e5e7eb', borderRadius: 14, padding: '18px 20px', marginBottom: 28, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
        <SectionTitle>🍰 פילוח הוצאות API לפי סוכן — החודש</SectionTitle>
        <SpendBar breakdown={g.agent_breakdown} />
      </div>

      {/* ── Per-agent cards ── */}
      <SectionTitle>🤖 סטטוס סוכנים</SectionTitle>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, marginBottom: 32 }}>
        {(agents?.agents ?? []).map(a => <AgentCard key={a.agent} a={a} />)}
      </div>

      {/* ── Recent runs ── */}
      <div style={{ background: 'white', border: '2px solid #e5e7eb', borderRadius: 14, padding: '18px 20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <SectionTitle>📋 ריצות אחרונות</SectionTitle>
          <select
            value={filterAgent}
            onChange={e => handleAgentFilter(e.target.value)}
            style={{ padding: '6px 10px', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 12, cursor: 'pointer' }}
          >
            {AGENTS_ALL.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <RecentRunsTable runs={runs} />
      </div>

    </div>
  );
}
