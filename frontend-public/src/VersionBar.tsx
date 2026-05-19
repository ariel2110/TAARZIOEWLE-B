// Version bar — stamped at build time via VITE_* env vars
const BUILD_TIME = import.meta.env.VITE_BUILD_TIME || ''
const GIT_HASH   = import.meta.env.VITE_GIT_HASH   || ''
const GIT_MSG    = import.meta.env.VITE_GIT_MSG    || ''

export default function VersionBar() {
  if (!BUILD_TIME) return null
  return (
    <div style={{
      borderTop: '1px solid rgba(255,255,255,0.06)',
      background: 'rgba(0,0,0,0.4)',
      padding: '10px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 10,
      flexWrap: 'wrap' as const,
      direction: 'rtl',
      fontFamily: "'Heebo',sans-serif",
    }}>
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', letterSpacing: '0.3px' }}>
        🚀 גרסה פעילה
      </span>
      <span style={{ width: 1, height: 12, background: 'rgba(255,255,255,0.1)', display: 'inline-block' }} />
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
        {BUILD_TIME}
      </span>
      {GIT_HASH && <>
        <span style={{ width: 1, height: 12, background: 'rgba(255,255,255,0.1)', display: 'inline-block' }} />
        <span style={{ fontSize: 11, color: 'rgba(255,107,0,0.55)', fontFamily: 'monospace' }}>
          #{GIT_HASH}
        </span>
      </>}
      {GIT_MSG && <>
        <span style={{ width: 1, height: 12, background: 'rgba(255,255,255,0.1)', display: 'inline-block' }} />
        <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const }}>
          {GIT_MSG}
        </span>
      </>}
    </div>
  )
}
