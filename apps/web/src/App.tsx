import { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { LandingPage } from './pages/LandingPage';
import { ScreeningFlowPage } from './pages/ScreeningFlowPage';
import { ResultsPage } from './pages/ResultsPage';
import { EyewearPage } from './pages/EyewearPage';
import { VirtualTryOnPage } from './pages/VirtualTryOnPage';
import { ShopDashboardPage } from './pages/ShopDashboardPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { LegalPages } from './pages/LegalPages';
import { LanguageProvider } from './localization/useLanguage';
import { AuthModal } from './components/layout/AuthModal';
import { apiClient } from './services/apiClient';
import { checkBackendHealth } from './services/apiClient';
import { getCurrentUser, setCurrentUser, getActiveSession } from './services/storage';
import { ScreeningSession, UserProfile, CustomerRecord, UserRole } from '@optiguide/shared';

export default function App() {
  const getInitialRoute = (): string => {
    if (typeof window === 'undefined') return 'home';
    const path = window.location.pathname.replace(/^\//, '').toLowerCase();
    if (path === 'virtual-try-on' || path === 'try-on') return 'virtual-try-on';
    if (path === 'screening' || path === 'eyewear' || path === 'results' || path === 'shop-dashboard' || path === 'admin-dashboard') {
      return path;
    }
    return 'home';
  };

  const [currentRoute, setCurrentRoute] = useState<string>(getInitialRoute());
  const [currentUser, setCurrentUserState] = useState<UserProfile | null>(getCurrentUser());
  const [activeSession, setActiveSession] = useState<ScreeningSession | null>(getActiveSession());
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [screeningCustomer, setScreeningCustomer] = useState<CustomerRecord | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);

  const navigateTo = (route: string) => {
    setCurrentRoute(route);
    if (typeof window !== 'undefined') {
      const targetPath = route === 'home' ? '/' : `/${route}`;
      if (window.location.pathname !== targetPath) {
        window.history.pushState(null, '', targetPath);
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  useEffect(() => {
    const handlePopState = () => {
      setCurrentRoute(getInitialRoute());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Poll backend health once on mount and sync authenticated user
  useEffect(() => {
    checkBackendHealth().then((status) => {
      setBackendOnline(status.online);
    });

    if (apiClient.getAccessToken()) {
      apiClient.getMe().then((me) => {
        const userProfile: UserProfile = {
          id: me.id,
          email: me.email,
          fullName: me.full_name,
          role: (me.role as UserRole) || 'individual',
          preferredLanguage: 'en',
          createdAt: me.created_at || new Date().toISOString(),
          updatedAt: me.updated_at || new Date().toISOString(),
        };
        setCurrentUser(userProfile);
        setCurrentUserState(userProfile);
      }).catch(() => {
        // Token invalid or expired
      });
    }
  }, []);

  // Handle role switching from navbar
  const handleSelectRole = (role: UserRole) => {
    const updated: UserProfile = {
      id: `usr-${role}`,
      email: `${role}@optiguide.org`,
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
      navigateTo('shop-dashboard');
    } else if (role === 'admin') {
      navigateTo('admin-dashboard');
    }
  };

  // Start screening for a specific customer from the shopkeeper kiosk
  const handleStartScreeningForCustomer = (customer: CustomerRecord) => {
    setScreeningCustomer(customer);
    navigateTo('screening');
  };

  // When a screening finishes
  const handleScreeningComplete = (session: ScreeningSession) => {
    setActiveSession(session);
    setScreeningCustomer(null);
    navigateTo('results');
  };

  return (
    <LanguageProvider>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: '#F7F4EC' }}>
        <Navbar
          currentRoute={currentRoute}
          onNavigate={(route) => navigateTo(route)}
          currentUser={currentUser}
          onSelectRole={handleSelectRole}
          backendOnline={backendOnline}
          onOpenAuth={() => setAuthModalOpen(true)}
        />

        <main style={{ flex: 1 }}>
          {currentRoute === 'home' && (
            <LandingPage
              onNavigate={(route) => navigateTo(route)}
            />
          )}

          {currentRoute === 'screening' && (
            <ScreeningFlowPage
              onComplete={handleScreeningComplete}
              onCancel={() => navigateTo('home')}
              customerName={screeningCustomer?.fullName}
              customerPhone={screeningCustomer?.phoneNumber}
            />
          )}

          {currentRoute === 'virtual-try-on' && (
            <VirtualTryOnPage
              onNavigate={(route) => navigateTo(route)}
              onSelectProductForCheckout={() => navigateTo('eyewear')}
            />
          )}

          {currentRoute === 'results' && activeSession && (
            <ResultsPage
              session={activeSession}
              onExploreEyewear={() => navigateTo('eyewear')}
              onNewScreening={() => navigateTo('screening')}
              onGoHome={() => navigateTo('home')}
            />
          )}

          {currentRoute === 'eyewear' && (
            <EyewearPage
              session={activeSession}
              onNavigate={(route) => navigateTo(route)}
            />
          )}

          {currentRoute === 'shop-dashboard' && (
            <ShopDashboardPage
              onStartScreeningForCustomer={handleStartScreeningForCustomer}
              onViewReport={(session) => {
                setActiveSession(session);
                navigateTo('results');
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
              onNavigate={(route) => navigateTo(route)}
            />
          )}
        </main>

        <Footer
          onNavigate={(route) => navigateTo(route)}
        />

        <AuthModal
          isOpen={authModalOpen}
          onClose={() => setAuthModalOpen(false)}
          currentUser={currentUser}
          onAuthSuccess={(updatedUser) => {
            setCurrentUserState(updatedUser);
            if (updatedUser.role === 'shopkeeper') {
              setCurrentRoute('shop-dashboard');
            } else if (updatedUser.role === 'admin') {
              setCurrentRoute('admin-dashboard');
            }
          }}
          onLogoutSuccess={() => {
            const guest: UserProfile = {
              id: 'usr-guest',
              email: 'guest@optiguide.org',
              fullName: 'Guest Citizen',
              role: 'guest',
              preferredLanguage: 'en',
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            };
            setCurrentUser(guest);
            setCurrentUserState(guest);
            setCurrentRoute('home');
          }}
        />
      </div>
    </LanguageProvider>
  );
}
