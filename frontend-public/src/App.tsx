import { useState } from 'react';
import Sidebar from './Sidebar'
import Marketplace from './Marketplace';
import MagicPortal from './MagicPortal';
import LandingExtra from './LandingExtra';
import IntakeForm from './IntakeForm';
import SubmissionStatus from './SubmissionStatus';
import PageGuide from './PageGuide';
import './styles.css';

export type AppPage = 'marketplace' | 'home' | 'intake' | 'status';

export default function App() {
  const [page, setPage] = useState<AppPage>(() => {
    if (window.location.hash.startsWith('#/status/')) return 'status';
    if (window.location.hash === '#/start') return 'intake';
    if (window.location.hash === '#/business') return 'home';
    return 'marketplace';
  });
  const [statusToken, setStatusToken] = useState<string>(() => {
    const hash = window.location.hash;
    if (hash.startsWith('#/status/')) return hash.replace('#/status/', '');
    return '';
  });
  const [selectedPlan, setSelectedPlan] = useState<string | undefined>(undefined);

  function goToIntake(planName?: string) {
    window.location.hash = '#/start';
    setSelectedPlan(planName);
    setPage('intake');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goToStatus(token: string) {
    window.location.hash = `#/status/${token}`;
    setStatusToken(token);
    setPage('status');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goHome() {
    window.location.hash = '';
    setPage('marketplace');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goToBusinessLanding() {
    window.location.hash = '#/business';
    setPage('home');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function handleGoTo(target: AppPage, planName?: string) {
    if (target === 'home') goToBusinessLanding();
    else if (target === 'intake') goToIntake(planName);
    else if (target === 'marketplace') goHome();
  }

  if (page === 'status') {
    return (
      <>
        <Sidebar currentPage={page} onGoTo={handleGoTo} />
        <SubmissionStatus token={statusToken} onBack={goHome} selectedPlan={selectedPlan} />
        <PageGuide page={page} onGoTo={handleGoTo} />
      </>
    );
  }

  if (page === 'intake') {
    return (
      <>
        <Sidebar currentPage={page} onGoTo={handleGoTo} />
        <IntakeForm onSubmitted={goToStatus} onBack={goHome} selectedPlan={selectedPlan} />
        <PageGuide page={page} onGoTo={handleGoTo} />
      </>
    );
  }

  if (page === 'home') {
    return (
      <>
        <Sidebar currentPage={page} onGoTo={handleGoTo} />
        <MagicPortal />
        <LandingExtra onStartIntake={goToIntake} />
        <PageGuide page={page} onGoTo={handleGoTo} />
      </>
    );
  }

  // Default: Marketplace
  return (
    <>
      <Sidebar currentPage={page} onGoTo={handleGoTo} />
      <Marketplace onJoin={goToBusinessLanding} />
      <PageGuide page={page} onGoTo={handleGoTo} />
    </>
  );
}
