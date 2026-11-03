import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Button } from '../../components/Button';
import { SCREENING_CONSTANTS } from '@optiguide/shared';

interface ScreeningIntroScreenProps {
  onStartScreening: () => void;
  onViewHistory: () => void;
  onReviewConsent: () => void;
}

export const ScreeningIntroScreen: React.FC<ScreeningIntroScreenProps> = ({
  onStartScreening,
  onViewHistory,
  onReviewConsent,
}) => {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <Text style={styles.title}>Preliminary Vision Screening</Text>
      <Text style={styles.subtitle}>
        Quick, accessible screening checks to assess visual acuity and provide eyewear guidance.
      </Text>

      {/* Medical Safeguard Box */}
      <View style={styles.disclaimerCard}>
        <Text style={styles.disclaimerTitle}>Non-Diagnostic Tool</Text>
        <Text style={styles.disclaimerBody}>{SCREENING_CONSTANTS.CLINICAL_DISCLAIMER_TEXT}</Text>
      </View>

      {/* What to Expect Section */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>What the Screening Covers</Text>

        <View style={styles.stepItem}>
          <View style={styles.stepBadge}><Text style={styles.stepBadgeText}>1</Text></View>
          <View style={styles.stepContent}>
            <Text style={styles.stepHeader}>Distance Visual Acuity</Text>
            <Text style={styles.stepDescription}>Measures Snellen equivalent acuity at standard calibration distance.</Text>
          </View>
        </View>

        <View style={styles.stepItem}>
          <View style={styles.stepBadge}><Text style={styles.stepBadgeText}>2</Text></View>
          <View style={styles.stepContent}>
            <Text style={styles.stepHeader}>Near Reading Vision</Text>
            <Text style={styles.stepDescription}>Screening for reading comfort and potential presbyopia symptoms.</Text>
          </View>
        </View>

        <View style={styles.stepItem}>
          <View style={styles.stepBadge}><Text style={styles.stepBadgeText}>3</Text></View>
          <View style={styles.stepContent}>
            <Text style={styles.stepHeader}>Astigmatism & Color Sensitivity</Text>
            <Text style={styles.stepDescription}>Preliminary checks for axis blur and basic color discrimination.</Text>
          </View>
        </View>
      </View>

      {/* Preparation Tips */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Before You Begin</Text>
        <Text style={styles.tipItem}>• Ensure you are in a well-lit room without harsh glare.</Text>
        <Text style={styles.tipItem}>• Keep your device at eye level and arm's length.</Text>
        <Text style={styles.tipItem}>• Wear your regular glasses or contacts if you usually wear them.</Text>
        <Text style={styles.tipItem}>• You can pause or cancel the test at any time.</Text>
      </View>

      {/* Action Buttons */}
      <View style={styles.buttonContainer}>
        <Button
          title="Start Vision Screening"
          onPress={onStartScreening}
          variant="primary"
          accessibilityLabel="Start vision screening button"
        />
        <Button
          title="Review Informed Consent"
          onPress={onReviewConsent}
          variant="outline"
          accessibilityLabel="Review consent document button"
          style={styles.secondaryButton}
        />
        <Button
          title="View Past Screening History"
          onPress={onViewHistory}
          variant="secondary"
          accessibilityLabel="View session history button"
          style={styles.secondaryButton}
        />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  title: {
    fontSize: 26,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: '#475569',
    marginBottom: 20,
  },
  disclaimerCard: {
    backgroundColor: '#EFF6FF',
    borderLeftWidth: 4,
    borderLeftColor: '#3B82F6',
    padding: 16,
    borderRadius: 8,
    marginBottom: 20,
  },
  disclaimerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1E40AF',
    marginBottom: 4,
  },
  disclaimerBody: {
    fontSize: 13,
    lineHeight: 19,
    color: '#1E3A8A',
  },
  sectionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 14,
  },
  stepItem: {
    flexDirection: 'row',
    marginBottom: 14,
  },
  stepBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#EEF2FF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  stepBadgeText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#4F46E5',
  },
  stepContent: {
    flex: 1,
  },
  stepHeader: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 2,
  },
  stepDescription: {
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
  },
  tipItem: {
    fontSize: 14,
    lineHeight: 22,
    color: '#334155',
    marginBottom: 6,
  },
  buttonContainer: {
    marginTop: 10,
  },
  secondaryButton: {
    marginTop: 12,
  },
});

export default ScreeningIntroScreen;
