import { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { LandingPage } from './pages/LandingPage';
import { ScreeningFlowPage } from './pages/ScreeningFlowPage';
import { ResultsPage } from './pages/ResultsPage';
import { EyewearPage } from './pages/EyewearPage';
import { ShopDashboardPage } from './pages/ShopDashboardPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { LegalPages } from './pages/LegalPages';
import { LanguageProvider } from './localization/useLanguage';
import { checkBackendHealth } from './services/apiClient';
import { getCurrentUser, setCurrentUser, getActiveSession } from './services/storage';
import { ScreeningSession, UserProfile, CustomerRecord, UserRole } from '@optiguide/shared';

export default function App() {
  const [currentRoute, setCurrentRoute] = useState<string>('home');
  const [currentUser, setCurrentUserState] = useState<UserProfile | null>(getCurrentUser());
  const [activeSession, setActiveSession] = useState<ScreeningSession | null>(getActiveSession());
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [screeningCustomer, setScreeningCustomer] = useState<CustomerRecord | null>(null);

  // Poll backend health once on mount
  useEffect(() => {
    checkBackendHealth().then((status) => {
      setBackendOnline(status.online);
    });
  }, []);

  // Handle role switching from navbar
  const handleSelectRole = (role: UserRole) => {
    const updated: UserProfile = {
      id: `usr-${role}`,
      email: `${role}@optiguide.local`,
      fullName:
        role === 'shopkeeper'
          ? 'Rameshwar Mohapatra'
          : role === 'admin'
          ? 'State Admin Officer'
          : role === 'optometrist'
          ? 'Dr. S. K. Patnaik, MS'
          : role === 'individual'
          ? 'Anandita Panda'
          : 'Guest Citizen',
      role,
      preferredLanguage: 'en',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setCurrentUser(updated);
    setCurrentUserState(updated);

    if (role === 'shopkeeper') {
      setCurrentRoute('shop-dashboard');
    } else if (role === 'admin') {
      setCurrentRoute('admin-dashboard');
    }
  };

  // Start screening for a specific customer from the shopkeeper kiosk
  const handleStartScreeningForCustomer = (customer: CustomerRecord) => {
    setScreeningCustomer(customer);
    setCurrentRoute('screening');
  };

  // When a screening finishes
  const handleScreeningComplete = (session: ScreeningSession) => {
    setActiveSession(session);
    setScreeningCustomer(null);
    setCurrentRoute('results');
  };

  return (
    <LanguageProvider>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: '#F7F4EC' }}>
        <Navbar
          currentRoute={currentRoute}
          onNavigate={(route) => {
            setCurrentRoute(route);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
          currentUser={currentUser}
          onSelectRole={handleSelectRole}
          backendOnline={backendOnline}
        />

        <main style={{ flex: 1 }}>
          {currentRoute === 'home' && (
            <LandingPage
              onNavigate={(route) => {
                setCurrentRoute(route);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
          )}

          {currentRoute === 'screening' && (
            <ScreeningFlowPage
              onComplete={handleScreeningComplete}
              onCancel={() => setCurrentRoute('home')}
              customerName={screeningCustomer?.fullName}
              customerPhone={screeningCustomer?.phoneNumber}
            />
          )}

          {currentRoute === 'results' && activeSession && (
            <ResultsPage
              session={activeSession}
              onExploreEyewear={() => setCurrentRoute('eyewear')}
              onNewScreening={() => setCurrentRoute('screening')}
              onGoHome={() => setCurrentRoute('home')}
            />
          )}

          {currentRoute === 'eyewear' && (
            <EyewearPage session={activeSession} />
          )}

          {currentRoute === 'shop-dashboard' && (
            <ShopDashboardPage
              onStartScreeningForCustomer={handleStartScreeningForCustomer}
              onViewReport={(session) => {
                setActiveSession(session);
                setCurrentRoute('results');
              }}
            />
          )}

          {currentRoute === 'admin-dashboard' && <AdminDashboardPage />}

          {(currentRoute === 'privacy-policy' ||
            currentRoute === 'terms-of-service' ||
            currentRoute === 'disclaimer' ||
            currentRoute === 'about' ||
            currentRoute === 'contact' ||
            currentRoute === 'how-it-works' ||
            currentRoute === 'for-shops') && (
            <LegalPages
              page={
                currentRoute === 'privacy-policy'
                  ? 'privacy'
                  : currentRoute === 'terms-of-service'
                  ? 'terms'
                  : (currentRoute as any)
              }
              onNavigate={(route) => {
                setCurrentRoute(route);
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
            />
          )}
        </main>

        <Footer
          onNavigate={(route) => {
            setCurrentRoute(route);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
        />
      </div>
    </LanguageProvider>
  );
}
