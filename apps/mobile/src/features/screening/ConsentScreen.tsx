import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  Platform,
} from 'react-native';
import { ConsentStatusResponse, SCREENING_CONSTANTS } from '@optiguide/shared';
import apiClient from '../../services/apiClient';
import { Button } from '../../components/Button';
import { LoadingIndicator } from '../../components/LoadingIndicator';
import { ErrorMessage } from '../../components/ErrorMessage';

interface ConsentScreenProps {
  onConsentAccepted?: () => void;
  onConsentWithdrawn?: () => void;
}

export const ConsentScreen: React.FC<ConsentScreenProps> = ({
  onConsentAccepted,
  onConsentWithdrawn,
}) => {
  const [consentState, setConsentState] = useState<ConsentStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const loadConsent = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await apiClient.getScreeningConsent();
      setConsentState(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Unable to retrieve screening consent. Please check connection.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadConsent();
  }, []);

  const handleAccept = async () => {
    if (!consentState) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await apiClient.acceptScreeningConsent(consentState.version);
      setSuccessNotice('Informed consent accepted successfully.');
      await loadConsent();
      if (onConsentAccepted) {
        onConsentAccepted();
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to record consent acceptance.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleWithdraw = async () => {
    const confirmWithdraw = () => {
      setIsSubmitting(true);
      setErrorMessage(null);
      apiClient
        .withdrawScreeningConsent()
        .then(() => {
          setSuccessNotice('Consent has been withdrawn. Active screening sessions have been cancelled.');
          loadConsent();
          if (onConsentWithdrawn) {
            onConsentWithdrawn();
          }
        })
        .catch((err: any) => {
          setErrorMessage(err.message || 'Failed to withdraw consent.');
        })
        .finally(() => {
          setIsSubmitting(false);
        });
    };

    if (Platform.OS === 'web') {
      if (window.confirm('Are you sure you want to withdraw your screening consent? Ongoing tests will be stopped.')) {
        confirmWithdraw();
      }
    } else {
      Alert.alert(
        'Withdraw Consent',
        'Are you sure you want to withdraw your screening consent? Ongoing screening sessions will be cancelled immediately.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Withdraw', style: 'destructive', onPress: confirmWithdraw },
        ]
      );
    }
  };

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <LoadingIndicator message="Loading screening disclosure and consent..." />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      <Text style={styles.headerTitle}>Informed Consent & Medical Disclosure</Text>
      <Text style={styles.versionBadge}>Document Version {consentState?.version || '1.0.0'}</Text>

      {/* Mandatory Non-Diagnostic Disclaimer Box */}
      <View style={styles.disclaimerBox} accessibilityRole="alert">
        <Text style={styles.disclaimerHeader}>Important Medical Notice</Text>
        <Text style={styles.disclaimerText}>{SCREENING_CONSTANTS.CLINICAL_DISCLAIMER_TEXT}</Text>
      </View>

      {errorMessage && (
        <ErrorMessage
          message={errorMessage}
          onRetry={loadConsent}
          style={styles.messageMargin}
        />
      )}

      {successNotice && (
        <View style={styles.successBox}>
          <Text style={styles.successText}>{successNotice}</Text>
        </View>
      )}

      {/* Consent Document Text */}
      <View style={styles.consentDocumentCard}>
        <Text style={styles.consentText}>
          {consentState?.content || 'Loading official disclosure...'}
        </Text>
      </View>

      {/* Consent State Status Pill */}
      <View style={styles.statusRow}>
        <Text style={styles.statusLabel}>Consent Status:</Text>
        <View
          style={[
            styles.statusPill,
            consentState?.is_active ? styles.statusPillActive : styles.statusPillInactive,
          ]}
        >
          <Text
            style={[
              styles.statusPillText,
              consentState?.is_active ? styles.statusPillTextActive : styles.statusPillTextInactive,
            ]}
          >
            {consentState?.is_active ? 'Active & Accepted' : 'Consent Not Given'}
          </Text>
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionsContainer}>
        {!consentState?.is_active ? (
          <Button
            title="I Understand & Accept Consent"
            onPress={handleAccept}
            loading={isSubmitting}
            variant="primary"
            accessibilityLabel="Accept informed consent button"
          />
        ) : (
          <View style={styles.activeActions}>
            <Text style={styles.alreadyActiveNotice}>
              You have already accepted consent for preliminary vision screening.
            </Text>
            <Button
              title="Continue to Screening"
              onPress={() => onConsentAccepted && onConsentAccepted()}
              variant="primary"
              accessibilityLabel="Proceed to screening session button"
              style={styles.actionGap}
            />
            <Button
              title="Withdraw Consent"
              onPress={handleWithdraw}
              variant="outline"
              loading={isSubmitting}
              accessibilityLabel="Withdraw informed consent button"
              style={styles.actionGap}
            />
          </View>
        )}
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
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#F8FAFC',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  versionBadge: {
    fontSize: 13,
    color: '#64748B',
    marginBottom: 16,
    fontWeight: '500',
  },
  disclaimerBox: {
    backgroundColor: '#FEF3C7',
    borderLeftWidth: 4,
    borderLeftColor: '#F59E0B',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  disclaimerHeader: {
    fontSize: 15,
    fontWeight: '700',
    color: '#92400E',
    marginBottom: 6,
  },
  disclaimerText: {
    fontSize: 13,
    lineHeight: 20,
    color: '#78350F',
  },
  consentDocumentCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
  },
  consentText: {
    fontSize: 14,
    lineHeight: 22,
    color: '#334155',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
  },
  statusLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1E293B',
  },
  statusPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  statusPillActive: {
    backgroundColor: '#DCFCE7',
  },
  statusPillInactive: {
    backgroundColor: '#FEE2E2',
  },
  statusPillText: {
    fontSize: 13,
    fontWeight: '600',
  },
  statusPillTextActive: {
    color: '#166534',
  },
  statusPillTextInactive: {
    color: '#991B1B',
  },
  actionsContainer: {
    marginTop: 8,
  },
  activeActions: {
    width: '100%',
  },
  alreadyActiveNotice: {
    fontSize: 14,
    color: '#059669',
    textAlign: 'center',
    marginBottom: 14,
    fontWeight: '500',
  },
  actionGap: {
    marginTop: 10,
  },
  messageMargin: {
    marginBottom: 14,
  },
  successBox: {
    backgroundColor: '#ECFDF5',
    borderColor: '#10B981',
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  successText: {
    color: '#065F46',
    fontSize: 14,
    fontWeight: '500',
  },
});

export default ConsentScreen;
