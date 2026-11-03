import { useState, useEffect, useCallback } from 'react';
import {
  HealthResponse,
  DatabaseHealthResponse,
  ApiUserProfileResponse,
  ConsentStatusResponse,
  ApiScreeningSessionResponse,
  ScreeningSessionListResponse,
  SCREENING_CONSTANTS,
  APP_CONFIG,
} from '@optiguide/shared';
import { webApiClient } from './services/apiClient';

type PageView = 'main' | 'screening' | 'auth' | 'diagnostics';
type ScreeningStep = 'intro' | 'consent' | 'active' | 'history';

export default function App() {
  const [currentView, setCurrentView] = useState<PageView>('main');
  const [screeningStep, setScreeningStep] = useState<ScreeningStep>('intro');
  const [backendStatus, setBackendStatus] = useState<'connected' | 'offline' | 'checking'>('checking');
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

  // Health Data
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [dbData, setDbData] = useState<DatabaseHealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(false);

  // Auth Data
  const [currentUser, setCurrentUser] = useState<ApiUserProfileResponse | null>(null);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState<string>('test.patient@example.com');
  const [password, setPassword] = useState<string>('SecurePassword123!');
  const [fullName, setFullName] = useState<string>('Test Patient');
  const [authLoading, setAuthLoading] = useState<boolean>(false);
  const [clinicalAccessResult, setClinicalAccessResult] = useState<string | null>(null);

  // Consent Data
  const [consentData, setConsentData] = useState<ConsentStatusResponse | null>(null);
  const [consentLoading, setConsentLoading] = useState<boolean>(false);

  // Session Data
  const [sessionsList, setSessionsList] = useState<ScreeningSessionListResponse | null>(null);
  const [activeSession, setActiveSession] = useState<ApiScreeningSessionResponse | null>(null);
  const [sessionsLoading, setSessionsLoading] = useState<boolean>(false);
  const [cancelReason, setCancelReason] = useState<string>('user_cancelled');

  const showNotification = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
    setStatusMessage({ text, type });
    setTimeout(() => setStatusMessage(null), 5000);
  };

  // Ping backend health
  const checkHealth = useCallback(async () => {
    setHealthLoading(true);
    setBackendStatus('checking');
    try {
      const [h, db] = await Promise.all([
        webApiClient.getHealth(),
        webApiClient.getDatabaseHealth(),
      ]);
      setHealthData(h);
      setDbData(db);
      setBackendStatus('connected');
    } catch {
      setBackendStatus('offline');
      setHealthData(null);
      setDbData(null);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  // Fetch current user if token exists
  const fetchCurrentUser = useCallback(async () => {
    if (!webApiClient.getAccessToken()) {
      setCurrentUser(null);
      return;
    }
    try {
      const user = await webApiClient.getCurrentUser();
      setCurrentUser(user);
    } catch {
      setCurrentUser(null);
    }
  }, []);

  // Fetch consent
  const fetchConsent = useCallback(async () => {
    if (!webApiClient.getAccessToken()) return;
    setConsentLoading(true);
    try {
      const res = await webApiClient.getConsentCurrent();
      setConsentData(res);
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setConsentLoading(false);
    }
  }, []);

  // Fetch sessions
  const fetchSessions = useCallback(async () => {
    if (!webApiClient.getAccessToken()) return;
    setSessionsLoading(true);
    try {
      const res = await webApiClient.listSessions({ page: 1, page_size: 20 });
      setSessionsList(res);
      const active = res.items.find((s) => s.status === 'in_progress') || null;
      setActiveSession(active);
      if (active) {
        setScreeningStep('active');
      }
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    checkHealth();
    fetchCurrentUser();
  }, [checkHealth, fetchCurrentUser]);

  // Auth Handlers
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    try {
      if (authMode === 'register') {
        const res = await webApiClient.register({ email, password, full_name: fullName });
        setCurrentUser(res.user);
        showNotification(`Welcome, ${res.user.full_name}!`, 'success');
      } else {
        const res = await webApiClient.login({ email, password });
        setCurrentUser(res.user);
        showNotification(`Signed in as ${res.user.email}`, 'success');
      }
      setCurrentView('main');
      await fetchConsent();
      await fetchSessions();
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = async () => {
    await webApiClient.logout();
    setCurrentUser(null);
    setConsentData(null);
    setSessionsList(null);
    setActiveSession(null);
    showNotification('Logged out successfully.', 'info');
  };

  const handleCheckClinicalReview = async () => {
    try {
      const res = await webApiClient.checkClinicalReviewAccess();
      setClinicalAccessResult(JSON.stringify(res, null, 2));
      showNotification('Clinical review access check completed.', 'success');
    } catch (err: any) {
      setClinicalAccessResult(`Error: ${err.message}`);
      showNotification(err.message, 'error');
    }
  };

  // Screening Flow Actions
  const handleStartScreeningButton = async () => {
    if (!currentUser) {
      setCurrentView('auth');
      showNotification('Please sign in or create an account to start screening.', 'info');
      return;
    }
    setCurrentView('screening');
    await fetchConsent();
    await fetchSessions();
  };

  const handleAcceptConsent = async () => {
    setConsentLoading(true);
    try {
      await webApiClient.acceptConsent('1.0.0');
      showNotification('Screening consent accepted (v1.0.0).', 'success');
      await fetchConsent();
      // Proceed to create session
      await handleCreateSession();
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setConsentLoading(false);
    }
  };

  const handleWithdrawConsent = async () => {
    if (!window.confirm('Withdraw screening consent? Any in-progress session will be cancelled.')) return;
    setConsentLoading(true);
    try {
      const res = await webApiClient.withdrawConsent();
      showNotification(`Consent withdrawn. ${res.active_sessions_cancelled} active session(s) cancelled.`, 'info');
      await fetchConsent();
      await fetchSessions();
      setScreeningStep('intro');
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setConsentLoading(false);
    }
  };

  const handleCreateSession = async () => {
    setSessionsLoading(true);
    try {
      const session = await webApiClient.createSession({
        device_info: `Web Browser (${navigator.userAgent.slice(0, 45)})`,
        notes: 'Preliminary Web Screening',
      });
      setActiveSession(session);
      setScreeningStep('active');
      showNotification('New screening session initialized.', 'success');
      await fetchSessions();
    } catch (err: any) {
      if (err.message && err.message.includes('CONSENT_REQUIRED')) {
        setScreeningStep('consent');
      } else if (err.message && err.message.includes('SESSION_ALREADY_ACTIVE')) {
        setScreeningStep('active');
        showNotification('Resuming your existing active screening session.', 'info');
      } else {
        showNotification(err.message, 'error');
      }
    } finally {
      setSessionsLoading(false);
    }
  };

  const handleCompleteSession = async (sessionId: string) => {
    setSessionsLoading(true);
    try {
      await webApiClient.completeSession(sessionId);
      showNotification('Screening session completed successfully!', 'success');
      setActiveSession(null);
      setScreeningStep('history');
      await fetchSessions();
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setSessionsLoading(false);
    }
  };

  const handleCancelSession = async (sessionId: string) => {
    setSessionsLoading(true);
    try {
      await webApiClient.cancelSession(sessionId, cancelReason);
      showNotification('Screening session cancelled.', 'info');
      setActiveSession(null);
      setScreeningStep('intro');
      await fetchSessions();
    } catch (err: any) {
      showNotification(err.message, 'error');
    } finally {
      setSessionsLoading(false);
    }
  };

  return (
    <div style={styles.appWrapper}>
      {/* =========================================================================
          GLOBAL NAVIGATION BAR
      ========================================================================= */}
      <header style={styles.navbar}>
        <div style={styles.navContainer}>
          <div style={styles.navBrand} onClick={() => setCurrentView('main')}>
            <span style={styles.brandIcon}>👁️</span>
            <div>
              <span style={styles.brandTitle}>{APP_CONFIG.APP_NAME}</span>
              <span style={styles.brandSubtitle}>Vision Screening & Guidance</span>
            </div>
          </div>

          <div style={styles.navActions}>
            {/* Live Server Indicator */}
            <div
              style={styles.systemStatusBadge}
              onClick={() => setCurrentView('diagnostics')}
              title="Click to view API & Database Health Diagnostics"
            >
              <span
                style={{
                  ...styles.statusDot,
                  backgroundColor:
                    backendStatus === 'connected' ? '#10B981' : backendStatus === 'checking' ? '#F59E0B' : '#EF4444',
                }}
              />
              <span style={styles.statusText}>
                {backendStatus === 'connected'
                  ? 'System Online'
                  : backendStatus === 'checking'
                  ? 'Connecting...'
                  : 'Backend Offline'}
              </span>
            </div>

            {/* User Profile / Authentication */}
            {currentUser ? (
              <button
                onClick={() => setCurrentView('auth')}
                style={styles.navUserButton}
              >
                👤 {currentUser.full_name}
                <span style={styles.navRoleBadge}>{currentUser.role}</span>
              </button>
            ) : (
              <button
                onClick={() => {
                  setAuthMode('login');
                  setCurrentView('auth');
                }}
                style={styles.navLoginButton}
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Global Notification Toast */}
      {statusMessage && (
        <div
          style={{
            ...styles.toast,
            backgroundColor:
              statusMessage.type === 'success'
                ? '#ECFDF5'
                : statusMessage.type === 'error'
                ? '#FEF2F2'
                : '#EFF6FF',
            borderColor:
              statusMessage.type === 'success'
                ? '#10B981'
                : statusMessage.type === 'error'
                ? '#EF4444'
                : '#3B82F6',
            color:
              statusMessage.type === 'success'
                ? '#065F46'
                : statusMessage.type === 'error'
                ? '#991B1B'
                : '#1E40AF',
          }}
        >
          {statusMessage.text}
        </div>
      )}

      {/* =========================================================================
          VIEW 1: MAIN HOME PAGE
      ========================================================================= */}
      {currentView === 'main' && (
        <main style={styles.mainContent}>
          {/* Clinical Medical Notice Banner */}
          <div style={styles.disclaimerBanner}>
            <div style={styles.disclaimerHeader}>
              <span style={styles.disclaimerIcon}>⚠️</span>
              <strong>Important Clinical Notice: Non-Diagnostic Platform</strong>
            </div>
            <p style={styles.disclaimerText}>
              {SCREENING_CONSTANTS.CLINICAL_DISCLAIMER_TEXT}
            </p>
          </div>

          {/* Hero Section */}
          <section style={styles.heroSection}>
            <div style={styles.heroBadge}>Preliminary Vision Guidance • v{APP_CONFIG.VERSION}</div>
            <h1 style={styles.heroHeading}>
              Accurate, Accessible Vision Screening & Eyewear Assistance
            </h1>
            <p style={styles.heroSubheading}>
              Check your visual acuity, assess reading clarity, and receive standardized guidance before consulting your certified eye-care professional.
            </p>

            <div style={styles.heroButtonRow}>
              <button
                onClick={handleStartScreeningButton}
                style={styles.heroPrimaryButton}
              >
                Start Vision Screening →
              </button>
              <button
                onClick={() => {
                  if (!currentUser) setCurrentView('auth');
                  else {
                    setCurrentView('screening');
                    setScreeningStep('history');
                  }
                }}
                style={styles.heroSecondaryButton}
              >
                View Screening History
              </button>
            </div>
          </section>

          {/* Product Feature Cards */}
          <section style={styles.featuresSection}>
            <h2 style={styles.sectionTitle}>OptiGuide Features</h2>
            <div style={styles.featuresGrid}>
              {/* Feature 1: Preliminary Screening */}
              <div style={styles.featureCard}>
                <div style={styles.featureIconBadge}>👁️</div>
                <div style={styles.featureStatusActive}>Phase 3.1 Live</div>
                <h3 style={styles.featureTitle}>Preliminary Vision Screening</h3>
                <p style={styles.featureBody}>
                  Standardized visual acuity checks, Snellen equivalent estimation, and contrast assessment with consent-gated session management.
                </p>
                <button
                  onClick={handleStartScreeningButton}
                  style={styles.cardActionButton}
                >
                  Launch Screening →
                </button>
              </div>

              {/* Feature 2: Eyewear & Frame Guidance */}
              <div style={styles.featureCard}>
                <div style={styles.featureIconBadge}>👓</div>
                <div style={styles.featureStatusUpcoming}>Phase 4 Preview</div>
                <h3 style={styles.featureTitle}>Eyewear & Frame Assistant</h3>
                <p style={styles.featureBody}>
                  Facial measurement guidance, lens recommendations, and ergonomic frame fitting options tailored to your screening profile.
                </p>
                <button
                  disabled
                  style={{ ...styles.cardActionButton, backgroundColor: '#E2E8F0', color: '#94A3B8', cursor: 'not-allowed' }}
                >
                  Coming Soon (Phase 4)
                </button>
              </div>

              {/* Feature 3: Professional Consultation */}
              <div style={styles.featureCard}>
                <div style={styles.featureIconBadge}>🩺</div>
                <div style={styles.featureStatusUpcoming}>Clinical Review</div>
                <h3 style={styles.featureTitle}>Optometrist Referral</h3>
                <p style={styles.featureBody}>
                  Seamlessly share your objective preliminary screening data with qualified optometrists and eye-care providers for prescription confirmation.
                </p>
                <button
                  onClick={() => setCurrentView('auth')}
                  style={styles.cardActionButtonOutline}
                >
                  Provider Verification →
                </button>
              </div>
            </div>
          </section>

          {/* Screening Preparation Checklist */}
          <section style={styles.checklistSection}>
            <h2 style={styles.sectionTitle}>Recommended Screening Environment</h2>
            <div style={styles.checklistGrid}>
              <div style={styles.checklistItem}>
                <div style={styles.checkIcon}>💡</div>
                <div>
                  <strong>Uniform Lighting</strong>
                  <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: '#64748B' }}>
                    Avoid screen glare and shadows on your display.
                  </p>
                </div>
              </div>

              <div style={styles.checklistItem}>
                <div style={styles.checkIcon}>📏</div>
                <div>
                  <strong>Proper Distance</strong>
                  <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: '#64748B' }}>
                    Sit comfortably at arm's length (40cm for near, calibrated for distance).
                  </p>
                </div>
              </div>

              <div style={styles.checklistItem}>
                <div style={styles.checkIcon}>👓</div>
                <div>
                  <strong>Wear Normal Eyewear</strong>
                  <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: '#64748B' }}>
                    Keep your current glasses or contact lenses on if testing corrected vision.
                  </p>
                </div>
              </div>

              <div style={styles.checklistItem}>
                <div style={styles.checkIcon}>⏱️</div>
                <div>
                  <strong>Take Your Time</strong>
                  <p style={{ margin: '0.25rem 0 0', fontSize: '0.875rem', color: '#64748B' }}>
                    Each test takes 2–3 minutes. Rest your eyes between checks.
                  </p>
                </div>
              </div>
            </div>
          </section>
        </main>
      )}

      {/* =========================================================================
          VIEW 2: VISION SCREENING FLOW
      ========================================================================= */}
      {currentView === 'screening' && (
        <div style={styles.subPageContainer}>
          <div style={styles.subPageTopBar}>
            <button
              onClick={() => setCurrentView('main')}
              style={styles.backButton}
            >
              ← Back to Main Page
            </button>
            <div style={styles.stepTabs}>
              <button
                onClick={() => setScreeningStep('intro')}
                style={{ ...styles.stepTabButton, ...(screeningStep === 'intro' ? styles.stepTabButtonActive : {}) }}
              >
                1. Intro & Prep
              </button>
              <button
                onClick={() => setScreeningStep('consent')}
                style={{ ...styles.stepTabButton, ...(screeningStep === 'consent' ? styles.stepTabButtonActive : {}) }}
              >
                2. Legal Consent {consentData?.has_accepted ? '✓' : ''}
              </button>
              <button
                onClick={() => setScreeningStep('active')}
                style={{ ...styles.stepTabButton, ...(screeningStep === 'active' ? styles.stepTabButtonActive : {}) }}
              >
                3. Active Session {activeSession ? '(1)' : ''}
              </button>
              <button
                onClick={() => setScreeningStep('history')}
                style={{ ...styles.stepTabButton, ...(screeningStep === 'history' ? styles.stepTabButtonActive : {}) }}
              >
                4. Session History
              </button>
            </div>
          </div>

          {/* Step 1: Intro */}
          {screeningStep === 'intro' && (
            <div style={styles.contentCard}>
              <h2>Preliminary Vision Screening Overview</h2>
              <p style={{ color: '#64748B', lineHeight: 1.6 }}>
                This screening module establishes your session and records objective visual test responses. It will guide you through distance visual acuity checks and near reading comfort assessments.
              </p>

              <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px', margin: '1.5rem 0' }}>
                <h4 style={{ margin: '0 0 0.5rem', color: '#1E293B' }}>Before Starting:</h4>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#475569', lineHeight: 1.7 }}>
                  <li>Ensure your screen brightness is comfortable.</li>
                  <li>Position yourself at standard viewing distance.</li>
                  <li>Review and accept the non-diagnostic clinical disclaimer.</li>
                </ul>
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                  onClick={() => {
                    if (consentData?.has_accepted) {
                      handleCreateSession();
                    } else {
                      setScreeningStep('consent');
                    }
                  }}
                  style={styles.heroPrimaryButton}
                >
                  {consentData?.has_accepted ? 'Start Screening Session →' : 'Review & Accept Consent →'}
                </button>
                <button
                  onClick={() => setScreeningStep('history')}
                  style={styles.heroSecondaryButton}
                >
                  View Past Sessions
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Consent */}
          {screeningStep === 'consent' && (
            <div style={styles.contentCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2>Screening Consent & Medical Disclaimer</h2>
                {consentData?.has_accepted ? (
                  <span style={styles.badgeSuccess}>Consent Active (v{consentData.version})</span>
                ) : (
                  <span style={styles.badgeWarning}>Consent Required</span>
                )}
              </div>

              <div style={{ backgroundColor: '#F8FAFC', padding: '1rem', borderRadius: '8px', margin: '1rem 0' }}>
                <p style={{ margin: '0 0 0.5rem' }}>
                  <strong>Document Version:</strong> {consentData?.version || '1.0.0'}
                </p>
                <p style={{ margin: '0 0 0.25rem' }}>
                  <strong>SHA-256 Cryptographic Hash:</strong>
                </p>
                <code style={{ fontSize: '0.75rem', wordBreak: 'break-all', color: '#2563EB' }}>
                  {consentData?.hash || 'ea78d46e3db2b07e74853059dbe888b50df3650ea9599fb42bfae21db7c25cf6'}
                </code>
              </div>

              <div style={styles.consentTextBox}>
                {consentData?.content || SCREENING_CONSTANTS.CLINICAL_DISCLAIMER_TEXT}
              </div>

              <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                {!consentData?.has_accepted ? (
                  <button
                    onClick={handleAcceptConsent}
                    disabled={consentLoading}
                    style={styles.heroPrimaryButton}
                  >
                    {consentLoading ? 'Submitting...' : '✓ I Agree & Accept Consent (v1.0.0)'}
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleCreateSession}
                      style={styles.heroPrimaryButton}
                    >
                      ▶ Start Active Session
                    </button>
                    <button
                      onClick={handleWithdrawConsent}
                      disabled={consentLoading}
                      style={styles.dangerButton}
                    >
                      Withdraw Consent
                    </button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Step 3: Active Session */}
          {screeningStep === 'active' && (
            <div style={styles.contentCard}>
              <h2>Active Screening Session</h2>

              {activeSession ? (
                <div style={styles.activeSessionCallout}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                      <span style={styles.badgeInProgress}>● IN PROGRESS</span>
                      <h3 style={{ margin: '0.5rem 0' }}>Screening Session Underway</h3>
                      <p style={{ color: '#475569', fontSize: '0.875rem' }}>
                        ID: <code>{activeSession.id}</code>
                      </p>
                      <p style={{ color: '#475569', fontSize: '0.875rem' }}>
                        Started At: {new Date(activeSession.started_at).toLocaleString()}
                      </p>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-end' }}>
                      <button
                        onClick={() => handleCompleteSession(activeSession.id)}
                        disabled={sessionsLoading}
                        style={styles.heroPrimaryButton}
                      >
                        ✓ Complete Session
                      </button>

                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <select
                          value={cancelReason}
                          onChange={(e) => setCancelReason(e.target.value)}
                          style={{ padding: '0.4rem', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '0.8125rem' }}
                        >
                          <option value="user_cancelled">Reason: User Cancelled</option>
                          <option value="interrupted">Reason: Interrupted</option>
                          <option value="technical_issue">Reason: Technical Issue</option>
                        </select>
                        <button
                          onClick={() => handleCancelSession(activeSession.id)}
                          disabled={sessionsLoading}
                          style={styles.dangerButton}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                  <h3>No Active Session Ongoing</h3>
                  <p style={{ color: '#64748B', maxWidth: '420px', margin: '0.5rem auto 1.5rem' }}>
                    You currently have no active session. Ready to begin your preliminary screening?
                  </p>
                  <button
                    onClick={handleCreateSession}
                    disabled={sessionsLoading}
                    style={styles.heroPrimaryButton}
                  >
                    ▶ Start New Screening Session
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Step 4: History */}
          {screeningStep === 'history' && (
            <div style={styles.contentCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2>Screening Session History</h2>
                <button onClick={() => fetchSessions()} disabled={sessionsLoading} style={styles.heroSecondaryButton}>
                  🔄 Refresh
                </button>
              </div>

              {sessionsList && sessionsList.items.length > 0 ? (
                <div style={{ overflowX: 'auto' }}>
                  <table style={styles.table}>
                    <thead>
                      <tr>
                        <th style={styles.th}>Session ID</th>
                        <th style={styles.th}>Status</th>
                        <th style={styles.th}>Started At</th>
                        <th style={styles.th}>Ended At</th>
                        <th style={styles.th}>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessionsList.items.map((s) => (
                        <tr key={s.id} style={styles.tr}>
                          <td style={styles.td}><code>{s.id.slice(0, 8)}...</code></td>
                          <td style={styles.td}>
                            <span
                              style={
                                s.status === 'completed'
                                  ? styles.badgeSuccess
                                  : s.status === 'in_progress'
                                  ? styles.badgeInProgress
                                  : styles.badgeError
                              }
                            >
                              {s.status.toUpperCase()}
                            </span>
                          </td>
                          <td style={styles.td}>{new Date(s.started_at).toLocaleString()}</td>
                          <td style={styles.td}>
                            {s.completed_at
                              ? new Date(s.completed_at).toLocaleString()
                              : s.cancelled_at
                              ? new Date(s.cancelled_at).toLocaleString()
                              : '—'}
                          </td>
                          <td style={styles.td}>{s.cancellation_reason || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p style={{ color: '#64748B' }}>No screening sessions recorded yet.</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          VIEW 3: USER AUTHENTICATION & PROFILE
      ========================================================================= */}
      {currentView === 'auth' && (
        <div style={styles.subPageContainer}>
          <div style={styles.subPageTopBar}>
            <button
              onClick={() => setCurrentView('main')}
              style={styles.backButton}
            >
              ← Back to Main Page
            </button>
          </div>

          <div style={{ ...styles.contentCard, maxWidth: '540px', margin: '0 auto' }}>
            {currentUser ? (
              <div>
                <h2>Your Account</h2>
                <div style={{ backgroundColor: '#F8FAFC', padding: '1.25rem', borderRadius: '8px', margin: '1.5rem 0' }}>
                  <p><strong>Name:</strong> {currentUser.full_name}</p>
                  <p><strong>Email:</strong> {currentUser.email}</p>
                  <p><strong>Role:</strong> <span style={styles.badgeInProgress}>{currentUser.role.toUpperCase()}</span></p>
                  <p><strong>Verified Professional:</strong> {currentUser.is_verified ? 'Yes ✓' : 'No'}</p>
                </div>

                <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button onClick={handleCheckClinicalReview} style={styles.heroSecondaryButton}>
                    Check Optometrist Clinical Access
                  </button>
                  <button onClick={handleLogout} style={styles.dangerButton}>
                    Sign Out
                  </button>
                </div>

                {clinicalAccessResult && (
                  <pre style={styles.codeBlock}>{clinicalAccessResult}</pre>
                )}
              </div>
            ) : (
              <div>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                  <button
                    onClick={() => setAuthMode('login')}
                    style={{
                      flex: 1,
                      padding: '0.75rem',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontWeight: 700,
                      backgroundColor: authMode === 'login' ? '#2563EB' : '#F1F5F9',
                      color: authMode === 'login' ? '#FFF' : '#475569',
                    }}
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => setAuthMode('register')}
                    style={{
                      flex: 1,
                      padding: '0.75rem',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontWeight: 700,
                      backgroundColor: authMode === 'register' ? '#2563EB' : '#F1F5F9',
                      color: authMode === 'register' ? '#FFF' : '#475569',
                    }}
                  >
                    Create Account
                  </button>
                </div>

                <form onSubmit={handleAuthSubmit}>
                  {authMode === 'register' && (
                    <div style={{ marginBottom: '1rem' }}>
                      <label style={styles.formLabel}>Full Name</label>
                      <input
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        style={styles.formInput}
                        placeholder="John Doe"
                      />
                    </div>
                  )}

                  <div style={{ marginBottom: '1rem' }}>
                    <label style={styles.formLabel}>Email Address</label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      style={styles.formInput}
                      placeholder="patient@example.com"
                    />
                  </div>

                  <div style={{ marginBottom: '1.5rem' }}>
                    <label style={styles.formLabel}>Password</label>
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      style={styles.formInput}
                      placeholder="••••••••"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={authLoading}
                    style={{ ...styles.heroPrimaryButton, width: '100%' }}
                  >
                    {authLoading ? 'Signing in...' : authMode === 'register' ? 'Register Patient Account' : 'Sign In'}
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      )}

      {/* =========================================================================
          VIEW 4: SYSTEM DIAGNOSTICS
      ========================================================================= */}
      {currentView === 'diagnostics' && (
        <div style={styles.subPageContainer}>
          <div style={styles.subPageTopBar}>
            <button
              onClick={() => setCurrentView('main')}
              style={styles.backButton}
            >
              ← Back to Main Page
            </button>
            <button
              onClick={checkHealth}
              disabled={healthLoading}
              style={styles.heroSecondaryButton}
            >
              🔄 Re-test Ping
            </button>
          </div>

          <div style={styles.contentCard}>
            <h2>System Architecture & Health Telemetry</h2>
            <div style={styles.featuresGrid}>
              <div style={styles.subCard}>
                <h3>FastAPI Service</h3>
                <p><strong>Status:</strong> {healthData ? healthData.status.toUpperCase() : 'Unavailable'}</p>
                <p><strong>Service:</strong> {healthData?.service || 'N/A'}</p>
                <p><strong>Version:</strong> {healthData?.version || 'N/A'}</p>
                <p><strong>Environment:</strong> {healthData?.environment || 'N/A'}</p>
              </div>

              <div style={styles.subCard}>
                <h3>Database Subsystem</h3>
                <p><strong>Status:</strong> {dbData ? dbData.status.toUpperCase() : 'Unavailable'}</p>
                <p><strong>Dialect:</strong> {dbData?.database_type || 'N/A'}</p>
                <p><strong>Latency:</strong> {dbData?.latency_ms !== null ? `${dbData?.latency_ms} ms` : 'N/A'}</p>
                <p><strong>Message:</strong> {dbData?.message || 'N/A'}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          GLOBAL FOOTER
      ========================================================================= */}
      <footer style={styles.footer}>
        <div style={styles.footerContainer}>
          <div style={styles.footerText}>
            © 2026 {APP_CONFIG.APP_NAME}. Preliminary vision screening tool. Not an ophthalmic diagnostic or prescription platform.
          </div>
          <div style={styles.footerLinks}>
            <span
              style={styles.footerLink}
              onClick={() => setCurrentView('diagnostics')}
            >
              System Health Diagnostics
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

// =============================================================================
// STYLES
// =============================================================================
const styles: Record<string, React.CSSProperties> = {
  appWrapper: {
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
    backgroundColor: '#F8FAFC',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    color: '#0F172A',
  },
  navbar: {
    backgroundColor: '#FFFFFF',
    borderBottom: '1px solid #E2E8F0',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  navContainer: {
    maxWidth: '1100px',
    margin: '0 auto',
    padding: '0.875rem 1.5rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  navBrand: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    cursor: 'pointer',
  },
  brandIcon: {
    fontSize: '1.75rem',
  },
  brandTitle: {
    fontSize: '1.25rem',
    fontWeight: 800,
    color: '#1E40AF',
    display: 'block',
    lineHeight: 1.2,
  },
  brandSubtitle: {
    fontSize: '0.75rem',
    color: '#64748B',
    display: 'block',
  },
  navActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  systemStatusBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.375rem 0.75rem',
    borderRadius: '9999px',
    backgroundColor: '#F1F5F9',
    cursor: 'pointer',
    fontSize: '0.8125rem',
    fontWeight: 600,
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  statusText: {
    color: '#334155',
  },
  navUserButton: {
    backgroundColor: '#EFF6FF',
    color: '#1E40AF',
    border: '1px solid #BFDBFE',
    borderRadius: '6px',
    padding: '0.4rem 0.75rem',
    fontSize: '0.875rem',
    fontWeight: 600,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  navRoleBadge: {
    backgroundColor: '#DBEAFE',
    color: '#1D4ED8',
    padding: '0.125rem 0.375rem',
    borderRadius: '4px',
    fontSize: '0.6875rem',
    textTransform: 'uppercase',
  },
  navLoginButton: {
    backgroundColor: '#2563EB',
    color: '#FFFFFF',
    border: 'none',
    borderRadius: '6px',
    padding: '0.5rem 1rem',
    fontSize: '0.875rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  toast: {
    position: 'fixed',
    top: '4.5rem',
    right: '1.5rem',
    zIndex: 1000,
    padding: '0.75rem 1.25rem',
    borderRadius: '8px',
    border: '1px solid',
    fontSize: '0.875rem',
    fontWeight: 600,
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  },
  mainContent: {
    maxWidth: '1100px',
    margin: '0 auto',
    padding: '2rem 1.5rem',
    flex: 1,
    width: '100%',
    boxSizing: 'border-box',
  },
  disclaimerBanner: {
    backgroundColor: '#FFFBEB',
    border: '1px solid #FCD34D',
    borderRadius: '10px',
    padding: '1.25rem 1.5rem',
    marginBottom: '2.5rem',
  },
  disclaimerHeader: {
    color: '#B45309',
    fontSize: '0.9375rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.375rem',
  },
  disclaimerIcon: {
    fontSize: '1.125rem',
  },
  disclaimerText: {
    color: '#92400E',
    fontSize: '0.875rem',
    lineHeight: 1.5,
    margin: 0,
  },
  heroSection: {
    textAlign: 'center',
    padding: '2.5rem 1rem 3.5rem',
  },
  heroBadge: {
    display: 'inline-block',
    backgroundColor: '#DBEAFE',
    color: '#1D4ED8',
    padding: '0.375rem 0.875rem',
    borderRadius: '9999px',
    fontSize: '0.8125rem',
    fontWeight: 700,
    marginBottom: '1.25rem',
  },
  heroHeading: {
    fontSize: '2.5rem',
    fontWeight: 800,
    color: '#0F172A',
    lineHeight: 1.2,
    maxWidth: '820px',
    margin: '0 auto 1.25rem',
  },
  heroSubheading: {
    fontSize: '1.125rem',
    color: '#475569',
    maxWidth: '640px',
    margin: '0 auto 2rem',
    lineHeight: 1.6,
  },
  heroButtonRow: {
    display: 'flex',
    justifyContent: 'center',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  heroPrimaryButton: {
    backgroundColor: '#2563EB',
    color: '#FFFFFF',
    border: 'none',
    borderRadius: '8px',
    padding: '0.875rem 1.75rem',
    fontSize: '1rem',
    fontWeight: 700,
    cursor: 'pointer',
    boxShadow: '0 4px 6px -1px rgba(37, 99, 235, 0.25)',
  },
  heroSecondaryButton: {
    backgroundColor: '#FFFFFF',
    color: '#334155',
    border: '1px solid #CBD5E1',
    borderRadius: '8px',
    padding: '0.875rem 1.5rem',
    fontSize: '1rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  featuresSection: {
    marginBottom: '3.5rem',
  },
  sectionTitle: {
    fontSize: '1.5rem',
    fontWeight: 800,
    color: '#0F172A',
    marginBottom: '1.5rem',
  },
  featuresGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '1.5rem',
  },
  featureCard: {
    backgroundColor: '#FFFFFF',
    border: '1px solid #E2E8F0',
    borderRadius: '12px',
    padding: '1.75rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    display: 'flex',
    flexDirection: 'column',
  },
  featureIconBadge: {
    fontSize: '2rem',
    marginBottom: '0.75rem',
  },
  featureStatusActive: {
    display: 'inline-block',
    alignSelf: 'flex-start',
    backgroundColor: '#D1FAE5',
    color: '#065F46',
    padding: '0.2rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.6875rem',
    fontWeight: 700,
    marginBottom: '0.75rem',
  },
  featureStatusUpcoming: {
    display: 'inline-block',
    alignSelf: 'flex-start',
    backgroundColor: '#F1F5F9',
    color: '#64748B',
    padding: '0.2rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.6875rem',
    fontWeight: 700,
    marginBottom: '0.75rem',
  },
  featureTitle: {
    fontSize: '1.25rem',
    fontWeight: 700,
    margin: '0 0 0.5rem',
    color: '#1E293B',
  },
  featureBody: {
    fontSize: '0.875rem',
    color: '#64748B',
    lineHeight: 1.6,
    flex: 1,
    marginBottom: '1.5rem',
  },
  cardActionButton: {
    backgroundColor: '#2563EB',
    color: '#FFFFFF',
    border: 'none',
    borderRadius: '6px',
    padding: '0.625rem 1rem',
    fontSize: '0.875rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  cardActionButtonOutline: {
    backgroundColor: 'transparent',
    color: '#2563EB',
    border: '1px solid #2563EB',
    borderRadius: '6px',
    padding: '0.625rem 1rem',
    fontSize: '0.875rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  checklistSection: {
    backgroundColor: '#FFFFFF',
    border: '1px solid #E2E8F0',
    borderRadius: '12px',
    padding: '2rem',
    marginBottom: '3rem',
  },
  checklistGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '1.5rem',
  },
  checklistItem: {
    display: 'flex',
    gap: '0.75rem',
    alignItems: 'flex-start',
  },
  checkIcon: {
    fontSize: '1.25rem',
  },
  subPageContainer: {
    maxWidth: '960px',
    margin: '0 auto',
    padding: '2rem 1.5rem',
    flex: 1,
    width: '100%',
    boxSizing: 'border-box',
  },
  subPageTopBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
    flexWrap: 'wrap',
    gap: '1rem',
  },
  backButton: {
    backgroundColor: 'transparent',
    color: '#2563EB',
    border: 'none',
    fontSize: '0.9375rem',
    fontWeight: 600,
    cursor: 'pointer',
    padding: '0.5rem 0',
  },
  stepTabs: {
    display: 'flex',
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  stepTabButton: {
    padding: '0.5rem 0.875rem',
    border: 'none',
    borderRadius: '6px',
    backgroundColor: '#F1F5F9',
    color: '#64748B',
    fontSize: '0.8125rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  stepTabButtonActive: {
    backgroundColor: '#EFF6FF',
    color: '#1D4ED8',
    border: '1px solid #BFDBFE',
  },
  contentCard: {
    backgroundColor: '#FFFFFF',
    border: '1px solid #E2E8F0',
    borderRadius: '12px',
    padding: '2rem',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
  },
  subCard: {
    backgroundColor: '#F8FAFC',
    border: '1px solid #E2E8F0',
    borderRadius: '8px',
    padding: '1.25rem',
  },
  consentTextBox: {
    backgroundColor: '#F8FAFC',
    border: '1px solid #CBD5E1',
    borderRadius: '8px',
    padding: '1rem',
    maxHeight: '160px',
    overflowY: 'auto',
    fontSize: '0.875rem',
    lineHeight: 1.6,
    color: '#334155',
  },
  activeSessionCallout: {
    backgroundColor: '#EFF6FF',
    border: '1px solid #BFDBFE',
    borderRadius: '8px',
    padding: '1.5rem',
  },
  dangerButton: {
    backgroundColor: '#DC2626',
    color: '#FFFFFF',
    border: 'none',
    borderRadius: '6px',
    padding: '0.625rem 1.25rem',
    fontSize: '0.875rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  badgeSuccess: {
    backgroundColor: '#D1FAE5',
    color: '#065F46',
    padding: '0.25rem 0.625rem',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: 700,
  },
  badgeWarning: {
    backgroundColor: '#FEF3C7',
    color: '#92400E',
    padding: '0.25rem 0.625rem',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: 700,
  },
  badgeInProgress: {
    backgroundColor: '#DBEAFE',
    color: '#1E40AF',
    padding: '0.25rem 0.625rem',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: 700,
  },
  badgeError: {
    backgroundColor: '#FEE2E2',
    color: '#991B1B',
    padding: '0.25rem 0.625rem',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: 700,
  },
  formLabel: {
    display: 'block',
    fontSize: '0.875rem',
    fontWeight: 600,
    marginBottom: '0.25rem',
    color: '#334155',
  },
  formInput: {
    width: '100%',
    padding: '0.625rem 0.75rem',
    borderRadius: '6px',
    border: '1px solid #CBD5E1',
    fontSize: '0.875rem',
    boxSizing: 'border-box',
  },
  codeBlock: {
    backgroundColor: '#0F172A',
    color: '#38BDF8',
    padding: '0.75rem',
    borderRadius: '6px',
    fontSize: '0.8125rem',
    overflowX: 'auto',
    marginTop: '1rem',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '0.875rem',
  },
  th: {
    textAlign: 'left',
    padding: '0.75rem',
    borderBottom: '2px solid #E2E8F0',
    color: '#64748B',
    fontWeight: 600,
  },
  td: {
    padding: '0.75rem',
    borderBottom: '1px solid #E2E8F0',
    color: '#334155',
  },
  tr: {
    transition: 'background-color 0.15s ease',
  },
  footer: {
    backgroundColor: '#FFFFFF',
    borderTop: '1px solid #E2E8F0',
    padding: '1.5rem',
    marginTop: 'auto',
  },
  footerContainer: {
    maxWidth: '1100px',
    margin: '0 auto',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '1rem',
  },
  footerText: {
    fontSize: '0.8125rem',
    color: '#64748B',
  },
  footerLinks: {
    display: 'flex',
    gap: '1rem',
  },
  footerLink: {
    fontSize: '0.8125rem',
    color: '#2563EB',
    cursor: 'pointer',
    fontWeight: 500,
  },
};
