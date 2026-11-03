import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { ScreenContainer } from '../../src/components/ScreenContainer';
import { Button } from '../../src/components/Button';
import { TextField } from '../../src/components/TextField';
import { ErrorMessage } from '../../src/components/ErrorMessage';
import { LoadingIndicator } from '../../src/components/LoadingIndicator';
import apiClient from '../../src/services/apiClient';
import { colors, spacing, typography, borderRadius, elevation } from '../../src/theme/tokens';
import { ApiUserProfileResponse } from '@optiguide/shared';

interface LoginScreenProps {
  onSuccess?: (user: ApiUserProfileResponse) => void;
  onBack?: () => void;
}

export default function LoginScreen({ onSuccess, onBack }: LoginScreenProps) {
  const [isRegistering, setIsRegistering] = useState<boolean>(false);
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [fullName, setFullName] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string; fullName?: string }>({});

  const validate = (): boolean => {
    const errors: { email?: string; password?: string; fullName?: string } = {};
    if (!email.trim()) {
      errors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      errors.email = 'Please enter a valid email address.';
    }

    if (!password) {
      errors.password = 'Password is required.';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters.';
    }

    if (isRegistering && !fullName.trim()) {
      errors.fullName = 'Full name is required.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    setErrorMessage(null);
    if (!validate()) return;

    setLoading(true);
    try {
      if (isRegistering) {
        const res = await apiClient.register({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
        });
        if (onSuccess) onSuccess(res.user);
      } else {
        const res = await apiClient.login({
          email: email.trim(),
          password,
        });
        if (onSuccess) onSuccess(res.user);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
        {onBack && (
          <View style={styles.topBar}>
            <Button title="← Back" variant="outline" size="sm" onPress={onBack} />
          </View>
        )}

        <View style={styles.card}>
          <Text style={styles.brandTitle}>👁️ OptiGuide</Text>
          <Text style={styles.heading}>{isRegistering ? 'Create Patient Account' : 'Sign In to OptiGuide'}</Text>
          <Text style={styles.subheading}>
            {isRegistering
              ? 'Access preliminary vision screening sessions and track your screening timeline.'
              : 'Sign in to access your consent status and active vision screenings.'}
          </Text>

          {/* Tab Selector */}
          <View style={styles.tabRow}>
            <Button
              title="Sign In"
              variant={!isRegistering ? 'primary' : 'outline'}
              size="sm"
              onPress={() => {
                setIsRegistering(false);
                setErrorMessage(null);
                setFieldErrors({});
              }}
              style={styles.tabButton}
            />
            <Button
              title="Create Account"
              variant={isRegistering ? 'primary' : 'outline'}
              size="sm"
              onPress={() => {
                setIsRegistering(true);
                setErrorMessage(null);
                setFieldErrors({});
              }}
              style={styles.tabButton}
            />
          </View>

          {errorMessage && (
            <ErrorMessage
              message={errorMessage}
              code="AUTH_ERROR"
              onRetry={() => setErrorMessage(null)}
            />
          )}

          {isRegistering && (
            <TextField
              label="Full Name"
              placeholder="e.g. Jane Doe"
              value={fullName}
              onChangeText={setFullName}
              error={fieldErrors.fullName}
              autoCapitalize="words"
            />
          )}

          <TextField
            label="Email Address"
            placeholder="patient@example.com"
            value={email}
            onChangeText={setEmail}
            error={fieldErrors.email}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
          />

          <TextField
            label="Password"
            placeholder="••••••••"
            value={password}
            onChangeText={setPassword}
            error={fieldErrors.password}
            secureTextEntry
            autoCapitalize="none"
            helperText={isRegistering ? 'Min 8 chars, 1 uppercase, 1 digit, 1 symbol' : undefined}
          />

          {loading ? (
            <LoadingIndicator message={isRegistering ? 'Creating account...' : 'Signing in...'} />
          ) : (
            <Button
              title={isRegistering ? 'Register Patient Account' : 'Sign In'}
              variant="primary"
              size="lg"
              onPress={handleSubmit}
              style={styles.submitBtn}
            />
          )}
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  scrollContainer: {
    paddingBottom: spacing['2xl'],
  },
  topBar: {
    marginBottom: spacing.base,
    alignItems: 'flex-start',
  },
  card: {
    backgroundColor: colors.neutral.white,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    ...elevation.medium,
  },
  brandTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary[700],
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: spacing.xs,
  },
  heading: {
    fontSize: typography.fontSize.xl,
    fontWeight: typography.fontWeight.bold,
    color: colors.neutral[900],
    marginBottom: spacing.xs,
  },
  subheading: {
    fontSize: typography.fontSize.sm,
    color: colors.neutral[600],
    lineHeight: 20,
    marginBottom: spacing.lg,
  },
  tabRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  tabButton: {
    flex: 1,
  },
  submitBtn: {
    marginTop: spacing.md,
  },
});
