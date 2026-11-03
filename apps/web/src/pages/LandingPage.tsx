import React from 'react';
import { EyeIcon, GlassesIcon, VolumeIcon, ShopIcon, UserIcon, ArrowRightIcon, ActivityIcon } from '../components/icons';
import { ClinicalDisclaimerBanner } from '../components/layout/ClinicalDisclaimerBanner';
import { InteractiveDemo } from '../components/live-demo/InteractiveDemo';
import { useLanguage } from '../localization/useLanguage';

interface LandingPageProps {
  onNavigate: (route: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const { t } = useLanguage();

  return (
    <div style={{ paddingBottom: '32px' }}>
      {/* Clinical Disclaimer Banner */}
      <div style={{ maxWidth: '1280px', margin: '16px auto 0', padding: '0 24px' }}>
        <ClinicalDisclaimerBanner onLearnMore={() => onNavigate('disclaimer')} />
      </div>

      {/* 2. Hero Section */}
      <section
        style={{
          maxWidth: '1280px',
          margin: '0 auto',
          padding: '48px 24px 40px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '48px',
          alignItems: 'center',
        }}
      >
        <div>
          <div
            style={{
              display: 'inline-block',
              backgroundColor: '#E9E5DA',
              border: '1px solid #D7D2C4',
              borderRadius: '4px',
              padding: '4px 12px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              color: '#073F35',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              marginBottom: '16px',
            }}
          >
            Digital Vision Care Infrastructure
          </div>

          <h1
            style={{
              fontSize: 'clamp(2.25rem, 5vw, 3.25rem)',
              lineHeight: 1.15,
              color: '#073F35',
              marginBottom: '20px',
              letterSpacing: '-0.02em',
            }}
          >
            {t.hero.headline}
          </h1>

          <p
            style={{
              fontSize: '1.125rem',
              color: '#202823',
              lineHeight: 1.6,
              marginBottom: '32px',
              maxWidth: '540px',
            }}
          >
            {t.hero.subheadline}
          </p>

          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '28px' }}>
            <button
              onClick={() => onNavigate('screening')}
              style={{
                backgroundColor: '#073F35',
                color: '#F7F4EC',
                border: 'none',
                borderRadius: '6px',
                padding: '14px 28px',
                fontSize: '1rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <EyeIcon size={20} color="#F7F4EC" />
              {t.hero.startCta}
            </button>

            <button
              onClick={() => onNavigate('how-it-works')}
              style={{
                backgroundColor: '#E9E5DA',
                color: '#073F35',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '14px 24px',
                fontSize: '1rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              {t.hero.howCta}
              <ArrowRightIcon size={16} />
            </button>
          </div>

          <div
            style={{
              fontSize: '0.875rem',
              color: '#686F69',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#28734F' }} />
            {t.hero.ruralNotice}
          </div>
        </div>

        {/* Visual representation: Authentic Indian rural eye screening scene */}
        <div>
          <div
            style={{
              backgroundColor: '#E9E5DA',
              border: '1px solid #D7D2C4',
              borderRadius: '8px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '280px',
                backgroundColor: '#092D28',
                backgroundImage:
                  'radial-gradient(circle at 70% 30%, #0d4a3f 0%, #092D28 100%)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                padding: '24px',
                color: '#F7F4EC',
                textAlign: 'center',
                position: 'relative',
              }}
            >
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  border: '2px solid #4F8278',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px',
                }}
              >
                <EyeIcon size={34} color="#F7F4EC" />
              </div>
              <div style={{ fontFamily: 'var(--font-heading)', fontSize: '1.25rem', marginBottom: '6px' }}>
                Rural Vision Camp and Kiosk Protocol
              </div>
              <p style={{ fontSize: '0.875rem', color: '#D2E4E0', maxWidth: '380px', lineHeight: 1.5 }}>
                Standardized vision acuity cards, mobile voice questionnaire, and pupillary alignment at primary health outposts.
              </p>
            </div>

            <div
              style={{
                padding: '20px',
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '16px',
                backgroundColor: '#F0ECE2',
                borderTop: '1px solid #D7D2C4',
              }}
            >
              <div>
                <div style={{ fontSize: '0.75rem', color: '#686F69', textTransform: 'uppercase' }}>
                  Acuity Protocol
                </div>
                <div style={{ fontWeight: 600, color: '#073F35', fontSize: '1rem', marginTop: '2px' }}>
                  Tumbling E & Snellen
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#686F69', textTransform: 'uppercase' }}>
                  Camera Metric
                </div>
                <div style={{ fontWeight: 600, color: '#073F35', fontSize: '1rem', marginTop: '2px' }}>
                  Reference Card PD
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Capability Introduction (2x2 Asymmetric Editorial Grid) */}
      <section
        style={{
          backgroundColor: '#F0ECE2',
          borderTop: '1px solid #D7D2C4',
          borderBottom: '1px solid #D7D2C4',
          padding: '64px 24px',
        }}
      >
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          <div style={{ maxWidth: '640px', marginBottom: '40px' }}>
            <h2
              style={{
                fontSize: '2rem',
                color: '#073F35',
                marginBottom: '12px',
              }}
            >
              Core Screening Capabilities
            </h2>
            <p style={{ fontSize: '1.0625rem', color: '#686F69', lineHeight: 1.6 }}>
              Built specifically to bridge the preliminary vision gap where optometrists are sparse, enabling structured screening and rapid referrals.
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '24px',
            }}
          >
            <div
              style={{
                backgroundColor: '#F7F4EC',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '28px',
              }}
            >
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '6px',
                  backgroundColor: '#E9E5DA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#073F35',
                  marginBottom: '16px',
                }}
              >
                <EyeIcon size={22} color="#073F35" />
              </div>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '10px' }}>
                Universal Web Accessibility
              </h3>
              <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.6 }}>
                Operates smoothly on standard smartphones and basic desktop computers through any modern web browser without proprietary hardware installations.
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#F7F4EC',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '28px',
              }}
            >
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '6px',
                  backgroundColor: '#E9E5DA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#073F35',
                  marginBottom: '16px',
                }}
              >
                <VolumeIcon size={22} color="#073F35" />
              </div>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '10px' }}>
                Voice-Guided Questionnaire
              </h3>
              <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.6 }}>
                Questions read aloud via high-clarity speech synthesis in Hindi, Odia, and English, allowing users with limited literacy to self-report visual difficulties with ease.
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#F7F4EC',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '28px',
              }}
            >
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '6px',
                  backgroundColor: '#E9E5DA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#073F35',
                  marginBottom: '16px',
                }}
              >
                <GlassesIcon size={22} color="#073F35" />
              </div>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '10px' }}>
                Eyewear & Frame Guidance
              </h3>
              <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.6 }}>
                Evidence-based suggestions for frame dimensions, lens types (single vision, progressive, blue-cut), and facial compatibility without automated prescribing.
              </p>
            </div>

            <div
              style={{
                backgroundColor: '#F7F4EC',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '28px',
              }}
            >
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '6px',
                  backgroundColor: '#E9E5DA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#073F35',
                  marginBottom: '16px',
                }}
              >
                <ShopIcon size={22} color="#073F35" />
              </div>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '10px' }}>
                Optical Shop Integration
              </h3>
              <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.6 }}>
                Dedicated dashboard for local opticians and shopkeepers to manage customer screening history, prepare spectacle orders, and track hospital referrals.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. How OptiGuide Works (Numbered Editorial Process) */}
      <section style={{ maxWidth: '1280px', margin: '0 auto', padding: '64px 24px' }}>
        <div style={{ maxWidth: '640px', marginBottom: '40px' }}>
          <h2 style={{ fontSize: '2rem', color: '#073F35', marginBottom: '12px' }}>
            How OptiGuide Operates
          </h2>
          <p style={{ fontSize: '1.0625rem', color: '#686F69', lineHeight: 1.6 }}>
            A transparent four-step preliminary screening workflow designed for community clarity and clinic trust.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '24px',
          }}
        >
          <div
            style={{
              padding: '24px',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              backgroundColor: '#F7F4EC',
            }}
          >
            <div
              style={{
                fontSize: '1.75rem',
                fontWeight: 700,
                color: '#4F8278',
                fontFamily: 'var(--font-heading)',
                marginBottom: '10px',
              }}
            >
              01
            </div>
            <h4 style={{ fontSize: '1.125rem', color: '#073F35', marginBottom: '8px' }}>
              Answer Symptom Inquiries
            </h4>
            <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.55 }}>
              Identify current vision complaints, headaches, blurred distance text, or reading difficulties with audio assistance.
            </p>
          </div>

          <div
            style={{
              padding: '24px',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              backgroundColor: '#F7F4EC',
            }}
          >
            <div
              style={{
                fontSize: '1.75rem',
                fontWeight: 700,
                color: '#4F8278',
                fontFamily: 'var(--font-heading)',
                marginBottom: '10px',
              }}
            >
              02
            </div>
            <h4 style={{ fontSize: '1.125rem', color: '#073F35', marginBottom: '8px' }}>
              Complete Vision Tests
            </h4>
            <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.55 }}>
              Perform calibrated visual acuity checks, astigmatism fan screening, and pseudoisochromatic colour plates.
            </p>
          </div>

          <div
            style={{
              padding: '24px',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              backgroundColor: '#F7F4EC',
            }}
          >
            <div
              style={{
                fontSize: '1.75rem',
                fontWeight: 700,
                color: '#4F8278',
                fontFamily: 'var(--font-heading)',
                marginBottom: '10px',
              }}
            >
              03
            </div>
            <h4 style={{ fontSize: '1.125rem', color: '#073F35', marginBottom: '8px' }}>
              Receive Screening Summary
            </h4>
            <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.55 }}>
              Get an organized preliminary summary highlighting potential acuity deficits or recommending hospital evaluation.
            </p>
          </div>

          <div
            style={{
              padding: '24px',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              backgroundColor: '#F7F4EC',
            }}
          >
            <div
              style={{
                fontSize: '1.75rem',
                fontWeight: 700,
                color: '#4F8278',
                fontFamily: 'var(--font-heading)',
                marginBottom: '10px',
              }}
            >
              04
            </div>
            <h4 style={{ fontSize: '1.125rem', color: '#073F35', marginBottom: '8px' }}>
              Explore Eyewear Guidance
            </h4>
            <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.55 }}>
              Estimate pupillary distance using standard card calibration and inspect compatible frames from community opticians.
            </p>
          </div>
        </div>
      </section>

      {/* 5. Actual Interactive Product Demonstration */}
      <section
        style={{
          backgroundColor: '#E9E5DA',
          borderTop: '1px solid #D7D2C4',
          borderBottom: '1px solid #D7D2C4',
          padding: '64px 24px',
        }}
      >
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', maxWidth: '680px', margin: '0 auto 36px' }}>
            <h2 style={{ fontSize: '2rem', color: '#073F35', marginBottom: '10px' }}>
              Experience the Screening Interface
            </h2>
            <p style={{ fontSize: '1.0625rem', color: '#686F69', lineHeight: 1.6 }}>
              Test the interactive visual acuity preview below to understand how the self-administered optotype checks operate.
            </p>
          </div>

          <InteractiveDemo />
        </div>
      </section>

      {/* 6. Rural Accessibility & Local Language Support */}
      <section style={{ maxWidth: '1280px', margin: '0 auto', padding: '64px 24px' }}>
        <div
          style={{
            backgroundColor: '#073F35',
            borderRadius: '8px',
            padding: '48px 36px',
            color: '#F7F4EC',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '36px',
            alignItems: 'center',
          }}
        >
          <div>
            <div
              style={{
                color: '#A5C9C1',
                textTransform: 'uppercase',
                fontSize: '0.8125rem',
                fontWeight: 600,
                letterSpacing: '0.05em',
                marginBottom: '10px',
              }}
            >
              Rural Community Vision Outreach
            </div>
            <h3 style={{ fontSize: '1.875rem', color: '#F7F4EC', marginBottom: '16px' }}>
              Engineered for Real-World Indian Village Infrastructure
            </h3>
            <p style={{ fontSize: '1rem', color: '#D2E4E0', lineHeight: 1.6, marginBottom: '20px' }}>
              In many rural blocks, certified optometrists visit once a month. OptiGuide provides primary optical shopkeepers and village health workers with an accessible, standardized method to flag vision impairment early.
            </p>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: '1.375rem', fontWeight: 700, color: '#F7F4EC' }}>3 Languages</div>
                <div style={{ fontSize: '0.8125rem', color: '#A5C9C1' }}>English, Hindi, Odia</div>
              </div>
              <div>
                <div style={{ fontSize: '1.375rem', fontWeight: 700, color: '#F7F4EC' }}>Offline-First</div>
                <div style={{ fontSize: '0.8125rem', color: '#A5C9C1' }}>Resilient state cache</div>
              </div>
              <div>
                <div style={{ fontSize: '1.375rem', fontWeight: 700, color: '#F7F4EC' }}>Zero Hardware</div>
                <div style={{ fontSize: '0.8125rem', color: '#A5C9C1' }}>Standard device screen</div>
              </div>
            </div>
          </div>

          <div
            style={{
              backgroundColor: '#092D28',
              border: '1px solid #4F8278',
              borderRadius: '6px',
              padding: '24px',
            }}
          >
            <h4 style={{ fontSize: '1.125rem', color: '#F7F4EC', marginBottom: '12px' }}>
              Voice & Audio Inclusivity
            </h4>
            <p style={{ fontSize: '0.875rem', color: '#D2E4E0', lineHeight: 1.6, marginBottom: '16px' }}>
              By integrating natural Web Speech audio synthesis in regional Indian accents, patients can listen to questions regarding eye pain, blurry near-vision, and light sensitivity without reading strain.
            </p>
            <button
              onClick={() => onNavigate('screening')}
              style={{
                backgroundColor: '#F7F4EC',
                color: '#073F35',
                border: 'none',
                borderRadius: '6px',
                padding: '10px 18px',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              Start Complete Screening Session
            </button>
          </div>
        </div>
      </section>

      {/* 7. Audience Introduction */}
      <section
        style={{
          backgroundColor: '#F0ECE2',
          borderTop: '1px solid #D7D2C4',
          padding: '56px 24px',
        }}
      >
        <div style={{ maxWidth: '1280px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', maxWidth: '600px', margin: '0 auto 36px' }}>
            <h2 style={{ fontSize: '1.875rem', color: '#073F35', marginBottom: '8px' }}>
              Connected Vision Care Ecosystem
            </h2>
            <p style={{ fontSize: '0.9375rem', color: '#686F69' }}>
              Collaborative workflows connecting citizens, rural kiosks, and clinical professionals.
            </p>
          </div>

          {/* Editorial Layout: Two primary sections above, one full-width section beneath */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '24px',
              }}
            >
              <div
                style={{
                  backgroundColor: '#F7F4EC',
                  border: '1px solid #D7D2C4',
                  borderRadius: '6px',
                  padding: '32px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                    <div
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '6px',
                        backgroundColor: '#E9E5DA',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <UserIcon size={20} color="#073F35" />
                    </div>
                    <h3 style={{ fontSize: '1.25rem', color: '#073F35', fontFamily: 'var(--font-heading)' }}>
                      For Individuals & Families
                    </h3>
                  </div>
                  <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.6, marginBottom: '16px' }}>
                    Free, confidential preliminary vision checks designed for home or mobile use. Understand your visual acuity in minutes with voice-guided prompts and receive clear recommendations on whether professional optometrist consultation is advised.
                  </p>
                </div>
                <div style={{ fontSize: '0.8125rem', color: '#073F35', fontWeight: 600 }}>
                  Immediate self-administered screening • No registration barrier
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#F7F4EC',
                  border: '1px solid #D7D2C4',
                  borderRadius: '6px',
                  padding: '32px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                    <div
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '6px',
                        backgroundColor: '#E9E5DA',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <ShopIcon size={20} color="#073F35" />
                    </div>
                    <h3 style={{ fontSize: '1.25rem', color: '#073F35', fontFamily: 'var(--font-heading)' }}>
                      For Optical Shopkeepers
                    </h3>
                  </div>
                  <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.6, marginBottom: '16px' }}>
                    Turn your local optical shop or community counter into a recognized vision screening kiosk. Register walk-in customers, estimate pupillary distance with reference card millimeter calibration, record spectacle orders, and track hospital referrals.
                  </p>
                </div>
                <div style={{ fontSize: '0.8125rem', color: '#073F35', fontWeight: 600 }}>
                  Customer ledger • Reference-card PD • Order and inventory management
                </div>
              </div>
            </div>

            {/* Full-width editorial section beneath */}
            <div
              style={{
                backgroundColor: '#F7F4EC',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '32px',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '24px',
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                  <div
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '6px',
                      backgroundColor: '#E9E5DA',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <ActivityIcon size={20} color="#073F35" />
                  </div>
                  <h3 style={{ fontSize: '1.25rem', color: '#073F35', fontFamily: 'var(--font-heading)' }}>
                    For Eye-Care Professionals & Clinical Referral Networks
                  </h3>
                </div>
                <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.6 }}>
                  Certified optometrists and ophthalmologists receive structured preliminary summaries from community kiosks. Review patient-reported symptom histories, visual acuity fractions, and astigmatism observations before conducting comprehensive dilated evaluations.
                </p>
              </div>

              <div
                style={{
                  backgroundColor: '#F0ECE2',
                  border: '1px solid #D7D2C4',
                  borderRadius: '6px',
                  padding: '20px',
                }}
              >
                <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#073F35', marginBottom: '6px' }}>
                  Clinical Referral Protocol Integration
                </div>
                <div style={{ fontSize: '0.8125rem', color: '#686F69', lineHeight: 1.5 }}>
                  Standardized PDF reports with session timestamps, observation summaries, and urgent symptom triage for expedited hospital care.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

