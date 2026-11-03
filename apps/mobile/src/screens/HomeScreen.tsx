import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { ScreenContainer } from '../components/ScreenContainer';
import { Button } from '../components/Button';
import { colors, spacing, typography, borderRadius, elevation } from '../theme/tokens';
import { ApiUserProfileResponse } from '@optiguide/shared';

export interface HomeScreenProps {
  onNavigateToDiagnostics: () => void;
  onNavigateToScreening?: () => void;
  onNavigateToLogin?: () => void;
  onNavigateToProfile?: () => void;
  currentUser?: ApiUserProfileResponse | null;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  onNavigateToDiagnostics,
  onNavigateToScreening,
  onNavigateToLogin,
  onNavigateToProfile,
  currentUser,
}) => {
  return (
    <ScreenContainer>
      {/* Header & User Navigation */}
      <View style={styles.header}>
        <View style={styles.headerTopRow}>
          <View style={styles.logoBadge}>
            <Text style={styles.logoText}>👁️ OptiGuide</Text>
          </View>
          {currentUser ? (
            <Button
              title={`👤 ${currentUser.full_name}`}
              variant="outline"
              size="sm"
              onPress={onNavigateToProfile || (() => {})}
            />
          ) : (
            <Button
              title="Sign In"
              variant="outline"
              size="sm"
              onPress={onNavigateToLogin || (() => {})}
            />
          )}
        </View>
        <Text style={styles.heading}>Vision Screening & Guidance</Text>
        <Text style={styles.subheading}>
          Accurate, accessible optical guidance and visual acuity assistance.
        </Text>
      </View>

      {/* Prominent Clinical Disclaimer Banner */}
      <View style={styles.disclaimerBanner} accessibilityRole="alert">
        <Text style={styles.disclaimerTitle}>⚠️ Important Medical Notice</Text>
        <Text style={styles.disclaimerBody}>
          OptiGuide is a preliminary vision screening and eyewear guidance platform. It is not a diagnostic system and must not independently prescribe lens power. Qualified eye-care professionals must confirm prescriptions and clinical decisions.
        </Text>
      </View>

      {/* Main Feature Cards / Placeholders */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Preliminary Screening</Text>
        <Text style={styles.cardBody}>
          Standardized visual acuity checks, color perception indicators, and contrast sensitivity assessment.
        </Text>
        <Button
          title="Start Screening"
          variant="primary"
          disabled={false}
          onPress={onNavigateToScreening || (() => {})}
          style={styles.cardAction}
        />
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Eyewear & Frame Assistant</Text>
        <Text style={styles.cardBody}>
          Facial dimension guidance, lens type recommendations, and ergonomic frame fitting options.
        </Text>
        <Button
          title="Explore Guidance (Phase 2)"
          variant="outline"
          disabled={true}
          onPress={() => {}}
          style={styles.cardAction}
        />
      </View>

      {/* Language Placeholder */}
      <View style={styles.secondarySection}>
        <Text style={styles.sectionLabel}>Language Support</Text>
        <View style={styles.languagePill}>
          <Text style={styles.languageText}>English (Default) • Multilingual support coming soon</Text>
        </View>
      </View>

      {/* Developer / System Diagnostics Navigation */}
      <View style={styles.diagnosticSection}>
        <Text style={styles.sectionLabel}>System Architecture & Health</Text>
        <Button
          title="Open API & Database Diagnostics"
          variant="secondary"
          onPress={onNavigateToDiagnostics}
          testID="btn-open-diagnostics"
        />
      </View>
    </ScreenContainer>
  );
};

const styles = StyleSheet.create({
  header: {
    marginBottom: spacing.xl,
    alignItems: 'stretch',
  },
  headerTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  logoBadge: {
    backgroundColor: colors.primary[100],
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    marginBottom: spacing.md,
  },
  logoText: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.bold,
    color: colors.primary[700],
  },
  heading: {
    fontSize: typography.fontSize['3xl'],
    fontWeight: typography.fontWeight.bold,
    color: colors.neutral[900],
    marginBottom: spacing.xs,
  },
  subheading: {
    fontSize: typography.fontSize.base,
    color: colors.neutral[600],
    lineHeight: 22,
  },
  disclaimerBanner: {
    backgroundColor: colors.status.warningBg,
    borderColor: colors.status.warning,
    borderWidth: 1.5,
    borderRadius: borderRadius.md,
    padding: spacing.base,
    marginBottom: spacing.xl,
  },
  disclaimerTitle: {
    fontSize: typography.fontSize.sm,
    fontWeight: typography.fontWeight.bold,
    color: colors.status.warning,
    marginBottom: spacing.xs,
  },
  disclaimerBody: {
    fontSize: typography.fontSize.xs,
    color: colors.neutral[800],
    lineHeight: 18,
  },
  card: {
    backgroundColor: colors.neutral.white,
    borderRadius: borderRadius.lg,
    padding: spacing.xl,
    marginBottom: spacing.base,
    ...elevation.low,
  },
  cardTitle: {
    fontSize: typography.fontSize.lg,
    fontWeight: typography.fontWeight.bold,
    color: colors.neutral[900],
    marginBottom: spacing.xs,
  },
  cardBody: {
    fontSize: typography.fontSize.sm,
    color: colors.neutral[600],
    marginBottom: spacing.base,
    lineHeight: 20,
  },
  cardAction: {
    alignSelf: 'stretch',
  },
  secondarySection: {
    marginVertical: spacing.md,
  },
  sectionLabel: {
    fontSize: typography.fontSize.xs,
    fontWeight: typography.fontWeight.semibold,
    color: colors.neutral[500],
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: spacing.xs,
  },
  languagePill: {
    backgroundColor: colors.neutral[200],
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
  },
  languageText: {
    fontSize: typography.fontSize.xs,
    color: colors.neutral[700],
  },
  diagnosticSection: {
    marginTop: spacing.xl,
    paddingTop: spacing.base,
    borderTopWidth: 1,
    borderTopColor: colors.neutral[200],
  },
});
