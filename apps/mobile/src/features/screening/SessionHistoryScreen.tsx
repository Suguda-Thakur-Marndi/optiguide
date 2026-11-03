import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, Platform } from 'react-native';
import { ApiScreeningSessionResponse } from '@optiguide/shared';
import apiClient from '../../services/apiClient';
import { Button } from '../../components/Button';
import { LoadingIndicator } from '../../components/LoadingIndicator';
import { ErrorMessage } from '../../components/ErrorMessage';

interface SessionHistoryScreenProps {
  onBackToIntro: () => void;
  onSelectSession?: (session: ApiScreeningSessionResponse) => void;
}

export const SessionHistoryScreen: React.FC<SessionHistoryScreenProps> = ({
  onBackToIntro,
  onSelectSession,
}) => {
  const [sessions, setSessions] = useState<ApiScreeningSessionResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchHistory = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await apiClient.listScreeningSessions();
      setSessions(data.items);
      setTotal(data.total);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to load screening session history.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return { style: styles.badgeCompleted, text: 'COMPLETED', textStyle: styles.badgeTextCompleted };
      case 'cancelled':
        return { style: styles.badgeCancelled, text: 'CANCELLED', textStyle: styles.badgeTextCancelled };
      case 'in_progress':
      default:
        return { style: styles.badgeInProgress, text: 'IN PROGRESS', textStyle: styles.badgeTextInProgress };
    }
  };

  const renderItem = ({ item }: { item: ApiScreeningSessionResponse }) => {
    const badge = getStatusBadge(item.status);
    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => onSelectSession && onSelectSession(item)}
        accessibilityRole="button"
        accessibilityLabel={`Screening session ${item.id}, status ${item.status}`}
      >
        <View style={styles.cardHeader}>
          <Text style={styles.sessionId}>ID: {item.id.slice(0, 8)}...</Text>
          <View style={[styles.statusBadge, badge.style]}>
            <Text style={[styles.statusBadgeText, badge.textStyle]}>{badge.text}</Text>
          </View>
        </View>

        <Text style={styles.dateText}>
          Started: {new Date(item.started_at).toLocaleDateString()} at{' '}
          {new Date(item.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>

        {item.completed_at && (
          <Text style={styles.subDateText}>
            Completed: {new Date(item.completed_at).toLocaleDateString()} at{' '}
            {new Date(item.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Text>
        )}

        {item.cancelled_at && (
          <Text style={styles.cancelledText}>
            Cancelled: {item.cancellation_reason || 'user_cancelled'}
          </Text>
        )}
      </TouchableOpacity>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <LoadingIndicator message="Loading screening history..." />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <Text style={styles.title}>Screening History</Text>
        <Text style={styles.countText}>{total} recorded session{total === 1 ? '' : 's'}</Text>
      </View>

      {errorMessage && (
        <ErrorMessage message={errorMessage} onRetry={fetchHistory} style={styles.errorMargin} />
      )}

      {sessions.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyTitle}>No Screening Sessions Yet</Text>
          <Text style={styles.emptySubtitle}>
            When you complete preliminary screening tests, your session timeline will appear here.
          </Text>
          <Button
            title="Start First Screening"
            onPress={onBackToIntro}
            variant="primary"
            style={styles.emptyButton}
          />
        </View>
      ) : (
        <FlatList
          data={sessions}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
        />
      )}

      <View style={styles.footer}>
        <Button
          title="Back to Screening Home"
          onPress={onBackToIntro}
          variant="outline"
          accessibilityLabel="Back to screening home button"
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  topBar: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0F172A',
  },
  countText: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 2,
  },
  errorMargin: {
    marginHorizontal: 20,
    marginBottom: 10,
  },
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sessionId: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  badgeCompleted: {
    backgroundColor: '#DCFCE7',
  },
  badgeCancelled: {
    backgroundColor: '#FEE2E2',
  },
  badgeInProgress: {
    backgroundColor: '#EFF6FF',
  },
  statusBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  badgeTextCompleted: {
    color: '#15803D',
  },
  badgeTextCancelled: {
    color: '#B91C1C',
  },
  badgeTextInProgress: {
    color: '#1D4ED8',
  },
  dateText: {
    fontSize: 13,
    color: '#475569',
    marginBottom: 2,
  },
  subDateText: {
    fontSize: 12,
    color: '#64748B',
  },
  cancelledText: {
    fontSize: 12,
    color: '#EF4444',
    fontStyle: 'italic',
    marginTop: 2,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#F8FAFC',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  emptyButton: {
    minWidth: 200,
  },
  footer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    backgroundColor: '#FFFFFF',
  },
});

export default SessionHistoryScreen;
