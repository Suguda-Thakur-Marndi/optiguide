import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { ScreenContainer } from '../../src/components/ScreenContainer';
import { Button } from '../../src/components/Button';
import { TextField } from '../../src/components/TextField';
import { ErrorMessage } from '../../src/components/ErrorMessage';
import { LoadingIndicator } from '../../src/components/LoadingIndicator';
import apiClient from '../../src/services/apiClient';
import { colors, spacing, typography, borderRadius, elevation } from '../../src/theme/tokens';
import { ApiUserProfileResponse, ApiSessionItem } from '@optiguide/shared';

interface ProfileIndexProps {
  onBack?: () => void;
  onLogout?: () => void;
}

export default function ProfileIndex({ onBack, onLogout }: ProfileIndexProps) {
  const [user, setUser] = useState<ApiUserProfileResponse | null>(null);
  const [sessions, setSessions] = useState<ApiSessionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form states
  const [fullName, setFullName] = useState<string>('');
  const [phoneNumber, setPhoneNumber] = useState<string>('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [userData, sessionsData] = await Promise.all([
        apiClient.getMe(),
        apiClient.getUserSessions().catch(() => []),
      ]);
      setUser(userData);
      setFullName(userData.full_name);
      setPhoneNumber(userData.phone_number || '');
      setSessions(sessionsData);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load profile data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleUpdateProfile = async () => {
    setSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      const updated = await apiClient.updateProfile({
        full_name: fullName.trim(),
        phone_number: phoneNumber.trim() || undefined,
      });
      setUser(updated);
      setSuccessMessage('Profile updated successfully.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiClient.logout();
    } finally {
      if (onLogout) onLogout();
      else if (onBack) onBack();
    }
  };

  const handleLogoutAll = async () => {
    try {
      await apiClient.logoutAll();
    } finally {
      if (onLogout) onLogout();
      else if (onBack) onBack();
    }
  };

  if (loading) {
    return (
      <ScreenContainer>
        <LoadingIndicator message="Loading profile and session history..." />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
        {onBack && (
          <View style={styles.topBar}>
            <Button title="← Back" variant="outline" size="sm" onPress={onBack} />
          </View>
        )}

        {errorMessage && (
          <ErrorMessage
            message={errorMessage}
            code="PROFILE_ERROR"
            onRetry={loadData}
          />
        )}

        {successMessage && (
          <View style={styles.successBanner}>
            <Text style={styles.successText}>✓ {successMessage}</Text>
          </View>
        )}

        {user ? (
          <>
            {/* Profile Overview Card */}
            <View style={styles.card}>
              <View style={styles.headerRow}>
                <View>
                  <Text style={styles.heading}>{user.full_name}</Text>
                  <Text style={styles.emailText}>{user.email}</Text>
                </View>
                <View style={styles.roleBadge}>
                  <Text style={styles.roleText}>{user.role.toUpperCase()}</Text>
                </View>
              </View>

              <View style={styles.divider} />

              <TextField
                label="Full Name"
                value={fullName}
                onChangeText={setFullName}
                placeholder="Your Full Name"
              />

              <TextField
                label="Phone Number"
                value={phoneNumber}
                onChangeText={setPhoneNumber}
                placeholder="+1 555-0199"
                keyboardType="phone-pad"
              />

              <Button
                title={saving ? 'Saving...' : 'Save Profile Changes'}
                variant="primary"
                onPress={handleUpdateProfile}
                disabled={saving}
                style={styles.saveBtn}
              />
            </View>

            {/* Active Sessions Card */}
            <View style={styles.card}>
              <Text style={styles.subheading}>Login Sessions ({sessions.length})</Text>
              <Text style={styles.caption}>
                Track your active logins across devices and browsers.
              </Text>

              {sessions.length > 0 ? (
                sessions.map((sess) => (
                  <View key={sess.id} style={styles.sessionItem}>
                    <View style={styles.sessionInfo}>
                      <Text style={styles.sessionDevice}>
                        {sess.user_agent ? sess.user_agent.slice(0, 40) : 'Mobile / Native Device'}
                      </Text>
                      <Text style={styles.sessionMeta}>
                        Created: {new Date(sess.created_at).toLocaleDateString()} • {sess.is_revoked ? 'Revoked' : 'Active'}
                      </Text>
                    </View>
                    <View style={sess.is_revoked ? styles.revokedBadge : styles.activeBadge}>
                      <Text style={sess.is_revoked ? styles.revokedBadgeText : styles.activeBadgeText}>
                        {sess.is_revoked ? 'REVOKED' : 'ACTIVE'}
                      </Text>
                    </View>
                  </View>
                ))
              ) : (
                <Text style={styles.emptyText}>No other active sessions found.</Text>
              )}

              <View style={styles.logoutGroup}>
                <Button
                  title="Sign Out Current Session"
                  variant="outline"
                  onPress={handleLogout}
                  style={styles.actionBtn}
                />
                <Button
                  title="Sign Out Everywhere"
                  variant="danger"
                  onPress={handleLogoutAll}
                  style={styles.actionBtn}
                />
              </View>
            </View>
          </>
        ) : (
          <View style={styles.card}>
            <Text style={styles.emptyText}>No profile information available. Please sign in.</Text>
          </View>
        )}
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
    marginBottom: spacing.base,
    ...elevation.low,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  heading: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.neutral[900],
  },
  emailText: {
    fontSize: typography.fontSize.sm,
    color: colors.neutral[500],
    marginTop: spacing.xs,
  },
  roleBadge: {
    backgroundColor: colors.primary[100],
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  roleText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary[700],
  },
  divider: {
    height: 1,
    backgroundColor: colors.neutral[200],
    marginVertical: spacing.md,
  },
  saveBtn: {
    marginTop: spacing.sm,
  },
  subheading: {
    fontSize: typography.fontSize.base,
    fontWeight: typography.fontWeight.bold,
    color: colors.neutral[900],
    marginBottom: spacing.xs,
  },
  caption: {
    fontSize: typography.fontSize.xs,
    color: colors.neutral[500],
    marginBottom: spacing.md,
  },
  sessionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.neutral[100],
  },
  sessionInfo: {
    flex: 1,
  },
  sessionDevice: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
    color: colors.neutral[800],
  },
  sessionMeta: {
    fontSize: typography.fontSize.xs,
    color: colors.neutral[400],
    marginTop: 2,
  },
  activeBadge: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
  },
  activeBadgeText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
    color: '#065F46',
  },
  revokedBadge: {
    backgroundColor: colors.neutral[100],
    paddingHorizontal: spacing.xs,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
  },
  revokedBadgeText: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.bold,
    color: colors.neutral[500],
  },
  emptyText: {
    fontSize: typography.fontSize.sm,
    color: colors.neutral[500],
    textAlign: 'center',
    paddingVertical: spacing.md,
  },
  logoutGroup: {
    marginTop: spacing.lg,
    gap: spacing.sm,
  },
  actionBtn: {
    width: '100%',
  },
  successBanner: {
    backgroundColor: '#ECFDF5',
    borderWidth: 1,
    borderColor: '#10B981',
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.base,
  },
  successText: {
    color: '#065F46',
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.medium,
  },
});
