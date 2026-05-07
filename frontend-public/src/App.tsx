import { useState } from 'react';
import MagicPortal from './MagicPortal';
import LandingExtra from './LandingExtra';
import IntakeForm from './IntakeForm';
import SubmissionStatus from './SubmissionStatus';
import './styles.css';

export type AppPage = 'home' | 'intake' | 'status';

export default function App() {
  const [page, setPage] = useState<AppPage>(() => {
    if (window.location.hash.startsWith('#/status/')) return 'status';
    if (window.location.hash === '#/start') return 'intake';
    return 'home';
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
    setPage('home');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (page === 'status') {
    return <SubmissionStatus token={statusToken} onBack={goHome} selectedPlan={selectedPlan} />;
  }

  if (page === 'intake') {
    return <IntakeForm onSubmitted={goToStatus} onBack={goHome} selectedPlan={selectedPlan} />;
  }

  return (
    <>
      <MagicPortal />
      <LandingExtra onStartIntake={goToIntake} />
    </>
  );
}
