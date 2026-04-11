
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Shell } from './components/Shell';
import OverviewPage from './pages/Overview';
import LeadsPage from './pages/Leads';
import BusinessesPage from './pages/Businesses';
import QueuesPage from './pages/Queues';
import ApprovalsPage from './pages/Approvals';
import TargetingPage from './pages/Targeting';
import CEOConsolePage from './pages/CEOConsole';
import FeedbackPage from './pages/Feedback';
import SecurityMonitoring from './pages/SecurityMonitoring';
import CustomersPage from './pages/Customers';
import DraftSitesPage from './pages/DraftSites';
import PaymentsPage from './pages/Payments';
import LoginPage from './pages/Login';
import { useEffect, useState } from 'react';
import { ensureDevLogin } from './services/queries';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('admin_access_token');
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Auto dev-login if no token present (dev mode)
    const token = localStorage.getItem('admin_access_token');
    if (!token) {
      ensureDevLogin().finally(() => setReady(true));
    } else {
      setReady(true);
    }
  }, []);

  if (!ready) return <div style={{ padding: 40, fontFamily: 'Arial' }}>Loading...</div>;

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/*" element={
          <RequireAuth>
            <Shell>
              <Routes>
                <Route index element={<OverviewPage />} />
                <Route path="leads" element={<LeadsPage />} />
                <Route path="businesses" element={<BusinessesPage />} />
                <Route path="draft-sites" element={<DraftSitesPage />} />
                <Route path="queues" element={<QueuesPage />} />
                <Route path="approvals" element={<ApprovalsPage />} />
                <Route path="payments" element={<PaymentsPage />} />
                <Route path="targeting" element={<TargetingPage />} />
                <Route path="customers" element={<CustomersPage />} />
                <Route path="ceo" element={<CEOConsolePage />} />
                <Route path="feedback" element={<FeedbackPage />} />
                <Route path="security" element={<SecurityMonitoring />} />
              </Routes>
            </Shell>
          </RequireAuth>
        } />
      </Routes>
    </BrowserRouter>
  );
}

