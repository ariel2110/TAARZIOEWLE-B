import { useEffect, useState } from 'react';
import { SectionTitle } from '../components/ui';
import {
    AgentGlobalStats, AgentStatusItem, AgentRunLog, AgentBuildConfig,
    AgentConnectionResult, AgentConnectionTestResponse,
    ApiKeyGroup, ApiKeyItem, FacebookStats,
    getAgentGlobalStats, getAgentStatus, getAgentRecentRuns,
    getApiKeys, updateApiKey, getFacebookStats, triggerFacebookTokenRefresh,
    toggleAgent, testAgentConnections,
} from '../services/queries';

// ─── Stat box ───────────────────────────────────────────────────────────────

function StatBox({
    icon, value, label, color = '#1f2937', sub,
}: { icon: string; value: string; label: string; color?: string; sub?: string }) {
    return (
        <div style={{
            background: 'white', border: '2px solid #e5e7eb', borderRadius: 14,
            padding: '14px 16px', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
            flex: '1 1 130px', minWidth: 110, maxWidth: 220,
        }}>
            <div style={{ fontSize: 26, marginBottom: 4 }}>{icon}</div>
            <div style={{ fontSize: 24, fontWeight: 800, color }}>{value}</div>
            {sub && <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{sub}</div>}
            <div style={{ fontSize: 12, color: '#6b7280', marginTop: 3 }}>{label}</div>
        </div>
    );
}

// ─── Toggle switch ───────────────────────────────────────────────────────────

function ToggleSwitch({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
    return (
        <button
            onClick={() => !disabled && onChange(!checked)}
            title={checked ? 'לחץ לכיבוי הסוכן' : 'לחץ להפעלת הסוכן'}
            style={{
                display: 'inline-flex', alignItems: 'center', cursor: disabled ? 'default' : 'pointer',
                background: 'none', border: 'none', padding: 0, gap: 5, opacity: disabled ? 0.5 : 1,
            }}
        >
            <div style={{
                width: 38, height: 20, borderRadius: 10, position: 'relative', transition: 'background 0.2s',
                background: checked ? '#16a34a' : '#d1d5db',
            }}>
                <div style={{
                    position: 'absolute', top: 2, left: checked ? 20 : 2, width: 16, height: 16,
                    borderRadius: '50%', background: 'white', boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                    transition: 'left 0.2s',
                }} />
            </div>
        </button>
    );
}

// ─── Role badge ───────────────────────────────────────────────────────────────

const ROLE_DISPLAY: Record<string, { label: string; bg: string; color: string }> = {
    content: { label: '📄 תוכן',  bg: '#eff6ff', color: '#1d4ed8' },
    design:  { label: '🎨 עיצוב', bg: '#fdf4ff', color: '#7e22ce' },
    html:    { label: '🔨 HTML',  bg: '#fff7ed', color: '#c2410c' },
};

// ─── Agent card ─────────────────────────────────────────────────────────────

const LLM_AGENTS = ['claude', 'gpt', 'gemini', 'grok', 'deepseek', 'mistral', 'cohere'];

function AgentCard({ a, onToggle, toggling }: {
    a: AgentStatusItem;
    onToggle?: (enabled: boolean) => void;
    toggling?: boolean;
}) {
    const fmtILS = (v: number) => v.toFixed(3) === '0.000' && v > 0 ? v.toFixed(5) : v.toFixed(2);
    const priceLabel =
        typeof a.pricing_input_per_1m === 'number'
            ? `$${a.pricing_input_per_1m} / $${a.pricing_output_per_1m} per 1M`
            : String(a.pricing_input_per_1m);

    const isLLM = LLM_AGENTS.includes(a.agent);
    const disabled = isLLM && !a.is_enabled;

    return (
        <div style={{
            background: 'white',
            border: `2px solid ${disabled ? '#e5e7eb' : a.configured ? a.color : '#e5e7eb'}`,
            borderRadius: 14, padding: '14px 16px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
            opacity: disabled ? 0.5 : a.configured ? 1 : 0.65,
            flex: '1 1 180px', minWidth: 160,
            transition: 'opacity 0.2s, border-color 0.2s',
        }}>
            {/* Header row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <span style={{ fontSize: 22 }}>{a.emoji}</span>
                <span style={{ fontWeight: 700, fontSize: 15 }}>{a.label}</span>
                {/* API configured badge */}
                <span style={{
                    fontSize: 10, padding: '2px 7px', borderRadius: 20,
                    background: a.configured ? '#dcfce7' : '#fee2e2',
                    color: a.configured ? '#166534' : '#991b1b', fontWeight: 600,
                }}>
                    {a.configured ? '✓ מוגדר' : '✗ לא מוגדר'}
                </span>
                {/* Toggle switch (only for LLM agents with API key) */}
                {isLLM && a.configured && onToggle && (
                    <div style={{ marginRight: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 10, color: a.is_enabled ? '#16a34a' : '#6b7280', fontWeight: 600 }}>
                            {toggling ? '⏳' : a.is_enabled ? 'פעיל' : 'כבוי'}
                        </span>
                        <ToggleSwitch
                            checked={a.is_enabled}
                            onChange={onToggle}
                            disabled={toggling}
                        />
                    </div>
                )}
            </div>

            {/* Role badges */}
            {a.build_roles && a.build_roles.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
                    {a.build_roles.map(role => {
                        const rd = ROLE_DISPLAY[role];
                        if (!rd) return null;
                        return (
                            <span key={role} style={{
                                fontSize: 10, padding: '2px 8px', borderRadius: 20,
                                background: rd.bg, color: rd.color, fontWeight: 700,
                                border: `1px solid ${rd.color}33`,
                            }}>
                                {rd.label}
                            </span>
                        );
                    })}
                </div>
            )}

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

// ─── Build config panel ───────────────────────────────────────────────────────

function BuildConfigPanel({ cfg }: { cfg: AgentBuildConfig }) {
    const stageNames: Record<string, string> = { content: 'תוכן ושיווק', design: 'עיצוב וסגנון', html: 'בנייה HTML' };
    const stageIcons: Record<string, string> = { content: '📄', design: '🎨', html: '🔨' };
    const enabled = cfg.enabled_agents;
    const roles = cfg.roles;

    return (
        <div style={{
            background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
            border: '2px solid #bae6fd', borderRadius: 14, padding: '16px 20px',
            marginBottom: 24, boxShadow: '0 2px 8px rgba(14,165,233,0.1)',
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <span style={{ fontSize: 20 }}>🏗️</span>
                <div>
                    <div style={{ fontWeight: 800, fontSize: 15, color: '#0c4a6e' }}>תצורת בנייה נוכחית</div>
                    <div style={{ fontSize: 12, color: '#0369a1' }}>
                        {enabled.length === 0
                            ? '⚠️ כל הסוכנים כבויים — משתמש בגיבוי'
                            : `${enabled.length} סוכן${enabled.length > 1 ? 'ים' : ''} פעיל${enabled.length > 1 ? 'ים' : ''}`
                        }
                    </div>
                </div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                {Object.entries(roles).map(([stage, agent]) => {
                    const rd = ROLE_DISPLAY[stage];
                    return (
                        <div key={stage} style={{
                            background: 'white', border: `2px solid ${rd?.color ?? '#e5e7eb'}33`,
                            borderRadius: 10, padding: '8px 14px', minWidth: 120, textAlign: 'center',
                            boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
                        }}>
                            <div style={{ fontSize: 18, marginBottom: 2 }}>{stageIcons[stage] ?? '⚙️'}</div>
                            <div style={{ fontSize: 10, color: '#6b7280', marginBottom: 2 }}>{stageNames[stage] ?? stage}</div>
                            <div style={{ fontWeight: 700, fontSize: 13, color: rd?.color ?? '#374151' }}>
                                {agent.toUpperCase()}
                            </div>
                        </div>
                    );
                })}
            </div>
            {enabled.length === 1 && (
                <div style={{ marginTop: 10, fontSize: 12, color: '#0369a1', fontStyle: 'italic' }}>
                    💡 סוכן יחיד פעיל — מטפל בכל השלבים בעצמו
                </div>
            )}
            {enabled.length >= 2 && (
                <div style={{ marginTop: 10, fontSize: 12, color: '#0369a1', fontStyle: 'italic' }}>
                    💡 {enabled.length} סוכנים פעילים — כל אחד ממוקד בתפקידו
                </div>
            )}
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
    { value: 'deepseek', label: '🐋 DeepSeek' },
    { value: 'mistral', label: '🌬️ Mistral' },
    { value: 'cohere', label: '🔷 Cohere' },
    { value: 'serper', label: '🔍 Serper' },
    { value: 'apify', label: '🕷️ Apify' },
];

function RecentRunsTable({ runs }: { runs: AgentRunLog[] }) {
    if (runs.length === 0) return (
        <div style={{ color: '#9ca3af', fontSize: 13, padding: '12px 0' }}>אין ריצות אחרונות</div>
    );
    return (
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
    );
}

// ─── Facebook Stats Card ─────────────────────────────────────────────────────

function FacebookStatsCard() {
    const [stats, setStats] = useState<FacebookStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

    useEffect(() => {
        getFacebookStats()
            .then(setStats)
            .catch(() => setStats({ status: 'error', page_name: null, followers: null, fan_count: null, detail: 'שגיאת רשת' }))
            .finally(() => setLoading(false));
    }, []);

    const handleRefresh = async () => {
        setRefreshing(true);
        setRefreshMsg(null);
        try {
            const res = await triggerFacebookTokenRefresh();
            if (res.triggered) {
                setRefreshMsg('✅ רענון הופעל — תקבל הודעת WhatsApp בסיום');
            } else {
                setRefreshMsg(`❌ ${res.detail || 'שגיאה בהפעלת רענון'}`);
            }
        } catch {
            setRefreshMsg('❌ שגיאת רשת');
        } finally {
            setRefreshing(false);
            setTimeout(() => setRefreshMsg(null), 6000);
        }
    };

    const statusMap: Record<FacebookStats['status'], { label: string; color: string; bg: string; icon: string }> = {
        active: { label: 'פעיל', color: '#166534', bg: '#dcfce7', icon: '✅' },
        no_token: { label: 'לא מוגדר', color: '#92400e', bg: '#fef3c7', icon: '⚠️' },
        token_expired: { label: 'טוקן פג תוקף', color: '#991b1b', bg: '#fee2e2', icon: '🔴' },
        error: { label: 'שגיאה', color: '#991b1b', bg: '#fee2e2', icon: '❌' },
    };

    const s = stats ? statusMap[stats.status] : null;

    return (
        <div style={{
            background: 'white',
            border: `2px solid ${s ? s.color : '#e5e7eb'}`,
            borderRadius: 14,
            padding: '18px 22px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
            flex: '1 1 260px',
            minWidth: 240,
            maxWidth: 380,
        }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                <span style={{ fontSize: 24 }}>📘</span>
                <div>
                    <div style={{ fontWeight: 700, fontSize: 15 }}>Facebook Page</div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>Graph API v19.0</div>
                </div>
                {s && (
                    <span style={{
                        marginRight: 'auto',
                        fontSize: 11, padding: '3px 10px', borderRadius: 20,
                        background: s.bg, color: s.color, fontWeight: 700,
                    }}>
                        {s.icon} {s.label}
                    </span>
                )}
            </div>

            {loading && <div style={{ color: '#9ca3af', fontSize: 13 }}>⏳ טוען...</div>}

            {!loading && stats?.status === 'active' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 18px' }}>
                    <div>
                        <div style={{ fontSize: 10, color: '#9ca3af', marginBottom: 2 }}>שם העמוד</div>
                        <div style={{ fontWeight: 700, fontSize: 15, color: '#1877f2', wordBreak: 'break-word' }}>
                            {stats.page_name ?? '—'}
                        </div>
                    </div>
                    <div>
                        <div style={{ fontSize: 10, color: '#9ca3af', marginBottom: 2 }}>עוקבים</div>
                        <div style={{ fontWeight: 700, fontSize: 20, color: '#1f2937' }}>
                            {stats.followers != null ? stats.followers.toLocaleString('he-IL') : '—'}
                        </div>
                    </div>
                    {stats.fan_count != null && stats.fan_count !== stats.followers && (
                        <div>
                            <div style={{ fontSize: 10, color: '#9ca3af', marginBottom: 2 }}>לייקים לעמוד</div>
                            <div style={{ fontWeight: 700, fontSize: 15, color: '#1f2937' }}>
                                {stats.fan_count.toLocaleString('he-IL')}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {!loading && stats?.status === 'token_expired' && (
                <div style={{ background: '#fee2e2', borderRadius: 8, padding: '10px 12px', fontSize: 13, color: '#991b1b', fontWeight: 600 }}>
                    🔴 הטוקן פג תוקף — יש לחדש אותו:
                    <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 5 }}>
                        <a href="https://developers.facebook.com/tools/debug/accesstoken" target="_blank" rel="noopener noreferrer"
                            style={{ color: '#1877f2', fontWeight: 600, fontSize: 12 }}>
                            🔍 Access Token Debugger — הארכת טוקן ל-60 יום
                        </a>
                        <a href="https://developers.facebook.com/tools/explorer" target="_blank" rel="noopener noreferrer"
                            style={{ color: '#1877f2', fontWeight: 600, fontSize: 12 }}>
                            🛠 Graph API Explorer — הפקת טוקן חדש
                        </a>
                        <a href="https://developers.facebook.com/apps" target="_blank" rel="noopener noreferrer"
                            style={{ color: '#1877f2', fontWeight: 600, fontSize: 12 }}>
                            ⚙️ My Apps — App ID ו-App Secret
                        </a>
                    </div>
                </div>
            )}

            {!loading && stats?.status === 'no_token' && (
                <div style={{ fontSize: 13, color: '#92400e' }}>
                    הגדר FACEBOOK_ACCESS_TOKEN בקטע מפתחות API למטה.
                </div>
            )}

            {!loading && stats?.status === 'error' && (
                <div style={{ fontSize: 13, color: '#991b1b' }}>{stats.detail}</div>
            )}

            {/* Manual refresh button */}
            <div style={{ marginTop: 14, borderTop: '1px solid #f3f4f6', paddingTop: 12 }}>
                <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    style={{
                        background: refreshing ? '#e5e7eb' : '#1877f2',
                        color: refreshing ? '#6b7280' : 'white',
                        border: 'none', borderRadius: 8,
                        padding: '7px 16px', fontSize: 12, fontWeight: 700,
                        cursor: refreshing ? 'not-allowed' : 'pointer',
                    }}
                >
                    {refreshing ? '⏳ מחדש...' : '🔄 חדש טוקן עכשיו'}
                </button>
                <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 4 }}>
                    רענון אוטומטי כל 50 יום
                </div>
                {refreshMsg && (
                    <div style={{
                        marginTop: 6, fontSize: 12, fontWeight: 600,
                        color: refreshMsg.startsWith('✅') ? '#065f46' : '#991b1b',
                    }}>
                        {refreshMsg}
                    </div>
                )}
            </div>
        </div>
    );
}

// ─── API Keys Section ────────────────────────────────────────────────────────

const CATEGORY_ICONS: Record<string, string> = {
    'LLM': '🤖', 'חיפוש ונתונים': '🔍', 'WhatsApp': '📱', 'תשלומים': '💳', 'תשתית': '🔧',
};

function ApiKeyCard({ item, onSaved }: { item: ApiKeyItem; onSaved: (result: ApiKeyItem) => void }) {
    const [editing, setEditing] = useState(false);
    const [inputVal, setInputVal] = useState('');
    const [showVal, setShowVal] = useState(false);
    const [saving, setSaving] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const [savedBanner, setSavedBanner] = useState(false);

    const friendlyError = (e: unknown): string => {
        const msg = e instanceof Error ? e.message : String(e);
        if (msg.includes('400')) return 'שגיאת validation — מפתח לא תקין';
        if (msg.includes('401')) return 'פג תוקף session — רענן את הדף';
        if (msg.includes('403')) return 'אין הרשאה לשנות מפתח זה';
        if (msg.includes('500')) return 'שגיאת שרת — נסה שנית או בדוק logs';
        return msg || 'שגיאה לא ידועה';
    };

    const handleSave = async () => {
        setSaving(true); setErr(null);
        try {
            const res = await updateApiKey(item.key, inputVal.trim() || null);
            onSaved({ ...item, configured: res.configured, masked: res.masked });
            setEditing(false); setInputVal('');
            setSavedBanner(true);
            setTimeout(() => setSavedBanner(false), 8000);
        } catch (e: unknown) {
            setErr(friendlyError(e));
        } finally { setSaving(false); }
    };

    const handleDelete = async () => {
        if (!window.confirm(`למחוק את המפתח "${item.label}"?`)) return;
        setSaving(true); setErr(null);
        try {
            const res = await updateApiKey(item.key, null);
            onSaved({ ...item, configured: res.configured, masked: res.masked });
        } catch (e: unknown) {
            setErr(friendlyError(e));
        } finally { setSaving(false); }
    };

    return (
        <div style={{
            background: 'white',
            border: `2px solid ${item.configured ? '#d1fae5' : '#e5e7eb'}`,
            borderRadius: 12, padding: '14px 16px',
            flex: '1 1 220px', minWidth: 0, maxWidth: '100%', boxSizing: 'border-box',
        }}>
            {/* Header row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span style={{ fontWeight: 700, fontSize: 14, flex: 1 }}>{item.label}</span>
                <span style={{
                    fontSize: 10, padding: '2px 7px', borderRadius: 20, fontWeight: 700,
                    background: item.configured ? '#dcfce7' : '#fee2e2',
                    color: item.configured ? '#166534' : '#991b1b',
                }}>
                    {item.configured ? '✓ פעיל' : '✗ חסר'}
                </span>
            </div>

            {/* Role description */}
            {item.role && (
                <div style={{ fontSize: 12, color: '#3b82f6', marginBottom: 8, fontWeight: 500 }}>{item.role}</div>
            )}

            {/* Masked value + env var */}
            <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 10, fontFamily: 'monospace', wordBreak: 'break-all', overflowWrap: 'anywhere' }}>
                {item.env_var}
                {item.masked && (
                    <span style={{ marginRight: 8, color: '#6b7280' }}>{item.masked}</span>
                )}
            </div>

            {/* Celery restart warning banner */}
            {savedBanner && (
                <div style={{
                    fontSize: 11, padding: '6px 10px', borderRadius: 8, marginBottom: 8,
                    background: '#fefce8', border: '1px solid #fde047', color: '#854d0e',
                    lineHeight: 1.5,
                }}>
                    ✅ נשמר בהצלחה. לכניסה מלאה לתוקף ב-Celery workers — נדרש <b>restart ידני</b>
                </div>
            )}

            {/* Edit form */}
            {editing ? (
                <div>
                    <div style={{ display: 'flex', gap: 6, marginBottom: 6 }}>
                        <input
                            type={showVal ? 'text' : 'password'}
                            value={inputVal}
                            onChange={e => setInputVal(e.target.value)}
                            placeholder="הדבק מפתח חדש..."
                            dir="ltr"
                            autoFocus
                            style={{
                                flex: 1, minWidth: 0, padding: '6px 10px', border: '1px solid #d1d5db',
                                borderRadius: 8, fontSize: 12, fontFamily: 'monospace', width: '100%',
                            }}
                        />
                        <button
                            onClick={() => setShowVal(v => !v)}
                            title={showVal ? 'הסתר' : 'הצג'}
                            style={{ padding: '6px 10px', border: '1px solid #d1d5db', borderRadius: 8, background: 'white', cursor: 'pointer', fontSize: 14 }}
                        >
                            {showVal ? '🙈' : '👁'}
                        </button>
                    </div>
                    {err && <div style={{ fontSize: 11, color: '#dc2626', marginBottom: 6 }}>{err}</div>}
                    <div style={{ display: 'flex', gap: 6 }}>
                        <button
                            onClick={handleSave} disabled={saving}
                            style={{ flex: 1, padding: '6px 0', background: '#1d4ed8', color: 'white', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 13, fontWeight: 700 }}
                        >
                            {saving ? '...' : '💾 שמור'}
                        </button>
                        <button
                            onClick={() => { setEditing(false); setInputVal(''); setErr(null); }}
                            style={{ padding: '6px 12px', border: '1px solid #e5e7eb', borderRadius: 8, background: 'white', cursor: 'pointer', fontSize: 13 }}
                        >
                            ביטול
                        </button>
                    </div>
                </div>
            ) : (
                <div style={{ display: 'flex', gap: 6 }}>
                    <button
                        onClick={() => setEditing(true)}
                        style={{ flex: 1, padding: '6px 0', background: '#f0f9ff', color: '#0369a1', border: '1px solid #bae6fd', borderRadius: 8, cursor: 'pointer', fontSize: 13, fontWeight: 600 }}
                    >
                        ✏️ {item.configured ? 'החלף' : 'הגדר'}
                    </button>
                    {item.manage_url && (
                        <a
                            href={item.manage_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="פתח ניהול"
                            style={{ padding: '6px 10px', background: '#f0fdf4', color: '#16a34a', border: '1px solid #bbf7d0', borderRadius: 8, cursor: 'pointer', fontSize: 14, textDecoration: 'none', display: 'flex', alignItems: 'center' }}
                        >
                            🔗
                        </a>
                    )}
                    {item.configured && (
                        <button
                            onClick={handleDelete} disabled={saving}
                            title="מחק מפתח"
                            style={{ padding: '6px 10px', background: '#fff1f2', color: '#dc2626', border: '1px solid #fecaca', borderRadius: 8, cursor: 'pointer', fontSize: 14 }}
                        >
                            🗑
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}

function ApiKeysSection() {
    const [groups, setGroups] = useState<ApiKeyGroup[]>([]);
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState<string | null>(null);

    useEffect(() => {
        getApiKeys()
            .then(r => setGroups(r.groups))
            .catch((e: unknown) => setErr(e instanceof Error ? e.message : 'שגיאה'))
            .finally(() => setLoading(false));
    }, []);

    const handleSaved = (groupIdx: number, keyIdx: number, updated: ApiKeyItem) => {
        setGroups(prev => prev.map((g, gi) =>
            gi !== groupIdx ? g : {
                ...g,
                keys: g.keys.map((k, ki) => ki === keyIdx ? updated : k),
            }
        ));
    };

    if (loading) return <div style={{ color: '#9ca3af', padding: '12px 0', fontSize: 13 }}>טוען מפתחות...</div>;
    if (err) return <div style={{ color: '#dc2626', padding: '12px 0', fontSize: 13 }}>❌ {err}</div>;

    return (
        <div>
            {groups.map((group, gi) => (
                <div key={group.category} style={{ marginBottom: 28 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
                        <span style={{ fontSize: 18 }}>{CATEGORY_ICONS[group.category] ?? '🔑'}</span>
                        <span style={{ fontWeight: 700, fontSize: 15 }}>{group.category}</span>
                        <span style={{ fontSize: 11, color: '#9ca3af', marginRight: 4 }}>
                            {group.keys.filter(k => k.configured).length}/{group.keys.length} מוגדרים
                        </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(240px, 100%), 1fr))', gap: 12 }}>
                        {group.keys.map((item, ki) => (
                            <ApiKeyCard
                                key={item.key}
                                item={item}
                                onSaved={updated => handleSaved(gi, ki, updated)}
                            />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

// ─── Tab Bar ─────────────────────────────────────────────────────────────────

const PAGE_TABS = [
    { id: 'overview', label: '📊 סקירה' },
    { id: 'connection', label: '🔌 בדיקת חיבור' },
    { id: 'runs', label: '📋 ריצות' },
    { id: 'social', label: '🌐 אינטגרציות' },
    { id: 'keys', label: '🔑 מפתחות' },
];

// ─── Connection test panel ────────────────────────────────────────────────────

const AGENT_DISPLAY_MAP: Record<string, { label: string; emoji: string; color: string }> = {
    serper:        { label: 'Serper /search', emoji: '🔍', color: '#0ea5e9' },
    serper_places: { label: 'Serper /places', emoji: '📍', color: '#0284c7' },
    apify:         { label: 'Apify',          emoji: '🕷️', color: '#f59e0b' },
    gpt:           { label: 'GPT / OpenAI',   emoji: '🟢', color: '#10b981' },
    claude:        { label: 'Claude',          emoji: '🤖', color: '#f97316' },
    gemini:        { label: 'Gemini',          emoji: '💎', color: '#8b5cf6' },
    grok:          { label: 'Grok / xAI',     emoji: '⚡', color: '#374151' },
    deepseek:      { label: 'DeepSeek',        emoji: '🐋', color: '#0ea5e9' },
    mistral:       { label: 'Mistral',         emoji: '🌬️', color: '#ff7000' },
    cohere:        { label: 'Cohere',          emoji: '🔷', color: '#3b4ac4' },
};

function ConnectionTestPanel() {
    const [data, setData] = useState<AgentConnectionTestResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [ran, setRan] = useState(false);

    const runTest = async () => {
        setLoading(true);
        try {
            const res = await testAgentConnections();
            setData(res);
            setRan(true);
        } catch (e: unknown) {
            setData({ all_ok: false, tested_at: new Date().toISOString(), test_business: '', results: [
                { agent: 'error', ok: false, latency_ms: -1, detail: e instanceof Error ? e.message : 'שגיאה' }
            ]});
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 20 }}>
                <div>
                    <div style={{ fontWeight: 800, fontSize: 16, color: '#0f172a' }}>🔌 בדיקת חיבור חי לכל הסוכנים</div>
                    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
                        שולח בקשת בדיקה אמיתית לכל שירות API — עסק בדיקה: <strong>קפה גינה מצפה רמון</strong>
                    </div>
                </div>
                <button
                    onClick={runTest}
                    disabled={loading}
                    style={{
                        padding: '10px 20px', borderRadius: 10, border: 'none', cursor: loading ? 'not-allowed' : 'pointer',
                        background: loading ? '#e5e7eb' : '#1d4ed8', color: loading ? '#9ca3af' : 'white',
                        fontWeight: 700, fontSize: 14, transition: 'all 0.2s',
                    }}
                >
                    {loading ? '⏳ בודק...' : ran ? '🔄 בדוק שוב' : '▶ הפעל בדיקה'}
                </button>
            </div>

            {!ran && !loading && (
                <div style={{
                    background: '#f8fafc', border: '2px dashed #e2e8f0', borderRadius: 14,
                    padding: 32, textAlign: 'center', color: '#94a3b8',
                }}>
                    <div style={{ fontSize: 40, marginBottom: 10 }}>🔌</div>
                    <div style={{ fontSize: 14 }}>לחץ על "הפעל בדיקה" כדי לבדוק את החיבור לכל הסוכנים</div>
                    <div style={{ fontSize: 12, marginTop: 6 }}>הבדיקה שולחת בקשה אמיתית ל-Serper, Apify, OpenAI, Anthropic, Google AI ו-xAI</div>
                </div>
            )}

            {ran && data && (
                <>
                    {/* Summary banner */}
                    <div style={{
                        borderRadius: 12, padding: '12px 18px', marginBottom: 18,
                        background: data.all_ok ? '#dcfce7' : '#fef2f2',
                        border: `2px solid ${data.all_ok ? '#86efac' : '#fca5a5'}`,
                        display: 'flex', alignItems: 'center', gap: 10,
                    }}>
                        <span style={{ fontSize: 20 }}>{data.all_ok ? '✅' : '⚠️'}</span>
                        <div>
                            <div style={{ fontWeight: 700, fontSize: 14, color: data.all_ok ? '#166534' : '#991b1b' }}>
                                {data.all_ok ? 'כל החיבורים תקינים' : 'חלק מהחיבורים נכשלו'}
                            </div>
                            <div style={{ fontSize: 11, color: '#6b7280' }}>
                                נבדק: {new Date(data.tested_at).toLocaleString('he-IL')} | עסק: {data.test_business}
                            </div>
                        </div>
                        <div style={{ marginRight: 'auto', fontWeight: 700, fontSize: 13 }}>
                            {data.results.filter(r => r.ok).length}/{data.results.length} ✓
                        </div>
                    </div>

                    {/* Result cards */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
                        {data.results.map((r: AgentConnectionResult) => {
                            const display = AGENT_DISPLAY_MAP[r.agent] ?? { label: r.agent, emoji: '⚙️', color: '#6b7280' };
                            return (
                                <div key={r.agent} style={{
                                    background: 'white',
                                    border: `2px solid ${r.ok ? '#bbf7d0' : '#fca5a5'}`,
                                    borderRadius: 12, padding: '14px 16px',
                                    boxShadow: '0 2px 6px rgba(0,0,0,0.05)',
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                        <span style={{ fontSize: 20 }}>{display.emoji}</span>
                                        <span style={{ fontWeight: 700, fontSize: 14 }}>{display.label}</span>
                                        <span style={{
                                            marginRight: 'auto', fontSize: 10, fontWeight: 700,
                                            padding: '2px 8px', borderRadius: 20,
                                            background: r.ok ? '#dcfce7' : '#fee2e2',
                                            color: r.ok ? '#166534' : '#991b1b',
                                        }}>
                                            {r.ok ? '✓ תקין' : '✗ שגיאה'}
                                        </span>
                                    </div>
                                    <div style={{ fontSize: 12, color: '#374151', marginBottom: 6, lineHeight: 1.5 }}>
                                        {r.detail}
                                    </div>
                                    {r.latency_ms >= 0 && (
                                        <div style={{ fontSize: 11, color: r.latency_ms < 500 ? '#16a34a' : r.latency_ms < 1500 ? '#ca8a04' : '#dc2626' }}>
                                            ⏱ {r.latency_ms}ms
                                        </div>
                                    )}
                                    {/* Extra details for Serper */}
                                    {r.extra && r.ok && (
                                        <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: '4px 12px' }}>
                                            {r.extra.credits_per_call !== undefined && (
                                                <span style={{ fontSize: 10, color: '#0369a1', background: '#e0f2fe', padding: '2px 8px', borderRadius: 20 }}>
                                                    💳 {String(r.extra.credits_per_call)} קרדיט לבקשה
                                                </span>
                                            )}
                                            {r.extra.organic_results !== undefined && (
                                                <span style={{ fontSize: 10, color: '#6b7280' }}>
                                                    📄 {String(r.extra.organic_results)} תוצאות
                                                </span>
                                            )}
                                            {r.extra.places_count !== undefined && (
                                                <span style={{ fontSize: 10, color: '#6b7280' }}>
                                                    📍 {String(r.extra.places_count)} עסקים
                                                </span>
                                            )}
                                            {r.extra.top_name && (
                                                <span style={{ fontSize: 10, color: '#374151', fontWeight: 600, width: '100%' }}>
                                                    📍 {String(r.extra.top_name)}
                                                    {r.extra.top_phone ? ` · ${String(r.extra.top_phone)}` : ''}
                                                    {r.extra.top_rating ? ` · ⭐ ${String(r.extra.top_rating)}` : ''}
                                                    {r.extra.top_price_level ? ` · ${String(r.extra.top_price_level)}` : ''}
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </>
            )}
        </div>
    );
}

// ─── Tab bar ─────────────────────────────────────────────────────────────────

function TabBar({ active, onChange }: { active: string; onChange: (id: string) => void }) {
    return (
        <div style={{
            display: 'flex',
            overflowX: 'auto',
            WebkitOverflowScrolling: 'touch',
            scrollbarWidth: 'none',
            borderBottom: '2px solid #e5e7eb',
            marginBottom: 20,
            gap: 2,
        }}>
            {PAGE_TABS.map(tab => (
                <button
                    key={tab.id}
                    onClick={() => onChange(tab.id)}
                    style={{
                        padding: '10px 16px',
                        border: 'none',
                        borderBottom: active === tab.id ? '3px solid #1d4ed8' : '3px solid transparent',
                        marginBottom: -2,
                        background: active === tab.id ? '#eff6ff' : 'none',
                        cursor: 'pointer',
                        fontWeight: active === tab.id ? 700 : 500,
                        color: active === tab.id ? '#1d4ed8' : '#6b7280',
                        fontSize: 13,
                        whiteSpace: 'nowrap',
                        borderRadius: '8px 8px 0 0',
                        transition: 'all 0.15s',
                    }}
                >
                    {tab.label}
                </button>
            ))}
        </div>
    );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function AgentsDashboard() {
    const [global, setGlobal] = useState<AgentGlobalStats | null>(null);
    const [agents, setAgents] = useState<{ agents: AgentStatusItem[]; usd_to_ils: number; build_config: AgentBuildConfig } | null>(null);
    const [runs, setRuns] = useState<AgentRunLog[]>([]);
    const [filterAgent, setFilterAgent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState('overview');
    const [toggling, setToggling] = useState<Set<string>>(new Set());

    const loadData = async () => {
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
    };

    useEffect(() => { loadData(); }, []);

    const handleToggle = async (agentName: string, enabled: boolean) => {
        setToggling(prev => new Set(prev).add(agentName));
        try {
            const res = await toggleAgent(agentName, enabled);
            // Optimistically update local state with new toggle + build config
            setAgents(prev => {
                if (!prev) return prev;
                return {
                    ...prev,
                    build_config: res.build_config,
                    agents: prev.agents.map(a => {
                        if (a.agent !== agentName) return a;
                        return { ...a, is_enabled: res.toggle.is_enabled };
                    }).map(a => ({
                        ...a,
                        build_roles: Object.entries(res.build_config.roles)
                            .filter(([, ag]) => ag === a.agent)
                            .map(([stage]) => stage),
                    })),
                };
            });
        } catch {
            // On error, reload fresh data
            await loadData();
        } finally {
            setToggling(prev => { const s = new Set(prev); s.delete(agentName); return s; });
        }
    };

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
    const buildConfig = agents?.build_config;

    return (
        <div style={{ padding: 'clamp(12px, 3vw, 28px)', maxWidth: 1200, margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>

            {/* ── Header ── */}
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 16 }}>
                <div>
                    <h1 style={{ margin: 0, fontSize: 'clamp(18px, 4vw, 24px)', fontWeight: 800 }}>📡 כלכלת יחידה — סוכני AI</h1>
                    <div style={{ color: '#6b7280', fontSize: 13, marginTop: 4 }}>
                        מעקב עלויות API בזמן אמת · {g.period}
                    </div>
                </div>
                <button
                    onClick={() => { setLoading(true); loadData(); }}
                    style={{ padding: '8px 14px', border: '1px solid #e5e7eb', borderRadius: 8, background: 'white', cursor: 'pointer', fontSize: 13, color: '#374151' }}
                >
                    🔄 רענן
                </button>
            </div>

            {/* ── Tab bar ── */}
            <TabBar active={activeTab} onChange={setActiveTab} />

            {/* ── Tab: Overview ── */}
            {activeTab === 'overview' && (
                <>
                    {/* KPI stat boxes */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 24 }}>
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

                    {/* Build config panel */}
                    {buildConfig && <BuildConfigPanel cfg={buildConfig} />}

                    {/* Spend breakdown */}
                    <div style={{ background: 'white', border: '2px solid #e5e7eb', borderRadius: 14, padding: '18px 20px', marginBottom: 28, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                        <SectionTitle>🍰 פילוח הוצאות API לפי סוכן — החודש</SectionTitle>
                        <SpendBar breakdown={g.agent_breakdown} />
                    </div>

                    {/* Per-agent cards */}
                    <SectionTitle>🤖 סוכני AI — הפעלה וכיבוי</SectionTitle>
                    <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 12 }}>
                        השתמש במתגים להפעלת/כיבוי סוכנים. הסוכנים הפעילים יחלקו תפקידים אוטומטית.
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, marginBottom: 8 }}>
                        {(agents?.agents ?? []).map(a => (
                            <AgentCard
                                key={a.agent}
                                a={a}
                                onToggle={LLM_AGENTS.includes(a.agent) ? (enabled) => handleToggle(a.agent, enabled) : undefined}
                                toggling={toggling.has(a.agent)}
                            />
                        ))}
                    </div>
                </>
            )}

            {/* ── Tab: Recent runs ── */}
            {activeTab === 'runs' && (
                <div style={{ background: 'white', border: '2px solid #e5e7eb', borderRadius: 14, padding: '16px 18px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 14 }}>
                        <SectionTitle>📋 ריצות אחרונות</SectionTitle>
                        <select
                            value={filterAgent}
                            onChange={e => handleAgentFilter(e.target.value)}
                            style={{ padding: '6px 10px', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 12, cursor: 'pointer', maxWidth: '100%' }}
                        >
                            {AGENTS_ALL.map(opt => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                            ))}
                        </select>
                    </div>
                    <div style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
                        <RecentRunsTable runs={runs} />
                    </div>
                </div>
            )}

            {/* ── Tab: Connection test ── */}
            {activeTab === 'connection' && (
                <div style={{ background: 'white', border: '2px solid #e5e7eb', borderRadius: 14, padding: '18px 20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                    <ConnectionTestPanel />
                </div>
            )}

            {/* ── Tab: Social integrations ── */}
            {activeTab === 'social' && (
                <>
                    <SectionTitle>🌐 אינטגרציות רשתות חברתיות</SectionTitle>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14 }}>
                        <FacebookStatsCard />
                    </div>
                </>
            )}

            {/* ── Tab: API Keys ── */}
            {activeTab === 'keys' && (
                <div style={{ background: 'white', border: '2px solid #e5e7eb', borderRadius: 14, padding: '18px 20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
                    <SectionTitle>🔑 מפתחות API וטוקנים</SectionTitle>
                    <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 20, marginTop: 0 }}>
                        ניהול מפתחות API — שינוי, החלפה או מחיקה. הערכים מוסתרים בממשק.
                    </p>
                    <ApiKeysSection />
                </div>
            )}

        </div>
    );
}
