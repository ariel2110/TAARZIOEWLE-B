import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { LangProvider, ThemeProvider } from './i18n';
import App from './App';
import { ScrollToTop } from './components/ScrollToTop';
import './styles/tazo-tokens.css';
import './styles.css';

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '';
if (!googleClientId) {
  // eslint-disable-next-line no-console
  console.warn('[admin] VITE_GOOGLE_CLIENT_ID is not set — Google OAuth login will be disabled.');
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={googleClientId}>
      <LangProvider>
        <ThemeProvider>
          <BrowserRouter>
            <ScrollToTop />
            <App />
          </BrowserRouter>
        </ThemeProvider>
      </LangProvider>
    </GoogleOAuthProvider>
  </React.StrictMode>
);
