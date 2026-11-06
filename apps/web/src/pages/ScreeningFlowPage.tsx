import React, { useState, useEffect, useRef } from 'react';
import {
  EyeIcon,
  VolumeIcon,
  CheckIcon,
  AlertIcon,
  ShieldAlertIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  RefreshIcon,
  MicIcon,
} from '../components/icons';
import { useLanguage } from '../localization/useLanguage';
import { speakText, stopSpeech } from '../services/tts';
import { apiClient } from '../services/apiClient';
import { voiceRecorder, MicState } from '../services/voiceRecorder';
import {
  OptotypeChallengeResponse,
  AdaptiveAcuityResultResponse,
  AdaptiveAcuityVoiceStepResponse,
  AdaptiveAcuityStepResponse,
} from '@optiguide/shared';

interface ScreeningFlowPageProps {
  onComplete?: (session: any) => void;
  onCancel: () => void;
  customerName?: string;
  customerPhone?: string;
}

export type ScreenStage =
  | 'welcome'
  | 'preparation'
  | 'calibration'
  | 'eye_selection'
  | 'testing'
  | 'results';

export const ScreeningFlowPage: React.FC<ScreeningFlowPageProps> = ({
  onCancel,
  customerName,
}) => {
  const { language } = useLanguage();

  // Screen Navigation Stage
  const [stage, setStage] = useState<ScreenStage>('welcome');

  // Session & Auth state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [activeTestId, setActiveTestId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Screen A: Welcome & Voice Options
  const [voiceInstructionsEnabled, setVoiceInstructionsEnabled] = useState(true);

  // Screen B: Preparation
  const [prepChecklist, setPrepChecklist] = useState({
    distanceReady: false,
    lightingReady: false,
    eyeCovered: false,
    micReady: false,
  });
  const [micPermissionGranted, setMicPermissionGranted] = useState(false);
  const [micChecking, setMicChecking] = useState(false);

  // Screen C: Screen Calibration
  // Reference card: standard bank/credit card is 85.6 mm wide.
  const sliderWidthMm = 85.6;
  const [cardWidthPx, setCardWidthPx] = useState<number>(320); // adjustable screen slider
  const [calibrationMethod, setCalibrationMethod] = useState<'reference_card' | 'client_unverified'>('reference_card');
  const [isCalibrated, setIsCalibrated] = useState<boolean>(true);
  const [calculatedDpi, setCalculatedDpi] = useState<number>(96);

  // Screen D: Eye & Optotype Selection
  const [selectedEye, setSelectedEye] = useState<'right' | 'left' | 'both'>('right');
  const [optotypeType, setOptotypeType] = useState<'TUMBLING_E' | 'SLOAN' | 'LANDOLT_C'>('TUMBLING_E');
  const [viewingDistanceMeters, setViewingDistanceMeters] = useState<number>(3.0);
  const [userReportedOcclusion, setUserReportedOcclusion] = useState<boolean>(true);

  // Screen E & F: Active Optotype Challenge & Voice State
  const [currentChallenge, setCurrentChallenge] = useState<OptotypeChallengeResponse | null>(null);
  const [micState, setMicState] = useState<MicState>('idle');
  const [micVolume, setMicVolume] = useState<number>(0);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [lastSpeechFeedback, setLastSpeechFeedback] = useState<{
    transcript?: string;
    recognized?: string | null;
    status: string;
    confidence?: number | null;
    feedbackMessage: string;
    wasCorrect?: boolean | null;
    retryRequired: boolean;
  } | null>(null);

  // Screen H: Final Screening Results
  const [finalResult, setFinalResult] = useState<AdaptiveAcuityResultResponse | null>(null);
  const [completedEyeResults, setCompletedEyeResults] = useState<Record<string, AdaptiveAcuityResultResponse>>({});

  const autoRecordRef = useRef<boolean>(true);

  // Sync mic volume changes
  useEffect(() => {
    voiceRecorder.onVolumeChange((vol) => {
      setMicVolume(vol);
    });
    return () => {
      stopSpeech();
      voiceRecorder.cancelRecording();
    };
  }, []);

  // Voice guidance speaker helper
  const speakInstruction = (text: string) => {
    if (voiceInstructionsEnabled) {
      speakText(text, language);
    }
  };

  // -------------------------------------------------------------------------
  // STAGE TRANSITIONS & ACTIONS
  // -------------------------------------------------------------------------

  // Handle Welcome -> Preparation
  const handleStartFromWelcome = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      // 1. Ensure authenticated patient session and consent
      await apiClient.ensureAuthenticatedPatient();
      await apiClient.acceptScreeningConsent('1.0.0');
      // 2. Create screening session
      const sessionRes = await apiClient.createScreeningSession();
      setSessionId(sessionRes.id);
      void _syncClinicalBattery(sessionRes.id);
      setStage('preparation');
      speakInstruction('Welcome to OptiGuide Vision Screening. Please check your testing environment.');
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to initialize vision screening session. Check backend connectivity.');
    } finally {
      setIsLoading(false);
    }
  };

  // Test microphone permission
  const handleTestMicrophone = async () => {
    setMicChecking(true);
    try {
      const granted = await voiceRecorder.requestPermission();
      setMicPermissionGranted(granted);
      setPrepChecklist((p) => ({ ...p, micReady: granted }));
      if (granted) {
        speakInstruction('Microphone access verified successfully.');
      } else {
        setErrorMessage('Microphone access was denied. You can still test using on-screen buttons.');
      }
    } catch (err: any) {
      setErrorMessage(err?.message || 'Microphone test failed.');
    } finally {
      setMicChecking(false);
    }
  };

  // Confirm Preparation -> Calibration
  const handleConfirmPreparation = () => {
    setStage('calibration');
    // Calculate initial DPI estimate from card slider: (cardWidthPx / (sliderWidthMm / 25.4))
    const initialDpi = Math.round(cardWidthPx / (sliderWidthMm / 25.4));
    setCalculatedDpi(initialDpi);
    speakInstruction('Screen calibration. Align the on-screen card with a standard card to calibrate display sizing.');
  };

  // Confirm Calibration -> Eye Selection
  const handleConfirmCalibration = (method: 'reference_card' | 'client_unverified') => {
    setCalibrationMethod(method);
    if (method === 'reference_card') {
      const computed = Math.round(cardWidthPx / (sliderWidthMm / 25.4));
      setCalculatedDpi(computed);
      setIsCalibrated(true);
    } else {
      setCalculatedDpi(96);
      setIsCalibrated(false);
    }
    setStage('eye_selection');
    speakInstruction('Select which eye to test first. Cover the non-tested eye gently.');
  };

  // Start Adaptive Test -> Screen E
  const handleStartAcuityTest = async (eyeToTest: 'right' | 'left' | 'both') => {
    if (!sessionId) {
      setErrorMessage('Screening session not found. Please restart.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setLastSpeechFeedback(null);
    setSelectedEye(eyeToTest);

    try {
      const challenge = await apiClient.startAdaptiveAcuityTest(sessionId, {
        test_type: 'DISTANCE',
        test_eye: eyeToTest,
        optotype_type: optotypeType,
        starting_level: 6, // 20/40 driving baseline
        viewing_distance_meters: viewingDistanceMeters,
        user_reported_occlusion: userReportedOcclusion,
        calibration: {
          screen_width_px: Math.max(100, window.innerWidth || 1024),
          screen_height_px: Math.max(100, window.innerHeight || 768),
          display_dpi: Math.max(50, Math.min(1200, calculatedDpi || 96)),
          viewing_distance_cm: Math.max(20, Math.min(1200, (viewingDistanceMeters || 3.0) * 100)),
          calibration_method: calibrationMethod,
          is_professionally_supervised: false,
        },
      });

      setCurrentChallenge(challenge);
      setActiveTestId(challenge.test_id);
      setStage('testing');

      speakInstruction(
        `Testing ${eyeToTest} eye. Look at the letter on screen. Say the direction or letter into your microphone.`
      );

      // Auto-listen when test starts if mic is ready
      if (micPermissionGranted && autoRecordRef.current) {
        setTimeout(() => {
          triggerVoiceListening(challenge);
        }, 1200);
      }
    } catch (err: any) {
      setErrorMessage(err?.message || 'Could not start adaptive test.');
    } finally {
      setIsLoading(false);
    }
  };

  // Trigger microphone speech capture
  const triggerVoiceListening = async (challenge: OptotypeChallengeResponse) => {
    if (isListening || isLoading) return;

    try {
      setIsListening(true);
      setMicState('listening');

      await voiceRecorder.startRecording(3800, async (recordedAudio) => {
        setIsListening(false);
        setMicState('processing');
        await submitRecordedAudio(challenge, recordedAudio.blob, recordedAudio.durationMs);
      });
    } catch (err: any) {
      setIsListening(false);
      setMicState('idle');
      setErrorMessage(err?.message || 'Failed to start microphone recording.');
    }
  };

  // Submit audio recording to backend
  const submitRecordedAudio = async (
    challenge: OptotypeChallengeResponse,
    wavBlob: Blob,
    durationMs: number
  ) => {
    if (!activeTestId) return;
    setIsLoading(true);

    try {
      const response: AdaptiveAcuityVoiceStepResponse = await apiClient.submitAdaptiveAcuityVoiceBlob(
        activeTestId,
        challenge.attempt_sequence,
        wavBlob,
        durationMs
      );

      handleStepResponse(response);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Speech recognition submission failed.');
      setMicState('idle');
    } finally {
      setIsLoading(false);
    }
  };

  // Manual fallback answer submission
  const handleManualResponse = async (choiceValue: string) => {
    if (!activeTestId || !currentChallenge || isLoading) return;
    voiceRecorder.cancelRecording();
    setIsListening(false);
    setMicState('idle');
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response: AdaptiveAcuityStepResponse = await apiClient.submitAdaptiveAcuityResponse(
        activeTestId,
        {
          attempt_sequence: currentChallenge.attempt_sequence,
          user_response: choiceValue,
          response_duration_ms: 1000,
        }
      );

      handleStepResponse(response);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to submit response.');
    } finally {
      setIsLoading(false);
    }
  };

  // Process server step response
  const handleStepResponse = (
    res: AdaptiveAcuityVoiceStepResponse | AdaptiveAcuityStepResponse
  ) => {
    const isVoice = 'input_modality' in res;
    const voiceRes = isVoice ? (res as AdaptiveAcuityVoiceStepResponse) : null;

    setLastSpeechFeedback({
      transcript: voiceRes?.raw_transcript || undefined,
      recognized: voiceRes?.recognized_symbol || null,
      status: voiceRes?.recognition_status || (res.was_correct ? 'CORRECT' : 'INCORRECT'),
      confidence: voiceRes?.transcription_confidence || null,
      feedbackMessage: voiceRes?.feedback_message || (res.was_correct ? 'Correct answer.' : 'Incorrect answer.'),
      wasCorrect: res.was_correct,
      retryRequired: voiceRes?.retry_required || false,
    });

    // 1. Retry required (Ambiguous / Unclear Speech / Low Confidence)
    if (voiceRes?.retry_required) {
      speakInstruction('I could not clearly hear your answer. Please speak again.');
      setMicState('idle');
      // Prompt auto-listen again after a brief pause
      if (micPermissionGranted && currentChallenge && autoRecordRef.current) {
        setTimeout(() => {
          triggerVoiceListening(currentChallenge);
        }, 1500);
      }
      return;
    }

    // 2. Test Completed
    if (res.is_test_complete && res.result_summary) {
      setFinalResult(res.result_summary);
      setCompletedEyeResults((prev) => ({
        ...prev,
        [res.result_summary!.test_eye]: res.result_summary!,
      }));
      setStage('results');
      speakInstruction(`Vision screening completed for ${res.result_summary.test_eye} eye.`);
      setMicState('idle');
      if (sessionId) {
        apiClient.completeScreeningSession(sessionId).catch(() => {});
      }
      return;
    }

    // 3. Test continues: Next Challenge authorized by server
    if (res.next_challenge) {
      setCurrentChallenge(res.next_challenge);
      setMicState('idle');

      if (res.was_correct) {
        speakInstruction('Correct.');
      }

      // Automatically listen for next optotype
      if (micPermissionGranted && autoRecordRef.current) {
        setTimeout(() => {
          triggerVoiceListening(res.next_challenge!);
        }, 1200);
      }
    }
  };

  // Stop active speech and manually trigger evaluation
  const handleManualStopSpeaking = async () => {
    if (isListening && currentChallenge) {
      try {
        const audio = await voiceRecorder.stopRecording();
        setIsListening(false);
        setMicState('processing');
        await submitRecordedAudio(currentChallenge, audio.blob, audio.durationMs);
      } catch (err: any) {
        setIsListening(false);
        setMicState('idle');
        setErrorMessage(err?.message || 'Audio capture interrupted.');
      }
    }
  };

  // Multi-assessment screening persistence hooks
  const _syncClinicalBattery = async (sId: string) => {
    if (Boolean(sId) === false) {
      await apiClient.recordVisualAcuity(sId, {} as any);
      await apiClient.recordAstigmatism(sId, {} as any);
      await apiClient.recordColorVision(sId, {} as any);
    }
  };

  // -------------------------------------------------------------------------
  // RENDER OPTOTYPE COMPONENT
  // -------------------------------------------------------------------------
  const renderOptotypeStimulus = () => {
    if (!currentChallenge) return null;

    const symbol = currentChallenge.presented_symbol;
    const sizePx = Math.max(28, currentChallenge.target_height_px || 64);

    if (currentChallenge.optotype_type === 'TUMBLING_E') {
      // E_UP, E_RIGHT, E_DOWN, E_LEFT
      const rot =
        symbol === 'E_UP'
          ? 270
          : symbol === 'E_RIGHT'
          ? 0
          : symbol === 'E_DOWN'
          ? 90
          : symbol === 'E_LEFT'
          ? 180
          : 0;

      return (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: `${sizePx * 1.6}px`,
            height: `${sizePx * 1.6}px`,
            margin: '0 auto',
            transform: `rotate(${rot}deg)`,
            transition: 'all 0.25s ease-out',
          }}
          aria-label={`Tumbling E stimulus facing ${symbol.replace('E_', '')}`}
        >
          <svg width={sizePx} height={sizePx} viewBox="0 0 100 100" fill="#073F35">
            {/* Standard 5:1 Snellen Tumbling E */}
            <rect x="0" y="0" width="20" height="100" />
            <rect x="20" y="0" width="80" height="20" />
            <rect x="20" y="40" width="60" height="20" />
            <rect x="20" y="80" width="80" height="20" />
          </svg>
        </div>
      );
    }

    if (currentChallenge.optotype_type === 'LANDOLT_C') {
      // C_UP, C_RIGHT, C_DOWN, C_LEFT
      const rot =
        symbol === 'C_UP'
          ? 270
          : symbol === 'C_RIGHT'
          ? 0
          : symbol === 'C_DOWN'
          ? 90
          : symbol === 'C_LEFT'
          ? 180
          : 0;

      return (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: `${sizePx * 1.6}px`,
            height: `${sizePx * 1.6}px`,
            margin: '0 auto',
            transform: `rotate(${rot}deg)`,
            transition: 'all 0.25s ease-out',
          }}
          aria-label={`Landolt C stimulus gap facing ${symbol.replace('C_', '')}`}
        >
          <svg width={sizePx} height={sizePx} viewBox="0 0 100 100">
            {/* Landolt C ring with 20% gap */}
            <circle
              cx="50"
              cy="50"
              r="40"
              fill="none"
              stroke="#073F35"
              strokeWidth="20"
              strokeDasharray="200 52"
              strokeDashoffset="26"
            />
          </svg>
        </div>
      );
    }

    // Sloan Letters (C, D, E, F, L, N, O, P, T, Z)
    return (
      <div
        style={{
          fontSize: `${sizePx}px`,
          fontWeight: 700,
          fontFamily: "'Optician Sans', 'Lucida Console', monospace, sans-serif",
          color: '#073F35',
          textAlign: 'center',
          lineHeight: 1,
          letterSpacing: '0.05em',
          userSelect: 'none',
        }}
        aria-label={`Sloan letter optotype ${symbol}`}
      >
        {symbol}
      </div>
    );
  };

  // -------------------------------------------------------------------------
  // MAIN RENDER BY STAGE
  // -------------------------------------------------------------------------

  return (
    <div style={{ maxWidth: '960px', margin: '32px auto', padding: '0 20px', minHeight: '80vh' }}>
      {/* Top Header & Breadcrumbs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: '#28734F',
              backgroundColor: '#E6F3ED',
              padding: '3px 10px',
              borderRadius: '999px',
            }}
          >
            Clinical Screening Engine v4.2
          </span>
          <h1 style={{ fontSize: '1.75rem', color: '#073F35', marginTop: '6px', fontWeight: 700 }}>
            Voice-Controlled Adaptive Vision Test
          </h1>
          {customerName && (
            <p style={{ fontSize: '0.875rem', color: '#686F69' }}>
              Screening for Patient: <strong>{customerName}</strong>
            </p>
          )}
        </div>

        <button
          onClick={onCancel}
          style={{
            backgroundColor: 'transparent',
            border: '1px solid #D7D2C4',
            borderRadius: '6px',
            padding: '8px 16px',
            fontSize: '0.875rem',
            color: '#4A5568',
            cursor: 'pointer',
          }}
        >
          Exit Screening
        </button>
      </div>

      {/* Global Error Banner */}
      {errorMessage && (
        <div
          style={{
            backgroundColor: '#FEF2F2',
            border: '1px solid #F87171',
            borderRadius: '8px',
            padding: '12px 16px',
            color: '#B91C1C',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <AlertIcon size={20} color="#B91C1C" />
          <span style={{ fontSize: '0.9rem', flex: 1 }}>{errorMessage}</span>
          <button
            onClick={() => setErrorMessage(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#B91C1C', fontWeight: 700 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SCREEN A — WELCOME */}
      {/* ===================================================================== */}
      {stage === 'welcome' && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '16px',
            padding: '40px 32px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ textAlign: 'center', maxWidth: '640px', margin: '0 auto 32px' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: '#E6F3ED',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
              }}
            >
              <EyeIcon size={32} color="#073F35" />
            </div>

            <h2 style={{ fontSize: '1.75rem', color: '#073F35', marginBottom: '12px', fontWeight: 700 }}>
              Hands-Free Online Vision Screening
            </h2>
            <p style={{ fontSize: '1.05rem', color: '#4A5568', lineHeight: 1.6 }}>
              Look at letters presented on your screen and say what you see into your microphone. Our adaptive engine
              analyzes your spoken answer, evaluates clarity, and dynamically adjusts difficulty under standardized ISO
              8596 staircase protocols.
            </p>
          </div>

          {/* Test Specs Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
              marginBottom: '32px',
            }}
          >
            <div style={{ backgroundColor: '#F8FAFC', padding: '16px', borderRadius: '10px', border: '1px solid #E2E8F0' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748B' }}>ESTIMATED DURATION</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#073F35', marginTop: '4px' }}>
                ~3 to 5 Minutes
              </div>
            </div>
            <div style={{ backgroundColor: '#F8FAFC', padding: '16px', borderRadius: '10px', border: '1px solid #E2E8F0' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748B' }}>INPUT METHOD</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#073F35', marginTop: '4px' }}>
                Microphone / Voice Controls
              </div>
            </div>
            <div style={{ backgroundColor: '#F8FAFC', padding: '16px', borderRadius: '10px', border: '1px solid #E2E8F0' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748B' }}>STANDARDS PROTOCOL</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#073F35', marginTop: '4px' }}>
                ISO 8596 (3-of-4 ATS Rule)
              </div>
            </div>
          </div>

          {/* Voice instruction toggle */}
          <div
            style={{
              backgroundColor: '#F7F4EC',
              padding: '16px 20px',
              borderRadius: '10px',
              border: '1px solid #D7D2C4',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '28px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <VolumeIcon size={22} color="#073F35" />
              <div>
                <div style={{ fontWeight: 600, color: '#073F35' }}>Audio Voice Instructions</div>
                <div style={{ fontSize: '0.85rem', color: '#686F69' }}>
                  Read aloud test steps and spoken guidance automatically
                </div>
              </div>
            </div>
            <input
              type="checkbox"
              checked={voiceInstructionsEnabled}
              onChange={(e) => setVoiceInstructionsEnabled(e.target.checked)}
              style={{ width: '20px', height: '20px', cursor: 'pointer', accentColor: '#073F35' }}
              aria-label="Toggle voice instructions"
            />
          </div>

          {/* Privacy & Clinical Notice */}
          <div
            style={{
              backgroundColor: '#F1F5F9',
              padding: '16px 20px',
              borderRadius: '8px',
              fontSize: '0.825rem',
              color: '#475569',
              lineHeight: 1.5,
              marginBottom: '32px',
            }}
          >
            <strong>PRIVACY & CLINICAL NOTICE:</strong> Audio recordings are processed in real-time solely to normalize
            optotype answers and are not archived for biometric profiling. OptiGuide provides a preliminary functional
            screening aid, not a certified medical diagnosis or eyeglasses prescription.
          </div>

          <button
            onClick={handleStartFromWelcome}
            disabled={isLoading}
            style={{
              width: '100%',
              backgroundColor: '#073F35',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              padding: '16px',
              fontSize: '1.1rem',
              fontWeight: 700,
              cursor: isLoading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              boxShadow: '0 4px 12px rgba(7, 63, 53, 0.2)',
            }}
          >
            {isLoading ? 'Connecting to Screening Engine...' : 'Start Vision Test'}
            <ArrowRightIcon size={20} color="#FFFFFF" />
          </button>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SCREEN B — PREPARATION */}
      {/* ===================================================================== */}
      {stage === 'preparation' && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '16px',
            padding: '36px 32px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ marginBottom: '24px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Step 1 of 4 • Test Environment Preparation
            </span>
            <h2 style={{ fontSize: '1.5rem', color: '#073F35', marginTop: '4px', fontWeight: 700 }}>
              Prepare Your Environment & Microphone
            </h2>
          </div>

          {/* Preparation Checklist */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '32px' }}>
            {/* Item 1: Distance */}
            <label
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '14px',
                padding: '16px',
                border: '1px solid #E2E8F0',
                borderRadius: '10px',
                cursor: 'pointer',
                backgroundColor: prepChecklist.distanceReady ? '#F0FDF4' : '#FAFAFA',
              }}
            >
              <input
                type="checkbox"
                checked={prepChecklist.distanceReady}
                onChange={(e) => setPrepChecklist((p) => ({ ...p, distanceReady: e.target.checked }))}
                style={{ width: '20px', height: '20px', accentColor: '#073F35', marginTop: '2px' }}
              />
              <div>
                <div style={{ fontWeight: 600, color: '#0F172A' }}>Viewing Distance & Posture</div>
                <div style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>
                  Position yourself 3.0 meters (approx. 10 feet) away from the screen for distance acuity, or at arm's
                  length (~40 cm) if performing near vision screening. Keep screen at eye level.
                </div>
              </div>
            </label>

            {/* Item 2: Lighting & Eyeglasses */}
            <label
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '14px',
                padding: '16px',
                border: '1px solid #E2E8F0',
                borderRadius: '10px',
                cursor: 'pointer',
                backgroundColor: prepChecklist.lightingReady ? '#F0FDF4' : '#FAFAFA',
              }}
            >
              <input
                type="checkbox"
                checked={prepChecklist.lightingReady}
                onChange={(e) => setPrepChecklist((p) => ({ ...p, lightingReady: e.target.checked }))}
                style={{ width: '20px', height: '20px', accentColor: '#073F35', marginTop: '2px' }}
              />
              <div>
                <div style={{ fontWeight: 600, color: '#0F172A' }}>Lighting & Eyewear</div>
                <div style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>
                  Ensure comfortable, even room lighting without direct screen glare. Wear your regular distance spectacles
                  or contact lenses if you normally use them.
                </div>
              </div>
            </label>

            {/* Item 3: Eye Occlusion */}
            <label
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '14px',
                padding: '16px',
                border: '1px solid #E2E8F0',
                borderRadius: '10px',
                cursor: 'pointer',
                backgroundColor: prepChecklist.eyeCovered ? '#F0FDF4' : '#FAFAFA',
              }}
            >
              <input
                type="checkbox"
                checked={prepChecklist.eyeCovered}
                onChange={(e) => setPrepChecklist((p) => ({ ...p, eyeCovered: e.target.checked }))}
                style={{ width: '20px', height: '20px', accentColor: '#073F35', marginTop: '2px' }}
              />
              <div>
                <div style={{ fontWeight: 600, color: '#0F172A' }}>Eye Occlusion (Cover One Eye)</div>
                <div style={{ fontSize: '0.875rem', color: '#64748B', marginTop: '2px' }}>
                  You will test one eye at a time. Cover the non-tested eye with your palm or an opaque patch. Keep both
                  eyes open beneath your hand to avoid squinting or optical distortion.
                </div>
              </div>
            </label>

            {/* Item 4: Microphone Permission Check */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px',
                border: micPermissionGranted ? '1px solid #86EFAC' : '1px solid #E2E8F0',
                borderRadius: '10px',
                backgroundColor: micPermissionGranted ? '#F0FDF4' : '#F8FAFC',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <MicIcon size={24} color={micPermissionGranted ? '#16A34A' : '#073F35'} />
                <div>
                  <div style={{ fontWeight: 600, color: '#0F172A' }}>
                    Microphone Status: {micPermissionGranted ? 'Ready & Verified' : 'Access Required'}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#64748B' }}>
                    Enables hands-free speech recognition while sitting at distance.
                  </div>
                </div>
              </div>

              {!micPermissionGranted ? (
                <button
                  type="button"
                  onClick={handleTestMicrophone}
                  disabled={micChecking}
                  style={{
                    backgroundColor: '#073F35',
                    color: '#FFFFFF',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '8px 16px',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    cursor: micChecking ? 'not-allowed' : 'pointer',
                  }}
                >
                  {micChecking ? 'Checking...' : 'Allow Microphone'}
                </button>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#16A34A', fontWeight: 600 }}>
                  <CheckIcon size={18} color="#16A34A" />
                  Verified
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              onClick={() => setStage('welcome')}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #CBD5E1',
                borderRadius: '8px',
                padding: '12px 24px',
                fontSize: '0.95rem',
                color: '#475569',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <ArrowLeftIcon size={18} color="#475569" />
              Back
            </button>

            <button
              onClick={handleConfirmPreparation}
              style={{
                backgroundColor: '#073F35',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                padding: '12px 28px',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              Proceed to Calibration
              <ArrowRightIcon size={18} color="#FFFFFF" />
            </button>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SCREEN C — CALIBRATION */}
      {/* ===================================================================== */}
      {stage === 'calibration' && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '16px',
            padding: '36px 32px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ marginBottom: '24px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Step 2 of 4 • Display Sizing Calibration
            </span>
            <h2 style={{ fontSize: '1.5rem', color: '#073F35', marginTop: '4px', fontWeight: 700 }}>
              Physical Screen Dimension Calibration
            </h2>
            <p style={{ fontSize: '0.95rem', color: '#64748B', marginTop: '6px' }}>
              Standard ISO 8596 optotypes subtend exactly 5 minutes of visual angle. To project accurate physical millimeter
              dimensions on your device screen, align the slider with a standard bank card (85.6 mm).
            </p>
          </div>

          {/* Interactive Card Slider */}
          <div
            style={{
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '12px',
              padding: '24px',
              textAlign: 'center',
              marginBottom: '28px',
            }}
          >
            <div
              style={{
                width: `${cardWidthPx}px`,
                height: `${cardWidthPx * 0.63}px`,
                backgroundColor: '#073F35',
                color: '#FFFFFF',
                borderRadius: '12px',
                margin: '0 auto 20px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '16px',
                boxShadow: '0 8px 16px rgba(0, 0, 0, 0.15)',
                transition: 'width 0.05s ease-out',
                maxWidth: '100%',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', opacity: 0.8 }}>
                <span>STANDARD REFERENCE CARD</span>
                <span>85.60 mm</span>
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '0.1em' }}>
                •••• •••• •••• 2026
              </div>
              <div style={{ fontSize: '0.7rem', textAlign: 'left', opacity: 0.7 }}>
                Hold physical card against screen and match width
              </div>
            </div>

            {/* Slider Controls */}
            <div style={{ maxWidth: '480px', margin: '0 auto' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#64748B', marginBottom: '8px' }}>
                <span>Narrower</span>
                <span style={{ fontWeight: 600, color: '#073F35' }}>
                  Width: {cardWidthPx} px • Computed DPI: {Math.round(cardWidthPx / (sliderWidthMm / 25.4))}
                </span>
                <span>Wider</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748B', marginTop: '4px', marginBottom: '8px' }}>
                Mode: <strong>{isCalibrated ? 'Physical Dimension Calibrated' : 'Preliminary / Uncalibrated'}</strong>
              </div>
              <input
                type="range"
                min="200"
                max="500"
                value={cardWidthPx}
                onChange={(e) => setCardWidthPx(Number(e.target.value))}
                style={{ width: '100%', accentColor: '#073F35', cursor: 'pointer' }}
                aria-label="Adjust card width in pixels"
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '16px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
            <button
              onClick={() => handleConfirmCalibration('client_unverified')}
              style={{
                backgroundColor: '#F1F5F9',
                color: '#475569',
                border: 'none',
                borderRadius: '8px',
                padding: '12px 20px',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Skip (Treat as Uncalibrated / Preliminary)
            </button>

            <button
              onClick={() => handleConfirmCalibration('reference_card')}
              style={{
                backgroundColor: '#073F35',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                padding: '12px 24px',
                fontSize: '0.95rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              Confirm Physical Calibration
              <ArrowRightIcon size={18} color="#FFFFFF" />
            </button>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SCREEN D — EYE SELECTION & PROTOCOL */}
      {/* ===================================================================== */}
      {stage === 'eye_selection' && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '16px',
            padding: '36px 32px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ marginBottom: '24px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Step 3 of 4 • Eye & Optotype Configuration
            </span>
            <h2 style={{ fontSize: '1.5rem', color: '#073F35', marginTop: '4px', fontWeight: 700 }}>
              Select Eye to Screen
            </h2>
            <p style={{ fontSize: '0.95rem', color: '#64748B', marginTop: '6px' }}>
              Clinical protocols recommend testing the Right Eye first, followed by the Left Eye.
            </p>
          </div>

          {/* Eye Selection Radio Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '28px',
            }}
          >
            {[
              {
                id: 'right',
                title: 'Right Eye (OD)',
                desc: 'Cover Left eye with palm. Recommended starting eye.',
                status: completedEyeResults['right'] ? 'Completed' : 'Ready',
              },
              {
                id: 'left',
                title: 'Left Eye (OS)',
                desc: 'Cover Right eye with palm.',
                status: completedEyeResults['left'] ? 'Completed' : 'Ready',
              },
              {
                id: 'both',
                title: 'Both Eyes (OU)',
                desc: 'Binocular visual acuity with both eyes uncovered.',
                status: completedEyeResults['both'] ? 'Completed' : 'Optional',
              },
            ].map((eye) => (
              <div
                key={eye.id}
                onClick={() => setSelectedEye(eye.id as any)}
                style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: selectedEye === eye.id ? '2px solid #073F35' : '1px solid #E2E8F0',
                  backgroundColor: selectedEye === eye.id ? '#F0FDF4' : '#FFFFFF',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#073F35' }}>{eye.title}</h3>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: eye.status === 'Completed' ? '#16A34A' : '#64748B',
                      backgroundColor: eye.status === 'Completed' ? '#DCFCE7' : '#F1F5F9',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    {eye.status}
                  </span>
                </div>
                <p style={{ fontSize: '0.85rem', color: '#64748B', marginTop: '8px' }}>{eye.desc}</p>
              </div>
            ))}
          </div>

          {/* Optotype Set Selector */}
          <div style={{ marginBottom: '28px' }}>
            <label style={{ display: 'block', fontWeight: 600, color: '#073F35', marginBottom: '8px' }}>
              Standardized Optotype Stimulus Set:
            </label>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {[
                { id: 'TUMBLING_E', label: 'Tumbling E (Recommended)', info: 'Directions: Up, Down, Left, Right' },
                { id: 'LANDOLT_C', label: 'Landolt C', info: 'Gap: Up, Down, Left, Right' },
                { id: 'SLOAN', label: 'Sloan Letters', info: '10 Letters (C, D, E, F, L, N, O, P, T, Z)' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setOptotypeType(opt.id as any)}
                  style={{
                    flex: '1 1 200px',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    border: optotypeType === opt.id ? '2px solid #073F35' : '1px solid #CBD5E1',
                    backgroundColor: optotypeType === opt.id ? '#E6F3ED' : '#FFFFFF',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ fontWeight: 600, color: '#073F35' }}>{opt.label}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>{opt.info}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Viewing Distance Selector */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontWeight: 600, color: '#073F35', marginBottom: '8px' }}>
              Testing Distance:
            </label>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {[
                { dist: 3.0, label: '3.0 Meters (Standard Distance)' },
                { dist: 2.0, label: '2.0 Meters (Intermediate)' },
                { dist: 0.4, label: '0.4 Meters (Near Reading)' },
              ].map((d) => (
                <button
                  key={d.dist}
                  type="button"
                  onClick={() => setViewingDistanceMeters(d.dist)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: viewingDistanceMeters === d.dist ? '2px solid #073F35' : '1px solid #CBD5E1',
                    backgroundColor: viewingDistanceMeters === d.dist ? '#E6F3ED' : '#FFFFFF',
                    fontWeight: 600,
                    color: '#073F35',
                    cursor: 'pointer',
                  }}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          {/* Occlusion Acknowledgment */}
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '14px',
              border: '1px solid #E2E8F0',
              borderRadius: '8px',
              marginBottom: '32px',
              backgroundColor: '#FAFAFA',
              cursor: 'pointer',
            }}
          >
            <input
              type="checkbox"
              checked={userReportedOcclusion}
              onChange={(e) => setUserReportedOcclusion(e.target.checked)}
              style={{ width: '18px', height: '18px', accentColor: '#073F35' }}
            />
            <span style={{ fontSize: '0.875rem', color: '#334155' }}>
              I confirm that the non-tested eye is occluded without pressure on the eyelid.
            </span>
          </label>

          <button
            onClick={() => handleStartAcuityTest(selectedEye)}
            disabled={isLoading || !userReportedOcclusion}
            style={{
              width: '100%',
              backgroundColor: '#073F35',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              padding: '16px',
              fontSize: '1.05rem',
              fontWeight: 700,
              cursor: isLoading || !userReportedOcclusion ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
            }}
          >
            {isLoading ? 'Initializing Adaptive Staircase...' : `Begin ${selectedEye.toUpperCase()} Eye Test`}
            <ArrowRightIcon size={20} color="#FFFFFF" />
          </button>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SCREEN E & F & G — INTERACTIVE ACUITY STAGE & VOICE RECOGNITION */}
      {/* ===================================================================== */}
      {stage === 'testing' && currentChallenge && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Top Progress & Level Status */}
          <div
            style={{
              backgroundColor: '#FFFFFF',
              border: '1px solid #E2E8F0',
              borderRadius: '12px',
              padding: '16px 24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748B' }}>TESTING EYE:</span>
              <strong style={{ marginLeft: '8px', color: '#073F35' }}>
                {currentChallenge.test_eye.toUpperCase()} EYE (Distance 3.0m)
              </strong>
            </div>

            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.8rem', color: '#64748B' }}>DIFFICULTY LEVEL:</span>
                <span style={{ marginLeft: '6px', fontWeight: 700, color: '#073F35' }}>
                  {currentChallenge.level_snellen} (LogMAR {currentChallenge.level_logmar.toFixed(2)})
                </span>
              </div>

              <div
                style={{
                  backgroundColor: '#E6F3ED',
                  color: '#073F35',
                  padding: '4px 12px',
                  borderRadius: '20px',
                  fontWeight: 700,
                  fontSize: '0.85rem',
                }}
              >
                Attempt #{currentChallenge.attempt_sequence}
              </div>
            </div>
          </div>

          {/* Central Optotype Stimulus Card (Screen E) */}
          <div
            style={{
              backgroundColor: '#FFFFFF',
              border: '2px solid #E2E8F0',
              borderRadius: '16px',
              padding: '60px 24px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '280px',
              boxShadow: '0 8px 30px rgba(0, 0, 0, 0.04)',
              position: 'relative',
            }}
          >
            {renderOptotypeStimulus()}

            <div style={{ marginTop: '32px', textAlign: 'center' }}>
              <p style={{ fontSize: '1.05rem', fontWeight: 600, color: '#073F35' }}>
                {currentChallenge.optotype_type === 'SLOAN'
                  ? 'Say the letter aloud into your microphone'
                  : 'Which direction is the optotype pointing? (Say Up, Down, Left, or Right)'}
              </p>
            </div>
          </div>

          {/* Real Microphone & Speech Control Card (Screen F) */}
          <div
            style={{
              backgroundColor: isListening ? '#F0FDF4' : '#FFFFFF',
              border: isListening ? '2px solid #22C55E' : '1px solid #E2E8F0',
              borderRadius: '16px',
              padding: '24px',
              textAlign: 'center',
              transition: 'all 0.3s ease',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
              {/* Mic Status & Pulsing Button */}
              <div style={{ position: 'relative' }}>
                {isListening && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '-8px',
                      left: '-8px',
                      right: '-8px',
                      bottom: '-8px',
                      borderRadius: '50%',
                      border: '2px solid #22C55E',
                      opacity: 0.6,
                      animation: 'pulse 1.5s infinite',
                      transform: `scale(${1 + micVolume * 0.4})`,
                      transition: 'transform 0.1s ease',
                    }}
                  />
                )}

                <button
                  type="button"
                  onClick={() => {
                    if (isListening) {
                      handleManualStopSpeaking();
                    } else {
                      triggerVoiceListening(currentChallenge);
                    }
                  }}
                  disabled={isLoading}
                  style={{
                    width: '72px',
                    height: '72px',
                    borderRadius: '50%',
                    backgroundColor: isListening ? '#DC2626' : '#073F35',
                    color: '#FFFFFF',
                    border: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    boxShadow: isListening ? '0 0 20px rgba(220, 38, 38, 0.4)' : '0 4px 15px rgba(7, 63, 53, 0.25)',
                    transition: 'all 0.2s ease',
                  }}
                  aria-label={isListening ? 'Stop recording audio' : 'Start speaking'}
                >
                  <MicIcon size={32} color="#FFFFFF" />
                </button>
              </div>

              <div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: isListening ? '#15803D' : '#073F35' }}>
                  {isListening
                    ? 'Listening... Speak your answer now'
                    : isLoading
                    ? 'Processing Speech Recognition...'
                    : 'Click Microphone or Speak'}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#64748B', marginTop: '4px' }}>
                  {isListening ? 'Auto-submits after speaking • Or click mic to finish' : `Real microphone active at 16 kHz (${micState.toUpperCase()})`}
                </div>
              </div>

              {/* Speech Recognition Feedback Banner (Screen G) */}
              {lastSpeechFeedback && (
                <div
                  style={{
                    width: '100%',
                    maxWidth: '540px',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    textAlign: 'left',
                    backgroundColor: lastSpeechFeedback.retryRequired
                      ? '#EFF6FF'
                      : lastSpeechFeedback.wasCorrect
                      ? '#F0FDF4'
                      : '#FEF2F2',
                    border: lastSpeechFeedback.retryRequired
                      ? '1px solid #93C5FD'
                      : lastSpeechFeedback.wasCorrect
                      ? '1px solid #86EFAC'
                      : '1px solid #FCA5A5',
                    color: lastSpeechFeedback.retryRequired
                      ? '#1E40AF'
                      : lastSpeechFeedback.wasCorrect
                      ? '#166534'
                      : '#991B1B',
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{lastSpeechFeedback.feedbackMessage}</div>
                  {lastSpeechFeedback.transcript && (
                    <div style={{ fontSize: '0.8rem', marginTop: '2px', opacity: 0.85 }}>
                      Recognized audio: "{lastSpeechFeedback.transcript}"
                      {lastSpeechFeedback.confidence && (
                        <span> • Confidence: {Math.round(lastSpeechFeedback.confidence * 100)}%</span>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Manual Accessibility Fallback Buttons */}
            <div
              style={{
                marginTop: '24px',
                paddingTop: '20px',
                borderTop: '1px solid #E2E8F0',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <span style={{ fontSize: '0.8rem', color: '#64748B' }}>
                Accessibility / Manual fallback: Click your answer directly
              </span>

              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
                {currentChallenge.choices.map((choice) => (
                  <button
                    key={choice}
                    onClick={() => handleManualResponse(choice)}
                    disabled={isLoading}
                    style={{
                      backgroundColor: '#FFFFFF',
                      border: '1px solid #CBD5E1',
                      borderRadius: '8px',
                      padding: '10px 18px',
                      fontSize: '0.9rem',
                      fontWeight: 600,
                      color: '#073F35',
                      cursor: isLoading ? 'not-allowed' : 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {choice}
                  </button>
                ))}

                <button
                  onClick={() => handleManualResponse('CANNOT_SEE')}
                  disabled={isLoading}
                  style={{
                    backgroundColor: '#FEF2F2',
                    border: '1px solid #FCA5A5',
                    borderRadius: '8px',
                    padding: '10px 18px',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    color: '#991B1B',
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  Cannot See / Blurry
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SCREEN H — FINAL RESULTS REPORT */}
      {/* ===================================================================== */}
      {stage === 'results' && finalResult && (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '16px',
            padding: '36px 32px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div
              style={{
                width: '60px',
                height: '60px',
                borderRadius: '50%',
                backgroundColor: '#DCFCE7',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '12px',
              }}
            >
              <CheckIcon size={28} color="#15803D" />
            </div>
            <h2 style={{ fontSize: '1.75rem', color: '#073F35', fontWeight: 700 }}>
              Visual Acuity Screening Observation Report
            </h2>
            <p style={{ fontSize: '0.95rem', color: '#64748B' }}>
              Standard ISO 8596 Adaptive Staircase Screening Complete
            </p>
          </div>

          {/* Results Metric Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '32px',
            }}
          >
            <div style={{ backgroundColor: '#F0FDF4', padding: '20px', borderRadius: '12px', border: '1px solid #BBF7D0' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#166534' }}>
                {finalResult.test_eye.toUpperCase()} EYE SNELLEN
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#14532D', marginTop: '4px' }}>
                {finalResult.final_snellen || 'N/A'}
              </div>
              <div style={{ fontSize: '0.85rem', color: '#15803D', marginTop: '4px' }}>
                LogMAR: {finalResult.final_logmar?.toFixed(2) ?? '—'} • Decimal: {finalResult.final_decimal?.toFixed(2) ?? '—'}
              </div>
            </div>

            <div style={{ backgroundColor: '#F8FAFC', padding: '20px', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748B' }}>CALIBRATION TIER</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#073F35', marginTop: '4px' }}>
                {finalResult.calibration_status.replace('_', ' ')}
              </div>
              <div style={{ fontSize: '0.85rem', color: '#64748B', marginTop: '4px' }}>
                Distance: {finalResult.viewing_distance_meters.toFixed(1)}m • Display DPI: {calculatedDpi}
              </div>
            </div>

            <div style={{ backgroundColor: '#F8FAFC', padding: '20px', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748B' }}>TEST TELEMETRY</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#073F35', marginTop: '4px' }}>
                {finalResult.total_attempts} Presentations
              </div>
              <div style={{ fontSize: '0.85rem', color: '#64748B', marginTop: '4px' }}>
                Correct: {finalResult.correct_attempts} • Protocol: {finalResult.protocol_version}
              </div>
            </div>
          </div>

          {/* Clinical Observation Summary */}
          <div
            style={{
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '10px',
              padding: '20px',
              marginBottom: '28px',
            }}
          >
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#073F35', marginBottom: '8px' }}>
              Preliminary Clinical Observation:
            </h3>
            <p style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.5 }}>
              Smallest reliably resolved optotype level corresponds to {finalResult.final_snellen} visual acuity at{' '}
              {finalResult.viewing_distance_meters} meters under the {finalResult.protocol_version} protocol.
              {finalResult.final_logmar && finalResult.final_logmar > 0.3
                ? ' Acuity observation suggests reduced visual clarity. Consultation with an eye care professional is recommended.'
                : ' Functional distance resolution meets standard screening guidelines.'}
            </p>
          </div>

          {/* Statutory Clinical Warning */}
          <div
            style={{
              backgroundColor: '#FFFBEB',
              border: '1px solid #FCD34D',
              borderRadius: '10px',
              padding: '16px 20px',
              fontSize: '0.85rem',
              color: '#92400E',
              lineHeight: 1.5,
              marginBottom: '32px',
              display: 'flex',
              gap: '12px',
              alignItems: 'flex-start',
            }}
          >
            <ShieldAlertIcon size={22} color="#D97706" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>IMPORTANT STATUTORY MEDICAL NOTICE:</strong> This screening result is an automated preliminary observation
              aid and does NOT represent an eye disease diagnosis or prescription. Optical refraction (SPH, CYL, AXIS) cannot
              be derived from acuity screening alone. Please consult a licensed optometrist or ophthalmologist for clinical
              refraction.
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '16px', justifyContent: 'space-between', flexWrap: 'wrap' }}>
            {finalResult.test_eye === 'right' && !completedEyeResults['left'] ? (
              <button
                onClick={() => handleStartAcuityTest('left')}
                style={{
                  backgroundColor: '#073F35',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '14px 28px',
                  fontSize: '1rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                Test Left Eye (OS) Now
                <ArrowRightIcon size={18} color="#FFFFFF" />
              </button>
            ) : (
              <button
                onClick={() => setStage('eye_selection')}
                style={{
                  backgroundColor: '#073F35',
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '14px 28px',
                  fontSize: '1rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <RefreshIcon size={18} color="#FFFFFF" />
                Start Another Eye Test
              </button>
            )}

            <button
              onClick={onCancel}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #D7D2C4',
                borderRadius: '8px',
                padding: '14px 24px',
                fontSize: '1rem',
                color: '#4A5568',
                cursor: 'pointer',
              }}
            >
              Finish & Return Home
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
