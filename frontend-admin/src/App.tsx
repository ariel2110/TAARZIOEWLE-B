
import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Shell } from './components/Shell';
import LoginPage from './pages/Login';

const OverviewPage        = lazy(() => import('./pages/Overview'));
const LeadsPage           = lazy(() => import('./pages/Leads'));
const BusinessesPage      = lazy(() => import('./pages/Businesses'));
const QueuesPage          = lazy(() => import('./pages/Queues'));
const ApprovalsPage       = lazy(() => import('./pages/Approvals'));
const TargetingPage       = lazy(() => import('./pages/Targeting'));
const CEOConsolePage      = lazy(() => import('./pages/CEOConsole'));
const FeedbackPage        = lazy(() => import('./pages/Feedback'));
const SecurityMonitoring  = lazy(() => import('./pages/SecurityMonitoring'));
const CustomersPage       = lazy(() => import('./pages/Customers'));
const DraftSitesPage      = lazy(() => import('./pages/DraftSites'));
const PaymentsPage        = lazy(() => import('./pages/Payments'));
const EnrichPage          = lazy(() => import('./pages/Enrich'));
const DemosPage           = lazy(() => import('./pages/Demos'));
const DemoSitePage        = lazy(() => import('./pages/DemoSite'));
const WhatsAppPage        = lazy(() => import('./pages/WhatsApp'));
const AgentsDashboard     = lazy(() => import('./pages/AgentsDashboard'));
const DomainApprovalsPage = lazy(() => import('./pages/DomainApprovals'));

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('admin_access_token');
  if (!token) return <LoginPage />;
  return <>{children}</>;
}

export default function App() {
  return (
    <Suspense fallback={<div style={{ padding: 32 }}>Loading…</div>}>
      <Routes>
        <Route path="/demo/:slug" element={<DemoSitePage />} />
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/*" element={
          <RequireAuth>
            <Shell>
              <Routes>
                <Route index element={<OverviewPage />} />
                <Route path="leads" element={<LeadsPage />} />
                <Route path="businesses" element={<BusinessesPage />} />
                <Route path="enrich" element={<EnrichPage />} />
                <Route path="demos" element={<DemosPage />} />
                <Route path="draft-sites" element={<DraftSitesPage />} />
                <Route path="queues" element={<QueuesPage />} />
                <Route path="approvals" element={<ApprovalsPage />} />
                <Route path="payments" element={<PaymentsPage />} />
                <Route path="targeting" element={<TargetingPage />} />
                <Route path="customers" element={<CustomersPage />} />
                <Route path="ceo" element={<CEOConsolePage />} />
                <Route path="feedback" element={<FeedbackPage />} />
                <Route path="security" element={<SecurityMonitoring />} />
                <Route path="whatsapp" element={<WhatsAppPage />} />
                <Route path="agents" element={<AgentsDashboard />} />
                <Route path="domain-approvals" element={<DomainApprovalsPage />} />
              </Routes>
            </Shell>
          </RequireAuth>
        } />
      </Routes>
    </Suspense>
  );
}

