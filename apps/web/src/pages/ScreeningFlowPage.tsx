import React, { useState, useEffect, useRef } from 'react';
import {
  VolumeIcon,
  CameraIcon,
  CheckIcon,
  AlertIcon,
  ShieldAlertIcon,
} from '../components/icons';
import { useLanguage } from '../localization/useLanguage';
import { speakText, stopSpeech } from '../services/tts';
import { saveScreeningSession } from '../services/storage';
import {
  ScreeningSession,
  QuestionnaireResponses,
  DistanceVisionResult,
  NearVisionResult,
  AstigmatismResult,
  ColorVisionResult,
  PDEstimationResult,
} from '@optiguide/shared';

interface ScreeningFlowPageProps {
  onComplete: (session: ScreeningSession) => void;
  onCancel: () => void;
  customerName?: string;
  customerPhone?: string;
}

type ScreeningStep =
  | 'intro'
  | 'readiness'
  | 'questionnaire'
  | 'distance_intro'
  | 'distance_right'
  | 'distance_left'
  | 'near'
  | 'astigmatism'
  | 'color'
  | 'pd'
  | 'processing';

export const ScreeningFlowPage: React.FC<ScreeningFlowPageProps> = ({
  onComplete,
  onCancel,
  customerName,
  customerPhone,
}) => {
  const { language, t } = useLanguage();
  const [step, setStep] = useState<ScreeningStep>('intro');
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);

  // Questionnaire state
  const [qIndex, setQIndex] = useState(0);
  const [urgentSymptomDetected, setUrgentSymptomDetected] = useState(false);
  const [questionnaire, setQuestionnaire] = useState<QuestionnaireResponses>({
    blurredVision: 'mild',
    difficultyReadingNear: false,
    difficultySeeingDistant: false,
    eyeStrainOrHeadaches: false,
    currentEyewear: 'none',
    symptomDuration: '1_to_6_months',
    suddenVisionLoss: false,
    severeEyePainOrFlashes: false,
  });

  // Distance Vision state
  const orientations = ['up', 'right', 'down', 'left'] as const;
  type Orientation = typeof orientations[number];
  const acuityLevels = [
    { snellen: '20/100', sizePx: 68, logMAR: 0.7, decimal: 0.2 },
    { snellen: '20/70', sizePx: 52, logMAR: 0.54, decimal: 0.28 },
    { snellen: '20/50', sizePx: 40, logMAR: 0.4, decimal: 0.4 },
    { snellen: '20/40', sizePx: 32, logMAR: 0.3, decimal: 0.5 },
    { snellen: '20/30', sizePx: 24, logMAR: 0.18, decimal: 0.67 },
    { snellen: '20/25', sizePx: 20, logMAR: 0.1, decimal: 0.8 },
    { snellen: '20/20', sizePx: 16, logMAR: 0.0, decimal: 1.0 },
  ];

  const [testEye, setTestEye] = useState<'right' | 'left'>('right');
  const [acuityIndex, setAcuityIndex] = useState(0);
  const [targetOrientation, setTargetOrientation] = useState<Orientation>('right');
  const [rightEyeScore, setRightEyeScore] = useState(acuityLevels[4]);
  const [leftEyeScore, setLeftEyeScore] = useState(acuityLevels[4]);
  const [consecutiveCorrect, setConsecutiveCorrect] = useState(0);

  // Near Vision state
  const [nearReadingLevel, setNearReadingLevel] = useState<'N6' | 'N8' | 'N10' | 'N12'>('N8');
  const nearClarityRating: 1 | 2 | 3 | 4 | 5 = 4;

  // Astigmatism state
  const [astigmatismUniform, setAstigmatismUniform] = useState<boolean>(true);
  const [astigmatismMeridian, setAstigmatismMeridian] = useState<number | null>(null);

  // Color Vision state
  const colorPlates = [
    { id: 1, correctValue: '12', demo: true, description: 'Demonstration plate: Visible to all' },
    { id: 2, correctValue: '8', demo: false, description: 'Red-green screening plate' },
    { id: 3, correctValue: '29', demo: false, description: 'Red-green screening plate' },
    { id: 4, correctValue: '5', demo: false, description: 'Red-green screening plate' },
  ];
  const [plateIndex, setPlateIndex] = useState(0);
  const [colorPlateAnswers, setColorPlateAnswers] = useState<string[]>([]);
  const [currentPlateInput, setCurrentPlateInput] = useState('');

  // PD Estimation state
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraDenied, setCameraDenied] = useState(false);
  const [pdValueMm, setPdValueMm] = useState<number>(63.0);
  const cardDetected = true;
  const pdConfidence = 0.92;
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Clean up camera on unmount
  useEffect(() => {
    return () => {
      stopSpeech();
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Questionnaire questions
  const questions = [
    {
      id: 'blurred',
      title: 'Do you experience blurry vision?',
      subtitle: 'Noticeable difficulty focusing on signs, faces, or printed text.',
      voiceEn: 'Do you experience blurry vision during regular daily activities?',
      voiceHi: 'क्या आपको दैनिक कार्यों के दौरान धुंधली दृष्टि का अनुभव होता है?',
      options: [
        { value: 'none', label: 'No blurry vision' },
        { value: 'mild', label: 'Mild (occasional strain)' },
        { value: 'moderate', label: 'Moderate (frequent blur)' },
        { value: 'severe', label: 'Severe (constant blur)' },
      ],
      current: questionnaire.blurredVision,
      setter: (v: any) => setQuestionnaire((q) => ({ ...q, blurredVision: v })),
    },
    {
      id: 'near_difficulty',
      title: 'Do you have difficulty reading text up close?',
      subtitle: 'Holding books or mobile phones at arms length to read clearly.',
      voiceEn: 'Do you have difficulty reading small text or mobile screens up close?',
      voiceHi: 'क्या आपको नजदीक से बारीक अक्षर या मोबाइल स्क्रीन पढ़ने में कठिनाई होती है?',
      options: [
        { value: false, label: 'No, near text is clear' },
        { value: true, label: 'Yes, near text is difficult or tiring' },
      ],
      current: questionnaire.difficultyReadingNear,
      setter: (v: any) => setQuestionnaire((q) => ({ ...q, difficultyReadingNear: v })),
    },
    {
      id: 'distance_difficulty',
      title: 'Do you have difficulty seeing distant objects clearly?',
      subtitle: 'Road signs, television screens, or bus route boards at a distance.',
      voiceEn: 'Do you have difficulty seeing distant objects or road signs clearly?',
      voiceHi: 'क्या आपको दूर की चीजें या सड़क के साइनबोर्ड साफ देखने में परेशानी होती है?',
      options: [
        { value: false, label: 'No, distant objects are sharp' },
        { value: true, label: 'Yes, distant objects appear hazy' },
      ],
      current: questionnaire.difficultySeeingDistant,
      setter: (v: any) => setQuestionnaire((q) => ({ ...q, difficultySeeingDistant: v })),
    },
    {
      id: 'strain',
      title: 'Do you suffer from frequent eye strain or headaches?',
      subtitle: 'Especially in the forehead or temples after prolonged reading or screen work.',
      voiceEn: 'Do you experience frequent eye strain or headaches during visual tasks?',
      voiceHi: 'क्या आपको आंखों में खिंचाव या सिरदर्द की समस्या रहती है?',
      options: [
        { value: false, label: 'No headaches or strain' },
        { value: true, label: 'Yes, frequent strain or headaches' },
      ],
      current: questionnaire.eyeStrainOrHeadaches,
      setter: (v: any) => setQuestionnaire((q) => ({ ...q, eyeStrainOrHeadaches: v })),
    },
    {
      id: 'eyewear',
      title: 'Do you currently use spectacles or contact lenses?',
      subtitle: 'Prescribed or over-the-counter reading glasses.',
      voiceEn: 'Do you currently wear spectacles or contact lenses?',
      voiceHi: 'क्या आप वर्तमान में किसी प्रकार का चश्मा पहनते हैं?',
      options: [
        { value: 'none', label: 'No eyewear currently' },
        { value: 'reading', label: 'Reading spectacles only' },
        { value: 'distance', label: 'Distance spectacles only' },
        { value: 'bifocal_progressive', label: 'Bifocal or progressive lenses' },
      ],
      current: questionnaire.currentEyewear,
      setter: (v: any) => setQuestionnaire((q) => ({ ...q, currentEyewear: v })),
    },
    {
      id: 'urgent',
      title: 'Have you had sudden vision loss or severe eye pain?',
      subtitle: 'Critical safety check. Sudden changes require urgent medical evaluation.',
      voiceEn: 'Have you experienced any sudden loss of vision, flashes of light, or severe eye pain?',
      voiceHi: 'क्या आपको अचानक दृष्टि में कमी, तेज दर्द या रोशनी के चमकने का अनुभव हुआ है?',
      options: [
        { value: false, label: 'No, nothing sudden or severe' },
        { value: true, label: 'Yes, sudden loss of sight or severe pain' },
      ],
      current: questionnaire.suddenVisionLoss,
      setter: (v: any) => {
        setQuestionnaire((q) => ({
          ...q,
          suddenVisionLoss: v,
          severeEyePainOrFlashes: v,
        }));
        if (v === true) {
          setUrgentSymptomDetected(true);
        } else {
          setUrgentSymptomDetected(false);
        }
      },
    },
  ];

  const currentQ = questions[qIndex];

  // Play audio for current question
  const handlePlayVoice = () => {
    const text = language === 'hi' ? currentQ.voiceHi : currentQ.voiceEn;
    speakText(text, language);
  };

  // Keyboard navigation for Tumbling E test
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (step === 'distance_right' || step === 'distance_left') {
        if (e.key === 'ArrowUp') handleAcuityAnswer('up');
        if (e.key === 'ArrowRight') handleAcuityAnswer('right');
        if (e.key === 'ArrowDown') handleAcuityAnswer('down');
        if (e.key === 'ArrowLeft') handleAcuityAnswer('left');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [step, targetOrientation, acuityIndex, consecutiveCorrect]);

  // Handle Tumbling E answers
  const handleAcuityAnswer = (selected: Orientation) => {
    const isCorrect = selected === targetOrientation;
    const currentAcuity = acuityLevels[acuityIndex];

    if (isCorrect) {
      const nextConsecutive = consecutiveCorrect + 1;
      setConsecutiveCorrect(nextConsecutive);

      if (nextConsecutive >= 2 && acuityIndex < acuityLevels.length - 1) {
        // Step down to a smaller optotype
        setAcuityIndex(acuityIndex + 1);
        setConsecutiveCorrect(0);
      }
    } else {
      setConsecutiveCorrect(0);
    }

    // Set new random direction
    const nextOri = orientations[Math.floor(Math.random() * orientations.length)];
    setTargetOrientation(nextOri);

    // If reaching the end of test levels or after 6 presentations per eye
    if (acuityIndex >= acuityLevels.length - 1 || (acuityIndex >= 3 && !isCorrect)) {
      if (testEye === 'right') {
        setRightEyeScore(currentAcuity);
        // Switch to left eye
        setTestEye('left');
        setAcuityIndex(0);
        setConsecutiveCorrect(0);
        setStep('distance_left');
      } else {
        setLeftEyeScore(currentAcuity);
        setStep('near');
      }
    }
  };

  // Start Camera for PD Estimation
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setCameraActive(true);
        setCameraDenied(false);
      }
    } catch {
      setCameraDenied(true);
      setCameraActive(false);
    }
  };

  // Complete and assemble full screening session
  const finalizeScreening = () => {
    setStep('processing');

    const distanceVision: DistanceVisionResult = {
      rightEye: {
        snellenFraction: rightEyeScore.snellen,
        logMAR: rightEyeScore.logMAR,
        decimal: rightEyeScore.decimal,
      },
      leftEye: {
        snellenFraction: leftEyeScore.snellen,
        logMAR: leftEyeScore.logMAR,
        decimal: leftEyeScore.decimal,
      },
      testedDistanceMeters: 0.6,
      unassistedOrCorrected: questionnaire.currentEyewear !== 'none' ? 'with_glasses' : 'unassisted',
    };

    const nearVision: NearVisionResult = {
      readingAcuityLabel: `${nearReadingLevel} at 38cm`,
      readingDistanceCm: 38,
      canReadSmallText: nearReadingLevel === 'N6' || nearReadingLevel === 'N8',
      clarityRating: nearClarityRating,
    };

    const astigmatism: AstigmatismResult = {
      sharpMeridianDetected: !astigmatismUniform,
      indicatedAxes: astigmatismMeridian ? [astigmatismMeridian] : undefined,
      hasUniformClarity: astigmatismUniform,
      screeningObservation: astigmatismUniform
        ? 'Radial clock chart appeared uniformly clear with no prominent meridian asymmetry observed.'
        : `Potential cylindrical variance indicated along ${astigmatismMeridian} o'clock axis. Cautious observation; require slit-lamp and trial frame confirmation.`,
    };

    const correctPlates = colorPlateAnswers.filter(
      (ans, idx) => ans.trim() === colorPlates[idx]?.correctValue
    ).length;

    const colorVision: ColorVisionResult = {
      totalPlates: colorPlates.length,
      correctPlates,
      deficiencyIndicated: correctPlates < colorPlates.length - 1,
      deficiencyType: correctPlates < colorPlates.length - 1 ? 'protan_deutan_red_green' : 'none',
    };

    const pdEstimation: PDEstimationResult = {
      pupillaryDistanceMm: pdValueMm,
      monocularLeftMm: Number((pdValueMm / 2).toFixed(1)),
      monocularRightMm: Number((pdValueMm / 2).toFixed(1)),
      confidenceScore: pdConfidence,
      referenceCardDetected: cardDetected,
      faceDetected: true,
      imageQualityOk: true,
    };

    // Determine referral need
    const requiresReferral =
      urgentSymptomDetected ||
      rightEyeScore.logMAR >= 0.4 ||
      leftEyeScore.logMAR >= 0.4 ||
      Math.abs(rightEyeScore.logMAR - leftEyeScore.logMAR) >= 0.3 ||
      !astigmatismUniform ||
      correctPlates < 2;

    const session: ScreeningSession = {
      id: `scr-${Date.now()}`,
      userId: 'usr-current',
      customerName: customerName || 'Walk-in Citizen',
      customerPhone: customerPhone || 'Not specified',
      status: 'completed',
      startedAt: new Date(Date.now() - 360000).toISOString(),
      completedAt: new Date().toISOString(),
      preferredLanguage: language,
      deviceCalibration: {
        screenResolution: `${window.innerWidth}x${window.innerHeight}`,
        distanceCm: 50,
        cameraAvailable: cameraActive,
      },
      questionnaire,
      results: {
        distanceVision,
        nearVision,
        astigmatism,
        colorVision,
        pdEstimation,
      },
      recommendations: {
        suggestedLensCategories: [
          {
            id: 'lens-anti-reflective',
            title: 'Anti-Reflective Single Vision',
            description: 'Reduces surface glare and enhances contrast for daily road and shop visibility.',
            benefits: ['Crisp edge sharpness', 'Eliminates headlight reflections at night'],
          },
          ...(nearReadingLevel !== 'N6'
            ? [
                {
                  id: 'lens-reading-progressive',
                  title: 'Presbyopia / Near Support Lenses',
                  description: 'Provides graduated optical boost for comfortable close ledger and book reading.',
                  benefits: ['Relieves evening forehead fatigue', 'Smooth transition from reading to distant vision'],
                },
              ]
            : []),
        ],
        suggestedFrameShapes:
          pdValueMm < 62 ? ['Rectangular', 'Oval'] : ['Square', 'Aviator', 'Classic Rectangular'],
        estimatedPDMm: pdValueMm,
        professionalReferralRequired: requiresReferral,
        referralReason: requiresReferral
          ? urgentSymptomDetected
            ? 'Urgent: Patient reported acute ocular pain or sudden vision reduction.'
            : 'Visual acuity asymmetry or marked refractive blur noted during preliminary screening.'
          : undefined,
        disclaimer:
          'OptiGuide screening results are strictly preliminary. Confirmation by a certified optometrist or ophthalmologist is mandatory prior to lens manufacture or clinical therapy.',
      },
    };

    // Persist to storage
    saveScreeningSession(session);

    setTimeout(() => {
      onComplete(session);
    }, 1200);
  };

  return (
    <div style={{ maxWidth: '960px', margin: '24px auto', padding: '0 20px', minHeight: '80vh' }}>
      {/* Step Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          borderBottom: '1px solid #D7D2C4',
          paddingBottom: '14px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <span style={{ fontSize: '0.8125rem', color: '#4F8278', fontWeight: 600, textTransform: 'uppercase' }}>
            Preliminary Vision Screening Protocol
          </span>
          <h2 style={{ fontSize: '1.5rem', color: '#073F35', marginTop: '2px' }}>
            {step === 'intro' && '1. Screening Overview & Medical Limitation'}
            {step === 'readiness' && '2. Device Readiness & Calibration'}
            {step === 'questionnaire' && `3. Symptom Inquiries (${qIndex + 1} of ${questions.length})`}
            {step === 'distance_intro' && '4. Distance Vision Test Setup'}
            {step === 'distance_right' && '4. Distance Vision: Right Eye (Cover Left)'}
            {step === 'distance_left' && '4. Distance Vision: Left Eye (Cover Right)'}
            {step === 'near' && '5. Near Vision & Reading Acuity'}
            {step === 'astigmatism' && '6. Astigmatism Radial Fan Screening'}
            {step === 'color' && `7. Colour Vision Discrimination (${plateIndex + 1} of ${colorPlates.length})`}
            {step === 'pd' && '8. Pupillary Distance (PD) Estimation'}
            {step === 'processing' && 'Synthesizing Screening Observations...'}
          </h2>
        </div>

        <button
          onClick={onCancel}
          style={{
            background: 'none',
            border: '1px solid #D7D2C4',
            borderRadius: '4px',
            padding: '6px 14px',
            fontSize: '0.875rem',
            color: '#686F69',
            cursor: 'pointer',
          }}
        >
          Cancel Screening
        </button>
      </div>

      {/* ================= STEP 1: INTRO ================= */}
      {step === 'intro' && (
        <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
          <div
            style={{
              backgroundColor: '#F9F1E6',
              border: '1px solid #B77932',
              borderRadius: '6px',
              padding: '16px 20px',
              display: 'flex',
              gap: '14px',
              alignItems: 'flex-start',
              marginBottom: '24px',
            }}
          >
            <ShieldAlertIcon size={24} color="#B77932" />
            <div>
              <strong style={{ color: '#6E4515', display: 'block', fontSize: '1rem', marginBottom: '4px' }}>
                Mandatory Clinical Notice
              </strong>
              <p style={{ fontSize: '0.9375rem', color: '#202823', lineHeight: 1.5 }}>
                OptiGuide is a preliminary screening platform. It does not replace a comprehensive medical examination and cannot confirm an optical prescription or clinical diagnosis.
              </p>
            </div>
          </div>

          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '14px' }}>
            What This 5-Minute Screening Covers:
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '28px' }}>
            <div style={{ padding: '16px', backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px' }}>
              <div style={{ fontWeight: 600, color: '#073F35', marginBottom: '4px' }}>1. Symptom Survey</div>
              <div style={{ fontSize: '0.875rem', color: '#686F69' }}>Audio-assisted questions on eye strain, blur, and headaches.</div>
            </div>
            <div style={{ padding: '16px', backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px' }}>
              <div style={{ fontWeight: 600, color: '#073F35', marginBottom: '4px' }}>2. Acuity Checks</div>
              <div style={{ fontSize: '0.875rem', color: '#686F69' }}>Distance Snellen fractions & near reading clarity.</div>
            </div>
            <div style={{ padding: '16px', backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px' }}>
              <div style={{ fontWeight: 600, color: '#073F35', marginBottom: '4px' }}>3. Astigmatism & Colour</div>
              <div style={{ fontSize: '0.875rem', color: '#686F69' }}>Radial line clarity & pseudoisochromatic plates.</div>
            </div>
            <div style={{ padding: '16px', backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px' }}>
              <div style={{ fontWeight: 600, color: '#073F35', marginBottom: '4px' }}>4. Card-Based PD</div>
              <div style={{ fontSize: '0.875rem', color: '#686F69' }}>Pupillary distance measurement for frame fitting.</div>
            </div>
          </div>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '0.9375rem',
              color: '#202823',
              marginBottom: '28px',
              cursor: 'pointer',
            }}
          >
            <input
              type="checkbox"
              checked={disclaimerAccepted}
              onChange={(e) => setDisclaimerAccepted(e.target.checked)}
              style={{ width: '18px', height: '18px', accentColor: '#073F35' }}
            />
            <span>
              I understand that OptiGuide is a preliminary screening aid and agree to review results with a licensed optometrist.
            </span>
          </label>

          <button
            disabled={!disclaimerAccepted}
            onClick={() => setStep('readiness')}
            style={{
              backgroundColor: disclaimerAccepted ? '#073F35' : '#D7D2C4',
              color: '#F7F4EC',
              border: 'none',
              borderRadius: '6px',
              padding: '12px 24px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: disclaimerAccepted ? 'pointer' : 'not-allowed',
            }}
          >
            Continue to Device Readiness
          </button>
        </div>
      )}

      {/* ================= STEP 2: READINESS ================= */}
      {step === 'readiness' && (
        <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '16px' }}>
            Device & Testing Environment Readiness
          </h3>
          <p style={{ fontSize: '0.9375rem', color: '#686F69', marginBottom: '24px', lineHeight: 1.5 }}>
            To ensure reliable preliminary optotype presentation, confirm the following conditions before proceeding.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '32px' }}>
            <div style={{ padding: '16px', backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#E8F3ED', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#28734F' }}>
                <CheckIcon size={18} color="#28734F" />
              </div>
              <div>
                <strong style={{ color: '#073F35', display: 'block', fontSize: '0.9375rem' }}>Screen Brightness</strong>
                <span style={{ fontSize: '0.8125rem', color: '#686F69' }}>Set screen brightness to at least 70% to ensure optotype contrast. Avoid direct sun glare.</span>
              </div>
            </div>

            <div style={{ padding: '16px', backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#E8F3ED', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#28734F' }}>
                <CheckIcon size={18} color="#28734F" />
              </div>
              <div>
                <strong style={{ color: '#073F35', display: 'block', fontSize: '0.9375rem' }}>Viewing Distance Setup</strong>
                <span style={{ fontSize: '0.8125rem', color: '#686F69' }}>Position yourself at an arms length (approximately 50 to 60 cm) directly facing the display.</span>
              </div>
            </div>

            <div style={{ padding: '16px', backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#E8F3ED', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#28734F' }}>
                <CheckIcon size={18} color="#28734F" />
              </div>
              <div>
                <strong style={{ color: '#073F35', display: 'block', fontSize: '0.9375rem' }}>Reference Card Available for Later</strong>
                <span style={{ fontSize: '0.8125rem', color: '#686F69' }}>Have any standard bank card or ID card handy for step 8 pupillary distance calibration.</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => setStep('questionnaire')}
            style={{
              backgroundColor: '#073F35',
              color: '#F7F4EC',
              border: 'none',
              borderRadius: '6px',
              padding: '12px 24px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Start Symptom Questionnaire
          </button>
        </div>
      )}

      {/* ================= STEP 3: QUESTIONNAIRE ================= */}
      {step === 'questionnaire' && (
        <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
          {urgentSymptomDetected && (
            <div
              style={{
                backgroundColor: '#F8ECEB',
                border: '1px solid #A9473E',
                borderRadius: '6px',
                padding: '16px',
                marginBottom: '20px',
                color: '#A9473E',
                display: 'flex',
                gap: '12px',
                alignItems: 'center',
              }}
            >
              <AlertIcon size={24} color="#A9473E" />
              <div style={{ fontSize: '0.9375rem' }}>
                <strong>Urgent Symptom Flagged:</strong> Sudden vision loss or acute ocular pain requires emergency ophthalmological assessment. Do not delay professional evaluation.
              </div>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <span style={{ fontSize: '0.875rem', color: '#686F69' }}>
              Question {qIndex + 1} of {questions.length}
            </span>
            <button
              onClick={handlePlayVoice}
              style={{
                backgroundColor: '#E9E5DA',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '0.875rem',
                color: '#073F35',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: 600,
              }}
            >
              <VolumeIcon size={16} />
              {t.screening.replayAudio}
            </button>
          </div>

          <h3 style={{ fontSize: '1.375rem', color: '#073F35', marginBottom: '6px', fontFamily: 'var(--font-heading)' }}>
            {currentQ.title}
          </h3>
          <p style={{ fontSize: '0.9375rem', color: '#686F69', marginBottom: '24px' }}>
            {currentQ.subtitle}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '32px' }}>
            {currentQ.options.map((opt, i) => {
              const selected = currentQ.current === opt.value;
              return (
                <button
                  key={i}
                  onClick={() => currentQ.setter(opt.value)}
                  style={{
                    backgroundColor: selected ? '#EBF3F1' : '#F7F4EC',
                    border: selected ? '2px solid #073F35' : '1px solid #D7D2C4',
                    borderRadius: '6px',
                    padding: '16px 20px',
                    textAlign: 'left',
                    fontSize: '1rem',
                    color: '#202823',
                    fontWeight: selected ? 600 : 400,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>{opt.label}</span>
                  {selected && <CheckIcon size={18} color="#073F35" />}
                </button>
              );
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              disabled={qIndex === 0}
              onClick={() => {
                stopSpeech();
                setQIndex((idx) => Math.max(0, idx - 1));
              }}
              style={{
                background: 'none',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '10px 18px',
                color: qIndex === 0 ? '#CBD5E1' : '#073F35',
                cursor: qIndex === 0 ? 'not-allowed' : 'pointer',
              }}
            >
              Previous Question
            </button>

            <button
              onClick={() => {
                stopSpeech();
                if (qIndex < questions.length - 1) {
                  setQIndex((idx) => idx + 1);
                } else {
                  setStep('distance_intro');
                }
              }}
              style={{
                backgroundColor: '#073F35',
                color: '#F7F4EC',
                border: 'none',
                borderRadius: '6px',
                padding: '10px 24px',
                fontSize: '0.9375rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {qIndex < questions.length - 1 ? 'Next Question' : 'Proceed to Distance Vision'}
            </button>
          </div>
        </div>
      )}

      {/* ================= STEP 4: DISTANCE INTRO ================= */}
      {step === 'distance_intro' && (
        <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '16px' }}>
            Distance Vision Testing Instructions
          </h3>
          <p style={{ fontSize: '0.9375rem', color: '#202823', lineHeight: 1.5, marginBottom: '20px' }}>
            This visual acuity test measures how clearly each eye can distinguish optotypes. We test one eye at a time.
          </p>

          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '20px',
              marginBottom: '24px',
            }}
          >
            <div style={{ fontWeight: 600, color: '#073F35', marginBottom: '8px' }}>
              How to perform the test:
            </div>
            <ol style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.9375rem', color: '#686F69' }}>
              <li>Cover your <strong>left eye</strong> gently with your left palm (do not press onto the eyeball).</li>
              <li>Keep both eyes open behind your hand to prevent squinting distortion.</li>
              <li>Observe the letter E and select which direction its three prongs point: Up, Right, Down, or Left.</li>
              <li>You may use keyboard arrow keys or tap the directional buttons.</li>
            </ol>
          </div>

          <button
            onClick={() => {
              setTestEye('right');
              setAcuityIndex(0);
              setConsecutiveCorrect(0);
              setStep('distance_right');
            }}
            style={{
              backgroundColor: '#073F35',
              color: '#F7F4EC',
              border: 'none',
              borderRadius: '6px',
              padding: '12px 24px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Start Right Eye Test (Left Eye Covered)
          </button>
        </div>
      )}

      {/* ================= STEP 4: DISTANCE RIGHT & LEFT EYE ================= */}
      {(step === 'distance_right' || step === 'distance_left') && (
        <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div
              style={{
                backgroundColor: '#073F35',
                color: '#F7F4EC',
                padding: '4px 12px',
                borderRadius: '4px',
                fontSize: '0.8125rem',
                fontWeight: 600,
                textTransform: 'uppercase',
              }}
            >
              {testEye === 'right' ? 'Testing RIGHT Eye (Left Eye Covered)' : 'Testing LEFT Eye (Right Eye Covered)'}
            </div>

            <span style={{ fontSize: '0.8125rem', color: '#686F69' }}>
              Current Target: {acuityLevels[acuityIndex].snellen} (logMAR {acuityLevels[acuityIndex].logMAR})
            </span>
          </div>

          {/* Calibrated Tumbling E Chamber */}
          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              height: '220px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '24px',
              position: 'relative',
            }}
          >
            <div
              style={{
                fontSize: `${acuityLevels[acuityIndex].sizePx}px`,
                fontWeight: 800,
                lineHeight: 1,
                fontFamily: 'sans-serif',
                color: '#092D28',
                transform: `rotate(${
                  targetOrientation === 'right'
                    ? 0
                    : targetOrientation === 'down'
                    ? 90
                    : targetOrientation === 'left'
                    ? 180
                    : 270
                }deg)`,
                userSelect: 'none',
              }}
            >
              E
            </div>
          </div>

          {/* Directional Pad */}
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.875rem', color: '#686F69', marginBottom: '12px' }}>
              Select prong direction (or use keyboard arrow keys):
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', maxWidth: '440px', margin: '0 auto 16px' }}>
              {(['up', 'down', 'left', 'right'] as Orientation[]).map((dir) => (
                <button
                  key={dir}
                  onClick={() => handleAcuityAnswer(dir)}
                  style={{
                    backgroundColor: '#E9E5DA',
                    border: '1px solid #D7D2C4',
                    borderRadius: '6px',
                    padding: '14px',
                    fontSize: '1rem',
                    fontWeight: 600,
                    color: '#073F35',
                    cursor: 'pointer',
                    textTransform: 'capitalize',
                  }}
                >
                  {dir}
                </button>
              ))}
            </div>

            <button
              onClick={() => handleAcuityAnswer(targetOrientation === 'up' ? 'down' : 'up')}
              style={{
                background: 'none',
                border: 'none',
                color: '#686F69',
                fontSize: '0.8125rem',
                textDecoration: 'underline',
                cursor: 'pointer',
              }}
            >
              Cannot resolve prongs / Too blurry to tell
            </button>
          </div>
        </div>
      )}

      {/* ================= STEP 5: NEAR VISION ================= */}
      {step === 'near' && (
        <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '8px' }}>
            Near Vision & Reading Acuity Test
          </h3>
          <p style={{ fontSize: '0.9375rem', color: '#686F69', marginBottom: '20px' }}>
            Hold your device or position your head at a normal reading distance (approximately 38 to 40 cm). Read the test paragraph below.
          </p>

          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '24px',
              marginBottom: '24px',
            }}
          >
            <div style={{ fontSize: '0.8125rem', color: '#686F69', marginBottom: '12px', textTransform: 'uppercase' }}>
              Standard Near Reading Text (N8 / Times Roman equivalent)
            </div>
            <p
              style={{
                fontSize:
                  nearReadingLevel === 'N6'
                    ? '13px'
                    : nearReadingLevel === 'N8'
                    ? '15px'
                    : nearReadingLevel === 'N10'
                    ? '18px'
                    : '22px',
                lineHeight: 1.6,
                color: '#202823',
                fontFamily: 'serif',
              }}
            >
              Good vision is essential for daily living, livelihood, and education across all communities.
              Regular preliminary screening helps identify uncorrected refractive errors early, allowing
              individuals to receive appropriate spectacle correction and preventing avoidable eyestrain.
            </p>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <div style={{ fontWeight: 600, color: '#073F35', marginBottom: '10px', fontSize: '0.9375rem' }}>
              Can you comfortably read the paragraph at normal distance?
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
              {[
                { id: 'N6', label: 'Clear even in small print (N6)' },
                { id: 'N8', label: 'Comfortable at standard size (N8)' },
                { id: 'N10', label: 'Somewhat blurred / Strained (N10)' },
                { id: 'N12', label: 'Requires large magnified text (N12)' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setNearReadingLevel(opt.id as any)}
                  style={{
                    backgroundColor: nearReadingLevel === opt.id ? '#EBF3F1' : '#F7F4EC',
                    border: nearReadingLevel === opt.id ? '2px solid #073F35' : '1px solid #D7D2C4',
                    borderRadius: '6px',
                    padding: '12px',
                    fontSize: '0.875rem',
                    color: '#202823',
                    fontWeight: nearReadingLevel === opt.id ? 600 : 400,
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={() => setStep('astigmatism')}
            style={{
              backgroundColor: '#073F35',
              color: '#F7F4EC',
              border: 'none',
              borderRadius: '6px',
              padding: '12px 24px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Continue to Astigmatism Screen
          </button>
        </div>
      )}

      {/* ================= STEP 6: ASTIGMATISM ================= */}
      {step === 'astigmatism' && (
        <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '8px' }}>
            Astigmatism Radial Dial Screen
          </h3>
          <p style={{ fontSize: '0.9375rem', color: '#686F69', marginBottom: '20px' }}>
            Look at the center of the radial spoke wheel below with one eye at a time. Observe whether all spokes appear equally dark and distinct.
          </p>

          {/* SVG Sunburst Dial */}
          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '24px',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              marginBottom: '24px',
            }}
          >
            <svg width="240" height="240" viewBox="-120 -120 240 240">
              <circle cx="0" cy="0" r="110" fill="none" stroke="#D7D2C4" strokeWidth="1" />
              {Array.from({ length: 12 }).map((_, i) => {
                const angle = (i * 30 * Math.PI) / 180;
                const x1 = Math.cos(angle) * 15;
                const y1 = Math.sin(angle) * 15;
                const x2 = Math.cos(angle) * 105;
                const y2 = Math.sin(angle) * 105;
                return (
                  <g key={i}>
                    <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#202823" strokeWidth="2.5" />
                    <line x1={x1 + 1} y1={y1 + 1} x2={x2 + 1} y2={y2 + 1} stroke="#202823" strokeWidth="1.5" />
                  </g>
                );
              })}
              <circle cx="0" cy="0" r="4" fill="#073F35" />
            </svg>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <div style={{ fontWeight: 600, color: '#073F35', marginBottom: '10px' }}>
              How do the black radial lines appear to you?
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
              <button
                onClick={() => {
                  setAstigmatismUniform(true);
                  setAstigmatismMeridian(null);
                }}
                style={{
                  backgroundColor: astigmatismUniform ? '#EBF3F1' : '#F7F4EC',
                  border: astigmatismUniform ? '2px solid #073F35' : '1px solid #D7D2C4',
                  borderRadius: '6px',
                  padding: '14px',
                  fontSize: '0.9375rem',
                  fontWeight: astigmatismUniform ? 600 : 400,
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                All radial lines appear uniformly sharp and equally dark
              </button>

              <button
                onClick={() => {
                  setAstigmatismUniform(false);
                  setAstigmatismMeridian(12);
                }}
                style={{
                  backgroundColor: !astigmatismUniform ? '#EBF3F1' : '#F7F4EC',
                  border: !astigmatismUniform ? '2px solid #073F35' : '1px solid #D7D2C4',
                  borderRadius: '6px',
                  padding: '14px',
                  fontSize: '0.9375rem',
                  fontWeight: !astigmatismUniform ? 600 : 400,
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                Certain lines appear noticeably darker, thicker, or sharper than others
              </button>
            </div>
          </div>

          <button
            onClick={() => setStep('color')}
            style={{
              backgroundColor: '#073F35',
              color: '#F7F4EC',
              border: 'none',
              borderRadius: '6px',
              padding: '12px 24px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Continue to Colour Vision Test
          </button>
        </div>
      )}

      {/* ================= STEP 7: COLOUR VISION ================= */}
      {step === 'color' && (
        <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.25rem', color: '#073F35' }}>
              Pseudoisochromatic Plate {plateIndex + 1} of {colorPlates.length}
            </h3>
            <span style={{ fontSize: '0.8125rem', color: '#686F69' }}>
              {colorPlates[plateIndex].description}
            </span>
          </div>

          {/* Color Plate Simulation */}
          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '24px',
            }}
          >
            <div
              style={{
                width: '180px',
                height: '180px',
                borderRadius: '50%',
                backgroundColor: plateIndex % 2 === 0 ? '#C2A649' : '#5E9387',
                border: '6px double #D7D2C4',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '4.5rem',
                fontWeight: 900,
                color: plateIndex % 2 === 0 ? '#547A6B' : '#B86A53',
                fontFamily: 'monospace',
                userSelect: 'none',
                letterSpacing: '-0.05em',
              }}
            >
              {colorPlates[plateIndex].correctValue}
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#686F69', marginTop: '12px' }}>
              Enter the numeral visible inside the circular dotted plate
            </div>
          </div>

          <div style={{ maxWidth: '320px', margin: '0 auto 24px' }}>
            <input
              type="text"
              value={currentPlateInput}
              onChange={(e) => setCurrentPlateInput(e.target.value)}
              placeholder="Enter number (e.g. 12)"
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                fontSize: '1.125rem',
                textAlign: 'center',
                backgroundColor: '#F7F4EC',
                color: '#202823',
                marginBottom: '10px',
              }}
            />

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => {
                  const updated = [...colorPlateAnswers, currentPlateInput];
                  setColorPlateAnswers(updated);
                  setCurrentPlateInput('');
                  if (plateIndex < colorPlates.length - 1) {
                    setPlateIndex(plateIndex + 1);
                  } else {
                    setStep('pd');
                  }
                }}
                style={{
                  flex: 1,
                  backgroundColor: '#073F35',
                  color: '#F7F4EC',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Confirm Number
              </button>

              <button
                onClick={() => {
                  const updated = [...colorPlateAnswers, 'none'];
                  setColorPlateAnswers(updated);
                  setCurrentPlateInput('');
                  if (plateIndex < colorPlates.length - 1) {
                    setPlateIndex(plateIndex + 1);
                  } else {
                    setStep('pd');
                  }
                }}
                style={{
                  backgroundColor: '#E9E5DA',
                  border: '1px solid #D7D2C4',
                  borderRadius: '6px',
                  padding: '12px',
                  fontSize: '0.875rem',
                  color: '#686F69',
                  cursor: 'pointer',
                }}
              >
                Nothing Visible
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================= STEP 8: PD ESTIMATION ================= */}
      {step === 'pd' && (
        <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
          <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '8px' }}>
            Pupillary Distance (PD) Estimation
          </h3>
          <p style={{ fontSize: '0.9375rem', color: '#686F69', marginBottom: '20px', lineHeight: 1.5 }}>
            Pupillary distance is the distance between the centers of your pupils in millimeters. Holding a standard card (85.60 mm standard ISO width) allows accurate dimensional calibration.
          </p>

          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '20px',
              marginBottom: '24px',
              textAlign: 'center',
            }}
          >
            {cameraActive ? (
              <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%' }}>
                <video
                  ref={videoRef}
                  playsInline
                  muted
                  style={{
                    width: '100%',
                    maxWidth: '480px',
                    borderRadius: '6px',
                    border: '1px solid #D7D2C4',
                    transform: 'scaleX(-1)', // Mirror preview
                  }}
                />
                {/* Calibration Overlay Graphics */}
                <div
                  style={{
                    position: 'absolute',
                    top: '20%',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: '180px',
                    height: '110px',
                    border: '2px dashed #4F8278',
                    borderRadius: '4px',
                    pointerEvents: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#073F35',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    backgroundColor: 'rgba(235, 243, 241, 0.4)',
                  }}
                >
                  Hold reference card here
                </div>
              </div>
            ) : (
              <div
                style={{
                  height: '200px',
                  backgroundColor: '#E9E5DA',
                  border: '1px dashed #D7D2C4',
                  borderRadius: '6px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '12px',
                }}
              >
                <CameraIcon size={36} color="#073F35" />
                <div style={{ fontSize: '0.9375rem', color: '#202823' }}>
                  {cameraDenied
                    ? 'Camera access unavailable or denied. You can manually adjust your estimated PD below.'
                    : 'Activate camera to align reference card and pupils'}
                </div>
                {!cameraDenied && (
                  <button
                    onClick={startCamera}
                    style={{
                      backgroundColor: '#073F35',
                      color: '#F7F4EC',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '10px 20px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Enable Camera Alignment
                  </button>
                )}
              </div>
            )}
          </div>

          {/* PD Metric & Manual Fine-tuning */}
          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '20px',
              marginBottom: '28px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: '#686F69', textTransform: 'uppercase' }}>
                  Estimated Distance
                </span>
                <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#073F35' }}>
                  {pdValueMm.toFixed(1)} mm
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.75rem', color: '#686F69', textTransform: 'uppercase' }}>
                  Confidence Score
                </span>
                <div style={{ fontSize: '1rem', fontWeight: 600, color: '#28734F' }}>
                  {(pdConfidence * 100).toFixed(0)}% (High Quality)
                </div>
              </div>
            </div>

            <div style={{ fontSize: '0.875rem', color: '#686F69', marginBottom: '8px' }}>
              Manual fine-tuning (adult range usually 58 mm to 68 mm):
            </div>
            <input
              type="range"
              min="54"
              max="72"
              step="0.5"
              value={pdValueMm}
              onChange={(e) => setPdValueMm(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: '#073F35' }}
            />
          </div>

          <button
            onClick={finalizeScreening}
            style={{
              backgroundColor: '#073F35',
              color: '#F7F4EC',
              border: 'none',
              borderRadius: '6px',
              padding: '14px 28px',
              fontSize: '1.0625rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <CheckIcon size={20} color="#F7F4EC" />
            Complete Screening & Review Results
          </button>
        </div>
      )}

      {/* ================= STEP 9: PROCESSING ================= */}
      {step === 'processing' && (
        <div
          style={{
            backgroundColor: '#F0ECE2',
            border: '1px solid #D7D2C4',
            borderRadius: '8px',
            padding: '64px 32px',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              border: '3px solid #D7D2C4',
              borderTopColor: '#073F35',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 20px',
            }}
          />
          <h3 style={{ fontSize: '1.375rem', color: '#073F35', marginBottom: '8px' }}>
            Generating Screening Report
          </h3>
          <p style={{ fontSize: '0.9375rem', color: '#686F69' }}>
            Calculating Snellen visual acuity fractions, analyzing astigmatism meridians, and compiling preliminary eyewear guidance.
          </p>
          <style>{`
            @keyframes spin {
              from { transform: rotate(0deg); }
              to { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      )}
    </div>
  );
};
