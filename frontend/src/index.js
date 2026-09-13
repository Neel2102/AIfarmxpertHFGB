import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import './index.css';
import App from './App';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
        }}
      >
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: 'var(--dash-card-bg)',
              backdropFilter: 'var(--dash-backdrop-blur-deep)',
              WebkitBackdropFilter: 'var(--dash-backdrop-blur-deep)',
              border: '1px solid var(--dash-card-border)',
              borderRadius: '18px',
              boxShadow: 'var(--dash-card-shadow-hover)',
              color: 'var(--dash-text-heading)',
            },
            success: {
              iconTheme: {
                primary: 'var(--dash-emerald)',
                secondary: 'var(--dash-card-bg-elevated)',
              },
              style: {
                background: 'var(--dash-card-bg)',
                backdropFilter: 'blur(32px) saturate(220%)',
                WebkitBackdropFilter: 'blur(32px) saturate(220%)',
                border: '1px solid var(--dash-card-border-hover)',
                boxShadow: 'var(--dash-card-shadow-hover), 0 0 24px var(--dash-glow-subtle)',
                color: 'var(--dash-text-heading)',
              },
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://cra.link/PWA
serviceWorkerRegistration.register();

