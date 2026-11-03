import React, { useState, useEffect, useCallback } from 'react';
import { HomeScreen } from './src/screens/HomeScreen';
import { DiagnosticsScreen } from './src/screens/DiagnosticsScreen';
import ScreeningIndex from './app/screening/index';
import LoginScreen from './app/(auth)/login';
import ProfileIndex from './app/profile/index';
import apiClient from './src/services/apiClient';
import { ApiUserProfileResponse } from '@optiguide/shared';

export type ActiveScreen = 'home' | 'diagnostics' | 'screening' | 'login' | 'profile';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<ActiveScreen>('home');
  const [currentUser, setCurrentUser] = useState<ApiUserProfileResponse | null>(null);

  const fetchUser = useCallback(async () => {
    if (apiClient.getAuthToken()) {
      try {
        const user = await apiClient.getMe();
        setCurrentUser(user);
      } catch {
        setCurrentUser(null);
      }
    } else {
      setCurrentUser(null);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  if (currentScreen === 'diagnostics') {
    return <DiagnosticsScreen onBack={() => setCurrentScreen('home')} />;
  }

  if (currentScreen === 'screening') {
    return <ScreeningIndex onBack={() => setCurrentScreen('home')} />;
  }

  if (currentScreen === 'login') {
    return (
      <LoginScreen
        onSuccess={(user) => {
          setCurrentUser(user);
          setCurrentScreen('home');
        }}
        onBack={() => setCurrentScreen('home')}
      />
    );
  }

  if (currentScreen === 'profile') {
    return (
      <ProfileIndex
        onBack={() => setCurrentScreen('home')}
        onLogout={() => {
          setCurrentUser(null);
          setCurrentScreen('home');
        }}
      />
    );
  }

  return (
    <HomeScreen
      currentUser={currentUser}
      onNavigateToDiagnostics={() => setCurrentScreen('diagnostics')}
      onNavigateToScreening={() => setCurrentScreen('screening')}
      onNavigateToLogin={() => setCurrentScreen('login')}
      onNavigateToProfile={() => setCurrentScreen('profile')}
    />
  );
}
