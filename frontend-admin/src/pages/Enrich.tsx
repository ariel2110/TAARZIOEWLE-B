import { useEffect, useState, useCallback } from 'react';
import { Card, SectionTitle } from '../components/ui';
import {
  EnrichedBusiness, EnrichStatus, EnrichCategory,
  getEnrichStatus, getEnrichCategories, searchEnrich, importEnrichedToLeads, createDemosFromEnriched,
} from '../services/queries';
import { useNavigate } from 'react-router-dom';

const CITIES = ['תל אביב', 'ירושלים', 'חיפה', 'באר שבע', 'ראשון לציון', 'פתח תקווה', 'נתניה', 'אשדוד', 'רמת גן', 'הרצליה'];

/** Hot lead = no website + 50+ reviews + 4.5+ rating */
function isHotLead(biz: EnrichedBusiness) {
  return !biz.website && (biz.reviews_count || 0) >= 50 && (biz.rating || 0) >= 4.5;
}

function OpportunityBar({ score }: { score: number }) {
  const color = score >= 75 ? '#ef4444' : score >= 50 ? '#f97316' : score >= 30 ? '#eab308' : '#9ca3af';
  const label = score >= 75 ? '🔥 ליד חם מאוד' : score >= 50 ? '⚡ ליד טוב' : score >= 30 ? '👍 פוטנציאל' : '💤 רגיל';
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 3 }}>
        <span style={{ fontSize: 11, fontWeight: 700, color }}>{label}</span>
        <span style={{ fontSize: 11, color: '#9ca3af' }}>{score}/100</span>
      </div>
      <div style={{ height: 5, background: '#f3f4f6', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${score}%`, background: color, borderRadius: 3, transition: 'width 0.3s' }} />
      </div>
    </div>
  );
}

function CacheStatusBadge({ status }: { status?: string }) {
  if (status === 'imported') return <span style={{ background: '#d1fae5', color: '#065f46', borderRadius: 8, padding: '1px 8px', fontSize: 11, fontWeight: 600 }}>✅ יובא</span>;
  if (status === 'known') return <span style={{ background: '#fef3c7', color: '#92400e', borderRadius: 8, padding: '1px 8px', fontSize: 11, fontWeight: 600 }}>🔁 נראה</span>;
  return <span style={{ background: '#ede9fe', color: '#5b21b6', borderRadius: 8, padding: '1px 8px', fontSize: 11, fontWeight: 600 }}>✨ חדש</span>;
}

export default function EnrichPage() {
  const [status, setStatus] = useState<EnrichStatus | null>(null);
  const [categories, setCategories] = useState<EnrichCategory[]>([]);
  const [city, setCity] = useState('תל אביב');
  const [category, setCategory] = useState('');
  const [limit, setLimit] = useState(30);
  const [noWebsite, setNoWebsite] = useState(true);
  const [minReviews, setMinReviews] = useState(20);
  const [minRating, setMinRating] = useState(4.0);
  const [results, setResults] = useState<EnrichedBusiness[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [creatingDemos, setCreatingDemos] = useState(false);
  const [stats, setStats] = useState<{ new_this_search?: number; already_known?: number; hot_leads?: number } | null>(null);
  const [importMsg, setImportMsg] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    getEnrichStatus().then(setStatus).catch(() => { });
    getEnrichCategories().then(setCategories).catch(() => { });
  }, []);

  const handleSearch = useCallback(async () => {
    setLoading(true);
    setImportMsg('');
    try {
      const res = await searchEnrich(city, category, limit, false, noWebsite, minReviews, minRating);
      // Sort by opportunity score desc
      const sorted = [...res.results].sort((a, b) => (b.lead_opportunity_score || 0) - (a.lead_opportunity_score || 0));
      setResults(sorted);
      const hot = sorted.filter(isHotLead).length;
      setStats({ new_this_search: res.new_this_search, already_known: res.already_known, hot_leads: hot });
      setSelected(new Set());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [city, category, limit, noWebsite, minReviews, minRating]);

  const toggleSelect = (pid: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(pid)) next.delete(pid); else next.add(pid);
      return next;
    });
  };
  const selectAll = () => setSelected(new Set(results.map(r => r.place_id).filter(Boolean)));
  const selectHot = () => setSelected(new Set(results.filter(isHotLead).map(r => r.place_id).filter(Boolean)));
  const clearAll = () => setSelected(new Set());

  const handleCreateDemos = async () => {
    const toDemo = results.filter(r => r.place_id && selected.has(r.place_id));
    if (!toDemo.length) return;
    setCreatingDemos(true);
    try {
      const res = await createDemosFromEnriched(toDemo);
      setImportMsg(`🎬 נוצרו ${res.created} אתרי דמו!`);
      setTimeout(() => navigate('/demos'), 1200);
    } catch {
      setImportMsg('❌ שגיאה ביצירת דמואים');
    } finally {
      setCreatingDemos(false);
    }
  };

  const handleImport = async () => {
    const toImport = results.filter(r => r.place_id && selected.has(r.place_id));
    if (!toImport.length) return;
    setImporting(true);
    try {
      const res = await importEnrichedToLeads(toImport, city);
      setImportMsg(`✅ יובאו ${res.imported} עסקים כלידים${res.skipped ? ` (${res.skipped} דולגו)` : ''}`);
      setResults(prev => prev.map(r => selected.has(r.place_id) ? { ...r, cache_status: 'imported' as const } : r));
      setSelected(new Set());
      getEnrichStatus().then(setStatus).catch(() => { });
    } catch {
      setImportMsg('❌ שגיאה בייבוא');
    } finally {
      setImporting(false);
    }
  };

  return (
    <div dir="rtl" style={{ maxWidth: 1100, margin: '0 auto' }}>
      <SectionTitle>🔍 איסוף לידים — עסקים ללא אתר</SectionTitle>

      {/* Value proposition banner */}
      <div style={{ background: 'linear-gradient(135deg, #fef3c7 0%, #fce7f3 100%)', border: '1.5px solid #f59e0b', borderRadius: 12, padding: '14px 18px', marginBottom: 18 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: '#92400e', marginBottom: 6 }}>🎯 מה אנחנו מחפשים?</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
          {[
            { icon: '🌐', text: 'אין להם אתר — הם צריכים אחד' },
            { icon: '⭐', text: 'ביקורות גבוהות — עסק פעיל ואמין' },
            { icon: '📊', text: 'הרבה חיפושים בגוגל — ביקוש קיים' },
            { icon: '📞', text: 'בעל טלפון — ניתן לפנות אליהם' },
          ].map(({ icon, text }) => (
            <div key={text} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#78350f' }}>
              <span style={{ fontSize: 18 }}>{icon}</span>
              <span>{text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Status bar */}
      {status && (
        <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
          <span style={{ background: status.google_places ? '#d1fae5' : '#fee2e2', color: status.google_places ? '#065f46' : '#991b1b', borderRadius: 20, padding: '3px 12px', fontSize: 12, fontWeight: 600 }}>
            {status.google_places ? '✅ Google Places — Live' : '⚠️ Google Places — Demo'}
          </span>
          <span style={{ background: '#f3f4f6', color: '#374151', borderRadius: 20, padding: '3px 12px', fontSize: 12 }}>
            🗄️ בקאש: {status.cache_total || 0} עסקים ({status.cache_imported || 0} יובאו)
          </span>
        </div>
      )}

      <Card>
        {/* "ללא אתר" toggle — prominent */}
        <div style={{
          background: noWebsite ? 'linear-gradient(90deg,#fce7f3,#ede9fe)' : '#f9fafb',
          border: `2px solid ${noWebsite ? '#c084fc' : '#e5e7eb'}`,
          borderRadius: 10, padding: '10px 16px', marginBottom: 16,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10,
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', flex: 1 }}>
            <input type="checkbox" checked={noWebsite} onChange={e => setNoWebsite(e.target.checked)}
              style={{ width: 18, height: 18, accentColor: '#a855f7', cursor: 'pointer' }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: 14, color: noWebsite ? '#7e22ce' : '#374151' }}>
                🌐 רק עסקים ללא אתר אינטרנט
              </div>
              <div style={{ fontSize: 12, color: '#9ca3af' }}>
                {noWebsite ? 'פעיל — מסנן עסקים שכבר יש להם אתר' : 'כבוי — מציג גם עסקים עם אתר'}
              </div>
            </div>
          </label>
          {noWebsite && (
            <span style={{ background: '#a855f7', color: 'white', borderRadius: 20, padding: '3px 14px', fontSize: 12, fontWeight: 700 }}>
              🔥 מצב ציד לידים
            </span>
          )}
        </div>

        {/* Filters row */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: 12, color: '#6b7280', marginBottom: 4 }}>עיר</label>
            <select value={city} onChange={e => setCity(e.target.value)} style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: '6px 10px', fontSize: 14 }}>
              {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 12, color: '#6b7280', marginBottom: 4 }}>כמות תוצאות</label>
            <select value={limit} onChange={e => setLimit(Number(e.target.value))} style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: '6px 10px', fontSize: 14 }}>
              {[10, 20, 30, 50].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 12, color: '#6b7280', marginBottom: 4 }}>מינ׳ ביקורות</label>
            <input type="number" min={0} max={500} value={minReviews} onChange={e => setMinReviews(Number(e.target.value))}
              style={{ width: 72, border: '1px solid #e5e7eb', borderRadius: 8, padding: '6px 10px', fontSize: 14 }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 12, color: '#6b7280', marginBottom: 4 }}>מינ׳ דירוג ⭐</label>
            <input type="number" min={0} max={5} step={0.5} value={minRating} onChange={e => setMinRating(Number(e.target.value))}
              style={{ width: 72, border: '1px solid #e5e7eb', borderRadius: 8, padding: '6px 10px', fontSize: 14 }} />
          </div>
        </div>

        {/* Category pills */}
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: 'block', fontSize: 12, color: '#6b7280', marginBottom: 6 }}>קטגוריה:</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            <button onClick={() => setCategory('')}
              style={{ borderRadius: 20, padding: '4px 12px', border: `1.5px solid ${category === '' ? '#6366f1' : '#e5e7eb'}`, background: category === '' ? '#eef2ff' : 'white', color: category === '' ? '#4338ca' : '#374151', fontSize: 12, cursor: 'pointer', fontWeight: category === '' ? 700 : 400 }}>
              🔎 הכל
            </button>
            {categories.map(cat => (
              <button key={cat.label} onClick={() => setCategory(cat.label === category ? '' : cat.label)}
                style={{ borderRadius: 20, padding: '4px 12px', border: `1.5px solid ${category === cat.label ? '#6366f1' : '#e5e7eb'}`, background: category === cat.label ? '#eef2ff' : 'white', color: category === cat.label ? '#4338ca' : '#374151', fontSize: 12, cursor: 'pointer', fontWeight: category === cat.label ? 700 : 400 }}>
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        <button onClick={handleSearch} disabled={loading}
          style={{ background: loading ? '#9ca3af' : '#7c3aed', color: 'white', border: 'none', borderRadius: 10, padding: '11px 32px', fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer' }}>
          {loading ? '⏳ מחפש...' : '🔍 חפש לידים חמים'}
        </button>
      </Card>

      {/* Stats after search */}
      {stats && (
        <div style={{ display: 'flex', gap: 10, marginTop: 12, flexWrap: 'wrap' }}>
          {(stats.hot_leads || 0) > 0 && (
            <span style={{ background: '#fef2f2', color: '#991b1b', borderRadius: 20, padding: '4px 14px', fontSize: 13, fontWeight: 700, border: '1.5px solid #fca5a5' }}>
              🔥 {stats.hot_leads} לידים חמים
            </span>
          )}
          <span style={{ background: '#ede9fe', color: '#5b21b6', borderRadius: 20, padding: '4px 14px', fontSize: 12, fontWeight: 600 }}>✨ {stats.new_this_search} חדשים</span>
          {(stats.already_known || 0) > 0 && <span style={{ background: '#fef3c7', color: '#92400e', borderRadius: 20, padding: '4px 14px', fontSize: 12 }}>🔁 {stats.already_known} כבר נראו</span>}
          <span style={{ background: '#f3f4f6', color: '#374151', borderRadius: 20, padding: '4px 14px', fontSize: 12 }}>סה"כ {results.length}</span>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div style={{ marginTop: 16 }}>
          {/* Bulk actions */}
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14, flexWrap: 'wrap' }}>
            <button onClick={selectHot}
              style={{ fontSize: 13, fontWeight: 600, padding: '6px 14px', borderRadius: 8, border: '1.5px solid #f97316', cursor: 'pointer', background: '#fff7ed', color: '#c2410c' }}>
              🔥 בחר לידים חמים
            </button>
            <button onClick={selectAll} style={{ fontSize: 12, padding: '6px 12px', borderRadius: 8, border: '1px solid #e5e7eb', cursor: 'pointer', background: 'white' }}>בחר הכל</button>
            <button onClick={clearAll} style={{ fontSize: 12, padding: '6px 12px', borderRadius: 8, border: '1px solid #e5e7eb', cursor: 'pointer', background: 'white' }}>נקה</button>
            <span style={{ fontSize: 12, color: '#6b7280' }}>{selected.size} נבחרו</span>
            {selected.size > 0 && (
              <>
                <button onClick={handleImport} disabled={importing}
                  style={{ background: importing ? '#9ca3af' : '#10b981', color: 'white', border: 'none', borderRadius: 8, padding: '7px 18px', fontSize: 14, fontWeight: 700, cursor: importing ? 'not-allowed' : 'pointer' }}>
                  {importing ? '⏳ מייבא...' : `📥 ייבא ${selected.size} לידים`}
                </button>
                <button onClick={handleCreateDemos} disabled={creatingDemos}
                  style={{ background: creatingDemos ? '#9ca3af' : '#7c3aed', color: 'white', border: 'none', borderRadius: 8, padding: '7px 18px', fontSize: 14, fontWeight: 700, cursor: creatingDemos ? 'not-allowed' : 'pointer', boxShadow: '0 4px 12px rgba(124,58,237,0.35)' }}>
                  {creatingDemos ? '⏳ יוצר...' : `🎬 צור ${selected.size} אתרי דמו`}
                </button>
              </>
            )}
            {importMsg && <span style={{ fontSize: 13, color: importMsg.startsWith('✅') ? '#065f46' : '#991b1b', fontWeight: 600 }}>{importMsg}</span>}
          </div>

          {/* Cards grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 14 }}>
            {results.map((biz, i) => {
              const isSelected = biz.place_id ? selected.has(biz.place_id) : false;
              const hot = isHotLead(biz);
              const noSite = !biz.website;
              const cardBorder = isSelected ? '#6366f1' : hot ? '#f97316' : noSite ? '#c084fc' : '#e5e7eb';
              const cardBg = isSelected ? '#eef2ff' : hot ? '#fff7ed' : noSite ? '#fdf4ff' : 'white';

              return (
                <div key={biz.place_id || i}
                  onClick={() => biz.place_id && toggleSelect(biz.place_id)}
                  style={{ border: `2px solid ${cardBorder}`, borderRadius: 12, padding: 14, background: cardBg, cursor: 'pointer', transition: 'border-color 0.15s, background 0.15s', position: 'relative' }}>

                  {/* Hot lead ribbon */}
                  {hot && !isSelected && (
                    <div style={{ position: 'absolute', top: -1, right: -1, background: '#f97316', color: 'white', borderRadius: '0 10px 0 10px', padding: '3px 10px', fontSize: 11, fontWeight: 700 }}>
                      🔥 ליד חם
                    </div>
                  )}
                  {noSite && !hot && !isSelected && (
                    <div style={{ position: 'absolute', top: -1, right: -1, background: '#a855f7', color: 'white', borderRadius: '0 10px 0 10px', padding: '3px 10px', fontSize: 11, fontWeight: 700 }}>
                      🎯 ללא אתר
                    </div>
                  )}

                  {/* Name + address */}
                  <div style={{ marginBottom: 8, paddingTop: hot || noSite ? 10 : 0 }}>
                    <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 2 }}>{biz.name}</div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>{biz.address}</div>
                  </div>

                  {/* Opportunity bar */}
                  <OpportunityBar score={biz.lead_opportunity_score || 0} />

                  {/* Badges row */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 8 }}>
                    <CacheStatusBadge status={biz.cache_status} />
                    {biz.phone && (
                      <span style={{ background: '#f0fdf4', color: '#15803d', borderRadius: 8, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>
                        📞 {biz.phone}
                      </span>
                    )}
                    {(biz.reviews_count || 0) > 0 && (
                      <span style={{ background: '#fffbeb', color: '#92400e', borderRadius: 8, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>
                        ⭐ {biz.rating} · {biz.reviews_count?.toLocaleString()} ביקורות
                      </span>
                    )}
                    {biz.website && (
                      <span style={{ background: '#f3f4f6', color: '#9ca3af', borderRadius: 8, padding: '2px 8px', fontSize: 11 }}>
                        🌐 יש אתר
                      </span>
                    )}
                  </div>

                  {/* Types */}
                  {biz.types?.length > 0 && (
                    <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 6 }}>
                      {biz.types.slice(0, 3).join(' · ')}
                    </div>
                  )}

                  {/* Top review */}
                  {biz.top_review && (
                    <div style={{ fontSize: 11, color: '#6b7280', background: '#f9fafb', borderRadius: 8, padding: '6px 8px', marginBottom: 6, fontStyle: 'italic', lineHeight: 1.4 }}>
                      "{biz.top_review.slice(0, 130)}{biz.top_review.length > 130 ? '...' : ''}"
                    </div>
                  )}

                  {/* Links */}
                  <div style={{ display: 'flex', gap: 10, marginTop: 6 }}>
                    {biz.google_maps_url && (
                      <a href={biz.google_maps_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                        style={{ fontSize: 12, color: '#6366f1', textDecoration: 'none', fontWeight: 500 }}>🗺️ Google Maps</a>
                    )}
                    {biz.facebook_url && (
                      <a href={biz.facebook_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                        style={{ fontSize: 12, color: '#1d4ed8', textDecoration: 'none' }}>📘 FB</a>
                    )}
                    {biz.instagram_url && (
                      <a href={biz.instagram_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                        style={{ fontSize: 12, color: '#e1306c', textDecoration: 'none' }}>📷 IG</a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!loading && results.length === 0 && stats !== null && (
        <Card>
          <p style={{ textAlign: 'center', color: '#9ca3af', padding: 24 }}>
            לא נמצאו עסקים לפי הסינון. נסה להוריד את מינימום הביקורות או הדירוג.
          </p>
        </Card>
      )}
    </div>
  );
}
