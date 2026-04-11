
import { NavLink } from 'react-router-dom';

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>LocalBiz Admin v24</h1>
        <p className="muted">Operational control room with queues, approvals, targeting, CEO oversight, feedback intelligence, and queue actions.</p>
        <nav className="nav">
          <NavLink to="/" end className={({isActive}) => isActive ? 'active' : ''}>Overview</NavLink>
          <NavLink to="/leads" className={({isActive}) => isActive ? 'active' : ''}>Leads</NavLink>
          <NavLink to="/businesses" className={({isActive}) => isActive ? 'active' : ''}>Businesses</NavLink>
          <NavLink to="/queues" className={({isActive}) => isActive ? 'active' : ''}>Queues</NavLink>
          <NavLink to="/approvals" className={({isActive}) => isActive ? 'active' : ''}>Approvals</NavLink>
          <NavLink to="/targeting" className={({isActive}) => isActive ? 'active' : ''}>Targeting</NavLink>
          <NavLink to="/ceo" className={({isActive}) => isActive ? 'active' : ''}>CEO Console</NavLink>
          <NavLink to="/feedback" className={({isActive}) => isActive ? 'active' : ''}>Feedback</NavLink>
          <NavLink to="/security" className={({isActive}) => isActive ? 'active' : ''}>Security</NavLink>
        </nav>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
