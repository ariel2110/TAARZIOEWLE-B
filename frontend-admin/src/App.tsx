
import { Routes, Route, Navigate } from 'react-router-dom';
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
import EnrichPage from './pages/Enrich';
import DemosPage from './pages/Demos';
import DemoSitePage from './pages/DemoSite';
import WhatsAppPage from './pages/WhatsApp';
import AgentsDashboard from './pages/AgentsDashboard';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('admin_access_token');
  if (!token) return <LoginPage />;
  return <>{children}</>;
}

export default function App() {
  return (
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
            </Routes>
          </Shell>
        </RequireAuth>
      } />
    </Routes>
  );
}

