import React, { useState } from 'react';
import { View, StyleSheet, Alert, Platform } from 'react-native';
import { ApiScreeningSessionResponse } from '@optiguide/shared';
import apiClient from '../../src/services/apiClient';
import ScreeningIntroScreen from '../../src/features/screening/ScreeningIntroScreen';
import ConsentScreen from '../../src/features/screening/ConsentScreen';
import ActiveSessionScreen from '../../src/features/screening/ActiveSessionScreen';
import SessionHistoryScreen from '../../src/features/screening/SessionHistoryScreen';
import { LoadingIndicator } from '../../src/components/LoadingIndicator';
import { ErrorMessage } from '../../src/components/ErrorMessage';

type ScreeningFlowState = 'intro' | 'consent' | 'active_session' | 'history';

export default function ScreeningIndex() {
  const [currentStep, setCurrentStep] = useState<ScreeningFlowState>('intro');
  const [activeSession, setActiveSession] = useState<ApiScreeningSessionResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const startScreeningFlow = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // 1. Check if user already has an active consent
      const consent = await apiClient.getScreeningConsent();
      if (!consent.is_active) {
        // Direct user to accept consent first
        setCurrentStep('consent');
        setIsLoading(false);
        return;
      }

      // 2. Attempt to create or fetch active session
      const session = await apiClient.createScreeningSession();
      setActiveSession(session);
      setCurrentStep('active_session');
    } catch (err: any) {
      if (err.message && err.message.includes('CONSENT_REQUIRED')) {
        setCurrentStep('consent');
      } else if (err.message && err.message.includes('SESSION_ALREADY_ACTIVE')) {
        // If an active session is already ongoing, fetch active session
        try {
          const list = await apiClient.listScreeningSessions('in_progress', 1, 0);
          if (list.items.length > 0) {
            setActiveSession(list.items[0]);
            setCurrentStep('active_session');
            return;
          }
        } catch (_) {
          // Fall through to display error
        }
        setErrorMessage(err.message || 'An active screening session is already in progress.');
      } else {
        setErrorMessage(err.message || 'Failed to initialize screening session.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleConsentAccepted = async () => {
    // Once consent is accepted, proceed to start screening session
    startScreeningFlow();
  };

  const handleConsentWithdrawn = () => {
    setActiveSession(null);
    setCurrentStep('intro');
  };

  const handleSessionCompleted = (session: ApiScreeningSessionResponse) => {
    if (Platform.OS === 'web') {
      alert('Screening session completed successfully!');
    } else {
      Alert.alert('Screening Complete', 'Screening session completed successfully!');
    }
    setActiveSession(null);
    setCurrentStep('history');
  };

  const handleSessionCancelled = (_session: ApiScreeningSessionResponse) => {
    setActiveSession(null);
    setCurrentStep('intro');
  };

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <LoadingIndicator message="Initializing screening workflow..." />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {errorMessage && (
        <View style={styles.errorWrapper}>
          <ErrorMessage
            message={errorMessage}
            onRetry={() => setErrorMessage(null)}
          />
        </View>
      )}

      {currentStep === 'intro' && (
        <ScreeningIntroScreen
          onStartScreening={startScreeningFlow}
          onReviewConsent={() => setCurrentStep('consent')}
          onViewHistory={() => setCurrentStep('history')}
        />
      )}

      {currentStep === 'consent' && (
        <ConsentScreen
          onConsentAccepted={handleConsentAccepted}
          onConsentWithdrawn={handleConsentWithdrawn}
        />
      )}

      {currentStep === 'active_session' && activeSession && (
        <ActiveSessionScreen
          session={activeSession}
          onSessionCompleted={handleSessionCompleted}
          onSessionCancelled={handleSessionCancelled}
        />
      )}

      {currentStep === 'history' && (
        <SessionHistoryScreen
          onBackToIntro={() => setCurrentStep('intro')}
          onSelectSession={(session) => {
            if (session.status === 'in_progress') {
              setActiveSession(session);
              setCurrentStep('active_session');
            }
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8FAFC',
    padding: 20,
  },
  errorWrapper: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#FEE2E2',
  },
});
