import React, { useState } from 'react';
import { CheckIcon, RefreshIcon } from '../icons';

export const InteractiveDemo: React.FC = () => {
  const orientations = ['right', 'down', 'left', 'up'] as const;
  type Orientation = typeof orientations[number];

  const levels = [
    { snellen: '20/100', sizePx: 64, logMAR: 0.7 },
    { snellen: '20/70', sizePx: 48, logMAR: 0.54 },
    { snellen: '20/50', sizePx: 36, logMAR: 0.4 },
    { snellen: '20/30', sizePx: 26, logMAR: 0.18 },
    { snellen: '20/20', sizePx: 18, logMAR: 0.0 },
  ];

  const [currentLevelIndex, setCurrentLevelIndex] = useState(0);
  const [targetOrientation, setTargetOrientation] = useState<Orientation>('right');
  const [correctCount, setCorrectCount] = useState(0);
  const [totalAttempts, setTotalAttempts] = useState(0);
  const [demoCompleted, setDemoCompleted] = useState(false);
  const [lastFeedback, setLastFeedback] = useState<string | null>(null);

  const getRotationDeg = (orientation: Orientation) => {
    switch (orientation) {
      case 'right': return 0;
      case 'down': return 90;
      case 'left': return 180;
      case 'up': return 270;
    }
  };

  const handleAnswer = (selected: Orientation) => {
    if (demoCompleted) return;

    const isCorrect = selected === targetOrientation;
    setTotalAttempts((prev) => prev + 1);

    if (isCorrect) {
      setCorrectCount((prev) => prev + 1);
      setLastFeedback('Correct direction');
    } else {
      setLastFeedback('Incorrect direction');
    }

    if (currentLevelIndex < levels.length - 1) {
      setCurrentLevelIndex((prev) => prev + 1);
      // Pick random orientation
      const nextOri = orientations[Math.floor(Math.random() * orientations.length)];
      setTargetOrientation(nextOri);
    } else {
      setDemoCompleted(true);
    }
  };

  const resetDemo = () => {
    setCurrentLevelIndex(0);
    setCorrectCount(0);
    setTotalAttempts(0);
    setDemoCompleted(false);
    setLastFeedback(null);
    setTargetOrientation('right');
  };

  const currentLevel = levels[currentLevelIndex];

  return (
    <div
      style={{
        backgroundColor: '#F0ECE2',
        border: '1px solid #D7D2C4',
        borderRadius: '8px',
        padding: '28px',
        maxWidth: '820px',
        margin: '0 auto',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #D7D2C4',
          paddingBottom: '16px',
          marginBottom: '20px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <span
            style={{
              backgroundColor: '#073F35',
              color: '#F7F4EC',
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '0.75rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            Interactive Product Preview
          </span>
          <h3
            style={{
              fontSize: '1.25rem',
              marginTop: '6px',
              fontFamily: 'var(--font-heading)',
              color: '#073F35',
            }}
          >
            Visual Acuity Tumbling E Optotype Demonstration
          </h3>
        </div>

        <div style={{ fontSize: '0.875rem', color: '#686F69' }}>
          Step {currentLevelIndex + 1} of {levels.length} (Calibrated Scale)
        </div>
      </div>

      {!demoCompleted ? (
        <div>
          <p style={{ fontSize: '0.9375rem', color: '#202823', marginBottom: '20px' }}>
            Sit approximately 40 to 60 cm from your screen. Indicate which direction the branches of the <strong>letter E</strong> are pointing:
          </p>

          {/* Test Display Chamber */}
          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              height: '190px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '24px',
              position: 'relative',
            }}
          >
            <div
              style={{
                fontSize: `${currentLevel.sizePx}px`,
                fontWeight: 800,
                lineHeight: 1,
                fontFamily: 'sans-serif',
                color: '#092D28',
                transform: `rotate(${getRotationDeg(targetOrientation)}deg)`,
                transition: 'none',
                userSelect: 'none',
              }}
            >
              E
            </div>

            <div
              style={{
                position: 'absolute',
                bottom: '8px',
                right: '12px',
                fontSize: '0.75rem',
                color: '#686F69',
              }}
            >
              Target Equivalent: {currentLevel.snellen} (logMAR {currentLevel.logMAR})
            </div>
          </div>

          {lastFeedback && (
            <div
              style={{
                textAlign: 'center',
                fontSize: '0.875rem',
                fontWeight: 600,
                color: lastFeedback === 'Correct direction' ? '#28734F' : '#A9473E',
                marginBottom: '16px',
              }}
            >
              {lastFeedback}
            </div>
          )}

          {/* Response Buttons */}
          <div style={{ textAlign: 'center', marginBottom: '12px' }}>
            <div style={{ fontSize: '0.8125rem', color: '#686F69', marginBottom: '10px' }}>
              Select direction:
            </div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: '12px',
                maxWidth: '440px',
                margin: '0 auto',
              }}
            >
              {(['up', 'down', 'left', 'right'] as Orientation[]).map((dir) => (
                <button
                  key={dir}
                  onClick={() => handleAnswer(dir)}
                  style={{
                    backgroundColor: '#E9E5DA',
                    border: '1px solid #D7D2C4',
                    borderRadius: '6px',
                    padding: '12px 16px',
                    fontSize: '0.9375rem',
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
          </div>
        </div>
      ) : (
        /* Completed Demo Summary */
        <div style={{ textAlign: 'center', padding: '16px 8px' }}>
          <div
            style={{
              width: '52px',
              height: '52px',
              borderRadius: '50%',
              backgroundColor: '#E8F3ED',
              border: '1px solid #28734F',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
              color: '#28734F',
            }}
          >
            <CheckIcon size={28} color="#28734F" />
          </div>

          <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', color: '#073F35', marginBottom: '8px' }}>
            Demonstration Complete
          </h4>
          <p style={{ fontSize: '0.9375rem', color: '#686F69', maxWidth: '520px', margin: '0 auto 18px', lineHeight: '1.5' }}>
            You correctly identified {correctCount} of {totalAttempts} test orientations in this interactive preview.
            In the full vision screening, both eyes are tested separately with distance verification, near vision reading, astigmatism checking, and camera-guided pupillary distance measurement.
          </p>

          <div
            style={{
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '16px',
              maxWidth: '460px',
              margin: '0 auto 20px',
              textAlign: 'left',
            }}
          >
            <div style={{ fontSize: '0.8125rem', color: '#686F69', textTransform: 'uppercase', marginBottom: '4px' }}>
              Sample Preliminary Metric
            </div>
            <div style={{ fontSize: '1.125rem', fontWeight: 600, color: '#092D28' }}>
              Estimated Visual Acuity: {correctCount >= 4 ? '20/20 (Preliminary Normal)' : '20/40 (Preliminary Mild Reduction)'}
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#686F69', marginTop: '6px' }}>
              No persistent health record was created. This was an unrecorded demonstration.
            </div>
          </div>

          <button
            onClick={resetDemo}
            style={{
              backgroundColor: '#E9E5DA',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '8px 18px',
              fontSize: '0.875rem',
              fontWeight: 600,
              color: '#073F35',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <RefreshIcon size={16} />
            Try Preview Again
          </button>
        </div>
      )}
    </div>
  );
};
