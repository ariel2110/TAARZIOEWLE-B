import React, { useState } from 'react';
import type { AppPage } from './App';

interface Props {
  page: AppPage;
  onGoTo: (page: AppPage, planName?: string) => void;
}

const TOTAL = 4;
const STEP_LABELS = ['\u05d2\u05dc\u05d9\u05d9\u05d4', '\u05ea\u05d5\u05db\u05e0\u05d9\u05d5\u05ea', '\u05d4\u05e8\u05e9\u05de\u05d4', '\u05e4\u05e2\u05d9\u05dc \ud83d\ude80'];

interface Config {
  step: number;
  icon: string;
  title: string;
  description: string;
  nextLabel?: string;
  nextPage?: AppPage;
}

const CONFIGS: Record<AppPage, Config> = {
  marketplace: {
    step: 1, icon: '\ud83d\udecd\ufe0f',
    title: '\u05e9\u05dc\u05d1 1: \u05d2\u05dc\u05d4 \u05e9\u05d9\u05e8\u05d5\u05ea\u05d9\u05dd \u05e7\u05e8\u05d5\u05d1\u05d9\u05dd \u05d0\u05dc\u05d9\u05da',
    description: '\u05e2\u05d9\u05d9\u05df \u05d1\u05e7\u05d8\u05d2\u05d5\u05e8\u05d9\u05d5\u05ea \u05d5\u05de\u05e6\u05d0 \u05e2\u05e1\u05e7\u05d9\u05dd \u05de\u05e7\u05d5\u05de\u05d9\u05d9\u05dd. \u05e8\u05d5\u05e6\u05d4 \u05d0\u05ea\u05e8 \u05de\u05e7\u05e6\u05d5\u05e2\u05d9 \u05dc\u05e2\u05e1\u05e7 \u05e9\u05dc\u05da? \u05dc\u05d7\u05e5 \u05e2\u05dc \u05d4\u05db\u05e4\u05ea\u05d5\u05e8 \u05de\u05d9\u05de\u05d9\u05df.',
    nextLabel: '\u05e8\u05d5\u05e6\u05d4 \u05d0\u05ea\u05e8 \u05dc\u05e2\u05e1\u05e7 \u05e9\u05dc\u05da? \u2190',
    nextPage: 'home',
  },
  home: {
    step: 2, icon: '\ud83d\udccb',
    title: '\u05e9\u05dc\u05d1 2: \u05d1\u05d7\u05e8 \u05ea\u05d5\u05db\u05e0\u05d9\u05ea \u05dc\u05e2\u05e1\u05e7 \u05e9\u05dc\u05da',
    description: '\u05db\u05dc \u05ea\u05d5\u05db\u05e0\u05d9\u05ea \u05db\u05d5\u05dc\u05dc\u05ea \u05d0\u05ea\u05e8 \u05de\u05e7\u05e6\u05d5\u05e2\u05d9, SSL, \u05d3\u05d5\u05de\u05d9\u05d9\u05df \u05d5\u05ea\u05de\u05d9\u05db\u05d4. AI \u05d1\u05d5\u05e0\u05d4 \u05d0\u05ea \u05d4\u05d0\u05ea\u05e8 \u05ea\u05d5\u05da 48 \u05e9\u05e2\u05d5\u05ea. \u05e0\u05d9\u05ea\u05df \u05dc\u05e9\u05d3\u05e8\u05d2 \u05d1\u05db\u05dc \u05e2\u05ea.',
    nextLabel: '\u05d1\u05d7\u05e8 \u05ea\u05d5\u05db\u05e0\u05d9\u05ea \u05d5\u05d4\u05ea\u05d7\u05dc \u2190',
    nextPage: 'intake',
  },
  intake: {
    step: 3, icon: '\u270d\ufe0f',
    title: '\u05e9\u05dc\u05d1 3: \u05e1\u05e4\u05e8 \u05dc\u05e0\u05d5 \u05e2\u05dc \u05d4\u05e2\u05e1\u05e7 \u05e9\u05dc\u05da',
    description: '\u05de\u05dc\u05d0 \u05e9\u05dd \u05e2\u05e1\u05e7, \u05d8\u05dc\u05e4\u05d5\u05df, \u05ea\u05d7\u05d5\u05dd \u05e2\u05d9\u05e1\u05d5\u05e7 \u05d5\u05db\u05de\u05d4 \u05ea\u05de\u05d5\u05e0\u05d5\u05ea. AI \u05d9\u05e0\u05ea\u05d7 \u05d5\u05d9\u05d1\u05e0\u05d4 \u05d0\u05ea\u05e8 \u05de\u05e7\u05e6\u05d5\u05e2\u05d9 \u05d5\u05de\u05d5\u05ea\u05d0\u05dd \u05d0\u05d9\u05e9\u05d9\u05ea \u05ea\u05d5\u05da 48 \u05e9\u05e2\u05d5\u05ea.',
  },
  status: {
    step: 4, icon: '\ud83c\udf89',
    title: '\u05e9\u05dc\u05d1 4: \u05d4\u05d0\u05ea\u05e8 \u05d1\u05d3\u05e8\u05da!',
    description: '\u05e7\u05d9\u05d1\u05dc\u05e0\u05d5 \u05d0\u05ea \u05d4\u05e4\u05e8\u05d8\u05d9\u05dd! \u05d4\u05e6\u05d5\u05d5\u05ea \u05e9\u05dc\u05e0\u05d5 + AI \u05e2\u05d5\u05d1\u05d3\u05d9\u05dd \u05e2\u05dc \u05d4\u05d0\u05ea\u05e8. \u05ea\u05e7\u05d1\u05dc \u05d4\u05d5\u05d3\u05e2\u05d4 \u05d1\u05d5\u05d5\u05d0\u05d8\u05e1\u05d0\u05e4 \u05db\u05e9\u05d4\u05d0\u05ea\u05e8 \u05de\u05d5\u05db\u05df \u05dc\u05d0\u05d9\u05e9\u05d5\u05e8\u05da.',
  },
};

export default function PageGuide({ page, onGoTo }: Props) {
  const storageKey = 'pg_v2_' + page;
  const [dismissed, setDismissed] = useState<boolean>(() => localStorage.getItem(storageKey) === '1');
  const [expanded, setExpanded] = useState<boolean>(true);

  if (dismissed) return null;

  const cfg = CONFIGS[page];

  const dismiss = (e: React.MouseEvent) => {
    e.stopPropagation();
    localStorage.setItem(storageKey, '1');
    setDismissed(true);
  };

  return (
    <div dir="rtl" style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 9999,
      fontFamily: 'system-ui,-apple-system,"Segoe UI",Arial,sans-serif',
      boxShadow: '0 -4px 24px rgba(0,0,0,0.18)',
    }}>
      <div
        onClick={() => setExpanded(v => !v)}
        style={{ background: '#4f46e5', padding: '8px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', userSelect: 'none' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          {Array.from({ length: TOTAL }, (_, i) => i + 1).map(s => (
            <React.Fragment key={s}>
              <div style={{
                width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, fontWeight: 700,
                background: s < cfg.step ? '#4ade80' : s === cfg.step ? '#fff' : 'rgba(255,255,255,0.2)',
                color: s < cfg.step ? '#166534' : s === cfg.step ? '#4f46e5' : 'rgba(255,255,255,0.55)',
                boxShadow: s === cfg.step ? '0 0 0 3px rgba(255,255,255,0.3)' : 'none',
                transform: s === cfg.step ? 'scale(1.1)' : 'scale(1)',
              }}>
                {s < cfg.step ? '\u2713' : s}
              </div>
              {s < TOTAL && (
                <div style={{ width: 20, height: 2, flexShrink: 0, background: s < cfg.step ? '#4ade80' : 'rgba(255,255,255,0.25)' }} />
              )}
            </React.Fragment>
          ))}
          <span style={{ color: 'rgba(255,255,255,0.95)', fontSize: 12, fontWeight: 600, marginRight: 10, flexShrink: 0 }}>
            {cfg.icon} {STEP_LABELS[cfg.step - 1]}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
          <button onClick={dismiss} title="\u05e1\u05d2\u05d5\u05e8" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.65)', fontSize: 16, padding: '0 4px', lineHeight: 1 }}>
            \u2715
          </button>
          <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13 }}>{expanded ? '\u25bc' : '\u25b2'}</span>
        </div>
      </div>

      {expanded && (
        <div style={{ background: '#fff', borderTop: '2px solid #c7d2fe', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#1e1b4b', marginBottom: 4 }}>{cfg.title}</div>
            <div style={{ fontSize: 12, color: '#4b5563', lineHeight: 1.6 }}>{cfg.description}</div>
          </div>
          {cfg.nextLabel && cfg.nextPage && (
            <button
              onClick={() => onGoTo(cfg.nextPage!)}
              style={{ background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 24, padding: '9px 20px', fontSize: 13, fontWeight: 600, cursor: 'pointer', flexShrink: 0, whiteSpace: 'nowrap' }}
            >
              {cfg.nextLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
