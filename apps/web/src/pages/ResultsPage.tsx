import React from 'react';
import {
  DownloadIcon,
  CheckIcon,
  AlertIcon,
  GlassesIcon,
  ArrowRightIcon,
} from '../components/icons';
import { ScreeningSession } from '@optiguide/shared';

interface ResultsPageProps {
  session: ScreeningSession;
  onExploreEyewear: () => void;
  onNewScreening: () => void;
  onGoHome: () => void;
}

export const ResultsPage: React.FC<ResultsPageProps> = ({
  session,
  onExploreEyewear,
  onNewScreening,
  onGoHome,
}) => {
  const { recommendations } = session;
  const results = session.results || ({} as any);
  const isReferralNeeded = recommendations?.professionalReferralRequired;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div style={{ maxWidth: '960px', margin: '32px auto', padding: '0 20px', color: '#202823' }}>
      {/* Top Action Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
        className="no-print"
      >
        <div>
          <button
            onClick={onGoHome}
            style={{
              background: 'none',
              border: 'none',
              color: '#4F8278',
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: '0.875rem',
              padding: 0,
              marginBottom: '4px',
              display: 'block',
            }}
          >
            ← Back to OptiGuide Overview
          </button>
          <h2 style={{ fontSize: '1.75rem', color: '#073F35' }}>Preliminary Screening Report</h2>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={handlePrint}
            style={{
              backgroundColor: '#E9E5DA',
              color: '#073F35',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '10px 18px',
              fontSize: '0.9375rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <DownloadIcon size={18} />
            Print or Save PDF Report
          </button>

          <button
            onClick={onExploreEyewear}
            style={{
              backgroundColor: '#073F35',
              color: '#F7F4EC',
              border: 'none',
              borderRadius: '6px',
              padding: '10px 20px',
              fontSize: '0.9375rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <GlassesIcon size={18} color="#F7F4EC" />
            Explore Recommended Eyewear
          </button>
        </div>
      </div>

      {/* Printable Report Document Card */}
      <div
        style={{
          backgroundColor: '#F7F4EC',
          border: '1px solid #D7D2C4',
          borderRadius: '8px',
          padding: '36px',
          marginBottom: '32px',
        }}
        id="printable-report"
      >
        {/* Document Header */}
        <div
          style={{
            borderBottom: '2px solid #073F35',
            paddingBottom: '20px',
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div>
            <div
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.5rem',
                fontWeight: 700,
                color: '#073F35',
              }}
            >
              OptiGuide
            </div>
            <div style={{ fontSize: '0.8125rem', color: '#686F69', textTransform: 'uppercase' }}>
              Standardized Preliminary Vision Screening Summary
            </div>
          </div>

          <div style={{ textAlign: 'right', fontSize: '0.875rem', color: '#686F69' }}>
            <div><strong>Session ID:</strong> {session.id}</div>
            <div><strong>Date:</strong> {new Date(session.completedAt || session.startedAt).toLocaleDateString()}</div>
            <div><strong>Participant:</strong> {session.customerName || 'Walk-in Citizen'}</div>
          </div>
        </div>

        {/* Section A: Screening Overview & Referral Status Banner */}
        {isReferralNeeded ? (
          <div
            style={{
              backgroundColor: '#F8ECEB',
              border: '1px solid #A9473E',
              borderRadius: '6px',
              padding: '16px 20px',
              marginBottom: '28px',
              display: 'flex',
              gap: '14px',
              alignItems: 'flex-start',
            }}
          >
            <AlertIcon size={24} color="#A9473E" />
            <div>
              <strong style={{ color: '#A9473E', fontSize: '1rem', display: 'block', marginBottom: '2px' }}>
                Professional Clinical Referral Recommended
              </strong>
              <p style={{ fontSize: '0.9375rem', color: '#202823', lineHeight: 1.5 }}>
                {recommendations?.referralReason ||
                  'One or more screening parameters indicate reduced visual acuity or asymmetric focusing. We recommend scheduling an evaluation with an eye-care professional.'}
              </p>
            </div>
          </div>
        ) : (
          <div
            style={{
              backgroundColor: '#E8F3ED',
              border: '1px solid #28734F',
              borderRadius: '6px',
              padding: '16px 20px',
              marginBottom: '28px',
              display: 'flex',
              gap: '14px',
              alignItems: 'flex-start',
            }}
          >
            <CheckIcon size={24} color="#28734F" />
            <div>
              <strong style={{ color: '#28734F', fontSize: '1rem', display: 'block', marginBottom: '2px' }}>
                Preliminary Vision Parameters Within Normal Range
              </strong>
              <p style={{ fontSize: '0.9375rem', color: '#202823', lineHeight: 1.5 }}>
                No pronounced acuity deficits were identified in this screening. Routine annual checkups with an optometrist remain advised.
              </p>
            </div>
          </div>
        )}

        {/* Section B: Individual Test Results Grid */}
        <div style={{ marginBottom: '32px' }}>
          <h3
            style={{
              fontSize: '1.1875rem',
              color: '#073F35',
              borderBottom: '1px solid #D7D2C4',
              paddingBottom: '8px',
              marginBottom: '16px',
            }}
          >
            Individual Vision Test Observations
          </h3>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
            }}
          >
            {/* Distance Vision */}
            <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: '#686F69', textTransform: 'uppercase', marginBottom: '4px' }}>
                Distance Acuity (Tumbling E)
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#073F35' }}>
                OD: {results.distanceVision?.rightEye.snellenFraction || '20/20'}
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#073F35', marginTop: '2px' }}>
                OS: {results.distanceVision?.leftEye.snellenFraction || '20/20'}
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', marginTop: '8px' }}>
                Tested at calibrated distance ({results.distanceVision?.unassistedOrCorrected}).
              </div>
            </div>

            {/* Near Vision */}
            <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: '#686F69', textTransform: 'uppercase', marginBottom: '4px' }}>
                Near Reading Acuity
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#073F35' }}>
                {results.nearVision?.readingAcuityLabel || 'N8 standard'}
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', marginTop: '12px' }}>
                Reading distance 38 cm. Clarity rating {results.nearVision?.clarityRating || 4}/5.
              </div>
            </div>

            {/* Astigmatism */}
            <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: '#686F69', textTransform: 'uppercase', marginBottom: '4px' }}>
                Astigmatism Radial Dial
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 700, color: results.astigmatism?.hasUniformClarity ? '#28734F' : '#B77932' }}>
                {results.astigmatism?.hasUniformClarity ? 'Uniform Clarity' : 'Asymmetry Detected'}
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', marginTop: '12px' }}>
                {results.astigmatism?.screeningObservation}
              </div>
            </div>

            {/* Colour Vision */}
            <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: '#686F69', textTransform: 'uppercase', marginBottom: '4px' }}>
                Colour Plate Screening
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#073F35' }}>
                {results.colorVision?.correctPlates} / {results.colorVision?.totalPlates} Correct
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', marginTop: '12px' }}>
                {results.colorVision?.deficiencyIndicated
                  ? 'Possible red-green variation noted.'
                  : 'Standard chromatic discrimination observed.'}
              </div>
            </div>
          </div>
        </div>

        {/* Section C: Pupillary Distance */}
        <div style={{ marginBottom: '32px' }}>
          <h3
            style={{
              fontSize: '1.1875rem',
              color: '#073F35',
              borderBottom: '1px solid #D7D2C4',
              paddingBottom: '8px',
              marginBottom: '16px',
            }}
          >
            Estimated Pupillary Distance (PD)
          </h3>

          <div
            style={{
              backgroundColor: '#F0ECE2',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '16px',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', color: '#686F69', textTransform: 'uppercase' }}>
                Binocular Pupillary Distance
              </div>
              <div style={{ fontSize: '1.875rem', fontWeight: 700, color: '#073F35' }}>
                {results.pdEstimation?.pupillaryDistanceMm.toFixed(1) || '63.0'} mm
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#686F69', marginTop: '4px' }}>
                Monocular estimate: Left {results.pdEstimation?.monocularLeftMm || '31.5'} mm | Right {results.pdEstimation?.monocularRightMm || '31.5'} mm
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <span
                style={{
                  backgroundColor: '#E8F3ED',
                  color: '#28734F',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  fontSize: '0.8125rem',
                  fontWeight: 600,
                }}
              >
                Measurement Confidence: {((results.pdEstimation?.confidenceScore || 0.9) * 100).toFixed(0)}%
              </span>
              <div style={{ fontSize: '0.75rem', color: '#686F69', marginTop: '6px' }}>
                Calibrated with standard ISO reference card width.
              </div>
            </div>
          </div>
        </div>

        {/* Section D: Recommendations */}
        <div style={{ marginBottom: '32px' }}>
          <h3
            style={{
              fontSize: '1.1875rem',
              color: '#073F35',
              borderBottom: '1px solid #D7D2C4',
              paddingBottom: '8px',
              marginBottom: '16px',
            }}
          >
            Preliminary Eyewear & Lens Guidance
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
            {recommendations?.suggestedLensCategories.map((lens) => (
              <div
                key={lens.id}
                style={{
                  backgroundColor: '#F0ECE2',
                  border: '1px solid #D7D2C4',
                  borderRadius: '6px',
                  padding: '18px',
                }}
              >
                <div style={{ fontWeight: 600, color: '#073F35', fontSize: '1rem', marginBottom: '6px' }}>
                  {lens.title}
                </div>
                <p style={{ fontSize: '0.875rem', color: '#686F69', lineHeight: 1.5, marginBottom: '10px' }}>
                  {lens.description}
                </p>
                <div style={{ fontSize: '0.8125rem', color: '#073F35' }}>
                  {lens.benefits.map((b, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '2px' }}>
                      <span style={{ color: '#28734F' }}>•</span> {b}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div
            style={{
              marginTop: '16px',
              padding: '14px',
              backgroundColor: '#E9E5DA',
              borderRadius: '6px',
              fontSize: '0.875rem',
              color: '#202823',
            }}
          >
            <strong>Suggested Frame Categories:</strong>{' '}
            {recommendations?.suggestedFrameShapes.join(', ') || 'Rectangular, Classic Round'}
            <div style={{ fontSize: '0.8125rem', color: '#686F69', marginTop: '4px' }}>
              Selected to match estimated pupillary width ({results.pdEstimation?.pupillaryDistanceMm.toFixed(1)} mm) and facial balance.
            </div>
          </div>
        </div>

        {/* Section E: Legal & Medical Limitation Disclaimer */}
        <div
          style={{
            borderTop: '1px solid #D7D2C4',
            paddingTop: '20px',
            fontSize: '0.8125rem',
            color: '#686F69',
            lineHeight: 1.55,
          }}
        >
          <strong>Notice of Clinical Limitation:</strong> This summary is generated from self-reported symptoms and computer-screen optotype responses. It does NOT constitute a confirmed prescription, refraction certificate, or diagnosis of eye disease. A qualified optometrist or ophthalmologist must perform a formal clinical examination before obtaining corrective lenses or initiating medical therapy.
        </div>
      </div>

      {/* Footer Navigation */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
        className="no-print"
      >
        <button
          onClick={onNewScreening}
          style={{
            backgroundColor: '#E9E5DA',
            border: '1px solid #D7D2C4',
            borderRadius: '6px',
            padding: '10px 18px',
            fontSize: '0.9375rem',
            fontWeight: 600,
            color: '#073F35',
            cursor: 'pointer',
          }}
        >
          Start Another Screening
        </button>

        <button
          onClick={onExploreEyewear}
          style={{
            backgroundColor: '#073F35',
            color: '#F7F4EC',
            border: 'none',
            borderRadius: '6px',
            padding: '12px 24px',
            fontSize: '1rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          Browse Frames & Try On
          <ArrowRightIcon size={16} />
        </button>
      </div>

      {/* Print Specific CSS */}
      <style>{`
        @media print {
          .no-print {
            display: none !important;
          }
          body {
            background-color: #FFFFFF !important;
            color: #000000 !important;
          }
          #printable-report {
            border: none !important;
            padding: 0 !important;
            background: none !important;
          }
        }
      `}</style>
    </div>
  );
};
