import { useState } from 'react';
import Sidebar from './Sidebar'
import Marketplace from './Marketplace';
import MagicPortal from './MagicPortal';
import LandingExtra from './LandingExtra';
import IntakeForm from './IntakeForm';
import SubmissionStatus from './SubmissionStatus';
import PageGuide from './PageGuide';
import TazoWebInstallBanner from './TazoWebInstallBanner';
import About from './About';
import './styles.css';

export type AppPage = 'marketplace' | 'home' | 'intake' | 'status' | 'about';

export default function App() {
  const [page, setPage] = useState<AppPage>(() => {
    if (window.location.hash.startsWith('#/status/')) return 'status';
    if (window.location.hash === '#/start') return 'intake';
    if (window.location.hash === '#/business') return 'home';
    if (window.location.hash === '#/about') return 'about';
    return 'marketplace';
  });
  const [statusToken, setStatusToken] = useState<string>(() => {
    const hash = window.location.hash;
    if (hash.startsWith('#/status/')) return hash.replace('#/status/', '');
    return '';
  });
  const [selectedPlan, setSelectedPlan] = useState<string | undefined>(undefined);
  const [jumpCategory, setJumpCategory] = useState<string | undefined>(() => {
    const m = window.location.hash.match(/^#\/category\/([^/]+)/);
    return m ? m[1] : undefined;
  });

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

  function handleGoTo(target: AppPage, categoryId?: string) {
    if (target === 'marketplace') {
      if (categoryId) {
        window.location.hash = `#/category/${categoryId}`;
        setJumpCategory(categoryId);
      } else {
        window.location.hash = '';
        setJumpCategory(undefined);
      }
      setPage('marketplace');
    } else if (target === 'home') goToBusinessLanding();
    else if (target === 'intake') goToIntake(categoryId);
    else if (target === 'about') { window.location.hash = '#/about'; setPage('about'); }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  if (page === 'about') {
    return (
      <>
        <Sidebar currentPage={page} onGoTo={handleGoTo} />
        <About />
      </>
    );
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
      <TazoWebInstallBanner />
      <Sidebar currentPage={page} onGoTo={handleGoTo} />
      <Marketplace onJoin={goToBusinessLanding} jumpCategory={jumpCategory} onClearJumpCategory={() => setJumpCategory(undefined)} />
      <PageGuide page={page} onGoTo={handleGoTo} />
    </>
  );
}
