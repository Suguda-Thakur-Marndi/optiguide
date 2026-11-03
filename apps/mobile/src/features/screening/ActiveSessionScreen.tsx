import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, Platform } from 'react-native';
import { ApiScreeningSessionResponse } from '@optiguide/shared';
import apiClient from '../../services/apiClient';
import { Button } from '../../components/Button';
import { ErrorMessage } from '../../components/ErrorMessage';

interface ActiveSessionScreenProps {
  session: ApiScreeningSessionResponse;
  onSessionCompleted: (session: ApiScreeningSessionResponse) => void;
  onSessionCancelled: (session: ApiScreeningSessionResponse) => void;
}

export const ActiveSessionScreen: React.FC<ActiveSessionScreenProps> = ({
  session,
  onSessionCompleted,
  onSessionCancelled,
}) => {
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleComplete = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const updated = await apiClient.completeScreeningSession(session.id);
      onSessionCompleted(updated);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to complete screening session.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = async () => {
    const executeCancel = (reason?: string) => {
      setIsSubmitting(true);
      setErrorMessage(null);
      apiClient
        .cancelScreeningSession(session.id, reason)
        .then((updated) => {
          onSessionCancelled(updated);
        })
        .catch((err: any) => {
          setErrorMessage(err.message || 'Failed to cancel screening session.');
        })
        .finally(() => {
          setIsSubmitting(false);
        });
    };

    if (Platform.OS === 'web') {
      const confirmed = window.confirm('Are you sure you want to cancel this vision screening session?');
      if (confirmed) {
        executeCancel('User cancelled from web interface.');
      }
    } else {
      Alert.alert(
        'Cancel Screening Session',
        'Are you sure you want to cancel this session? You will be able to start a new screening whenever you are ready.',
        [
          { text: 'Keep Screening', style: 'cancel' },
          {
            text: 'Yes, Cancel',
            style: 'destructive',
            onPress: () => executeCancel('User cancelled from mobile interface.'),
          },
        ]
      );
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Session Status Banner */}
      <View style={styles.sessionCard}>
        <View style={styles.badgeRow}>
          <Text style={styles.sessionTitle}>Screening Session Active</Text>
          <View style={styles.activePill}>
            <Text style={styles.activePillText}>IN PROGRESS</Text>
          </View>
        </View>

        <Text style={styles.sessionId}>ID: {session.id}</Text>
        <Text style={styles.timestamp}>Started: {new Date(session.started_at).toLocaleString()}</Text>
      </View>

      {errorMessage && (
        <ErrorMessage message={errorMessage} style={styles.errorMargin} />
      )}

      {/* Phase 3.1 Architecture Milestone Info */}
      <View style={styles.moduleCard}>
        <Text style={styles.moduleTitle}>Screening Session Foundation (Phase 3.1)</Text>
        <Text style={styles.moduleBody}>
          Informed consent is verified, session lifecycle state is active, and privacy-conscious audit telemetry is recording.
        </Text>
        <View style={styles.upcomingBox}>
          <Text style={styles.upcomingTitle}>Upcoming Screening Modules (Phase 3.2):</Text>
          <Text style={styles.upcomingItem}>• Distance Visual Acuity (Tumbling E Chart)</Text>
          <Text style={styles.upcomingItem}>• Near Vision Reading Verification</Text>
          <Text style={styles.upcomingItem}>• Astigmatism Dial Assessment</Text>
          <Text style={styles.upcomingItem}>• Color Discrimination Screening</Text>
        </View>
      </View>

      {/* Action Controls */}
      <View style={styles.actions}>
        <Button
          title="Complete Screening Session"
          onPress={handleComplete}
          loading={isSubmitting}
          variant="primary"
          accessibilityLabel="Complete screening session button"
        />
        <Button
          title="Cancel Session"
          onPress={handleCancel}
          loading={isSubmitting}
          variant="outline"
          accessibilityLabel="Cancel screening session button"
          style={styles.cancelButton}
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
  sessionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
  },
  badgeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sessionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
  },
  activePill: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  activePillText: {
    color: '#2563EB',
    fontSize: 12,
    fontWeight: '700',
  },
  sessionId: {
    fontSize: 13,
    color: '#64748B',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 4,
  },
  timestamp: {
    fontSize: 13,
    color: '#475569',
  },
  moduleCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 24,
  },
  moduleTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 8,
  },
  moduleBody: {
    fontSize: 14,
    lineHeight: 21,
    color: '#475569',
    marginBottom: 14,
  },
  upcomingBox: {
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    padding: 12,
  },
  upcomingTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#334155',
    marginBottom: 6,
  },
  upcomingItem: {
    fontSize: 13,
    color: '#475569',
    lineHeight: 20,
  },
  actions: {
    marginTop: 8,
  },
  cancelButton: {
    marginTop: 12,
  },
  errorMargin: {
    marginBottom: 16,
  },
});

export default ActiveSessionScreen;
