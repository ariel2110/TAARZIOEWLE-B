
import React, { useState, useRef } from 'react';

// ── Tooltip ──────────────────────────────────────────────────────────────────
export function Tooltip({ text, children, position = 'top' }: {
  text: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'right' | 'left';
}) {
  const [visible, setVisible] = useState(false);
  const posStyle: React.CSSProperties =
    position === 'top' ? { bottom: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)' } :
      position === 'bottom' ? { top: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)' } :
        position === 'right' ? { top: '50%', left: 'calc(100% + 8px)', transform: 'translateY(-50%)' } :
          { top: '50%', right: 'calc(100% + 8px)', transform: 'translateY(-50%)' };

  const arrowStyle: React.CSSProperties =
    position === 'top' ? { top: '100%', left: '50%', transform: 'translateX(-50%)', borderTop: '6px solid #1f2937', borderLeft: '5px solid transparent', borderRight: '5px solid transparent' } :
      position === 'bottom' ? { bottom: '100%', left: '50%', transform: 'translateX(-50%)', borderBottom: '6px solid #1f2937', borderLeft: '5px solid transparent', borderRight: '5px solid transparent' } :
        position === 'right' ? { top: '50%', right: '100%', transform: 'translateY(-50%)', borderRight: '6px solid #1f2937', borderTop: '5px solid transparent', borderBottom: '5px solid transparent' } :
          { top: '50%', left: '100%', transform: 'translateY(-50%)', borderLeft: '6px solid #1f2937', borderTop: '5px solid transparent', borderBottom: '5px solid transparent' };

  return (
    <span
      style={{ position: 'relative', display: 'block' }}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <span style={{
          position: 'absolute',
          ...posStyle,
          background: '#1f2937',
          color: '#f9fafb',
          borderRadius: 8,
          padding: '6px 11px',
          fontSize: 12,
          fontWeight: 400,
          lineHeight: 1.5,
          maxWidth: 220,
          whiteSpace: 'normal' as any,
          zIndex: 9999,
          boxShadow: '0 4px 16px rgba(0,0,0,0.22)',
          pointerEvents: 'none',
          textAlign: 'center',
          direction: 'rtl',
        }}>
          {text}
          <span style={{ position: 'absolute', width: 0, height: 0, ...arrowStyle }} />
        </span>
      )}
    </span>
  );
}

// ── InfoTip ──────────────────────────────────────────────────────────────────
// Small ℹ icon with hover tooltip — attach next to section titles / labels
export function InfoTip({ text, position = 'top' }: { text: string; position?: 'top' | 'bottom' | 'right' | 'left' }) {
  return (
    <Tooltip text={text} position={position}>
      <span style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        width: 17, height: 17, borderRadius: '50%',
        background: '#e5e7eb', color: '#6b7280',
        fontSize: 11, fontWeight: 700,
        cursor: 'default', userSelect: 'none',
        marginInlineStart: 6, verticalAlign: 'middle',
      }}>i</span>
    </Tooltip>
  );
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="section-title">{children}</h2>;
}

export function Card({ children, dark = false }: { children: React.ReactNode; dark?: boolean }) {
  return (
    <div className="card" style={dark ? { background: '#111827', color: '#fff' } : undefined}>
      {children}
    </div>
  );
}

export function Button({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props}>{children}</button>;
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} />;
}
