
import React from 'react';

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
