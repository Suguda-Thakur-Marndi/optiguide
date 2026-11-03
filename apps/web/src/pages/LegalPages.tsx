import React, { useState } from 'react';
import { ShieldAlertIcon, CheckIcon } from '../components/icons';

interface LegalPagesProps {
  page: 'privacy' | 'terms' | 'disclaimer' | 'about' | 'contact' | 'faq' | 'for-shops' | 'how-it-works';
  onNavigate: (page: string) => void;
}

export const LegalPages: React.FC<LegalPagesProps> = ({ page, onNavigate }) => {
  const [contactSubmitted, setContactSubmitted] = useState(false);
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactMessage, setContactMessage] = useState('');

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setContactSubmitted(true);
  };

  return (
    <div style={{ maxWidth: '960px', margin: '40px auto', padding: '0 24px', color: '#202823' }}>
      {/* ================= PRIVACY POLICY ================= */}
      {page === 'privacy' && (
        <div>
          <span style={{ fontSize: '0.8125rem', color: '#4F8278', fontWeight: 600, textTransform: 'uppercase' }}>
            Data Privacy & Camera Ethics
          </span>
          <h2 style={{ fontSize: '2rem', color: '#073F35', marginTop: '4px', marginBottom: '16px' }}>
            Privacy Policy
          </h2>
          <div style={{ fontSize: '0.875rem', color: '#686F69', marginBottom: '28px' }}>
            Last Updated: 2 November 2026 • Compliant with Indian Digital Personal Data Protection (DPDP) Standards
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', lineHeight: 1.65, fontSize: '0.9375rem' }}>
            <section style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>1. Privacy By Design Architecture</h3>
              <p>
                OptiGuide is engineered to protect sensitive health and biometric information. Vision tests (Tumbling E, near vision reading, astigmatism, and colour plates) run entirely client-side inside your browser or device without transmitting raw responses unless you explicitly choose to save your screening summary.
              </p>
            </section>

            <section style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>2. Camera Access & Pupillary Distance (PD) Capture</h3>
              <p>
                Camera access is requested strictly when you initiate the Pupillary Distance estimation step or the Virtual Try-On studio. We never request camera permissions on landing pages or unprompted browsing. Video frames are processed in volatile client memory solely to calculate distance metrics. <strong>No selfie photographs or facial imagery are uploaded or stored on OptiGuide servers without prior explicit confirmation.</strong>
              </p>
            </section>

            <section style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>3. Information Collected for Kiosk Records</h3>
              <p>
                When an optical shopkeeper registers a walk-in citizen, only minimal operational contact data is recorded (name, phone number, age, and screening observations). Citizens have the right to request deletion or modification of their local kiosk records at any time.
              </p>
            </section>

            <section style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>4. Data Security & Storage</h3>
              <p>
                All network interactions with the FastAPI backend enforce HTTPS and TLS 1.3 encryption. Diagnostic logs strip personally identifiable details, and database connections operate with credential isolation.
              </p>
            </section>
          </div>
        </div>
      )}

      {/* ================= TERMS OF SERVICE ================= */}
      {page === 'terms' && (
        <div>
          <span style={{ fontSize: '0.8125rem', color: '#4F8278', fontWeight: 600, textTransform: 'uppercase' }}>
            Operational Agreement
          </span>
          <h2 style={{ fontSize: '2rem', color: '#073F35', marginTop: '4px', marginBottom: '16px' }}>
            Terms of Service
          </h2>
          <div style={{ fontSize: '0.875rem', color: '#686F69', marginBottom: '28px' }}>
            Effective Date: 2 November 2026
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', lineHeight: 1.65, fontSize: '0.9375rem' }}>
            <section style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>1. Scope of the Application</h3>
              <p>
                OptiGuide provides educational, preliminary vision screening tools and eyewear category guidance. By using this service, you acknowledge that OptiGuide is not a medical practice, medical clinic, or licensed healthcare provider.
              </p>
            </section>

            <section style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>2. Acceptable Use</h3>
              <p>
                Users and optical shopkeepers agree to use the screening protocols in good faith for community vision awareness. Shopkeepers must not market OptiGuide summaries as certified ophthalmic prescriptions or guarantees of refractive power.
              </p>
            </section>

            <section style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>3. Limitation of Liability</h3>
              <p>
                Screening accuracy depends on user honesty, display calibration, ambient illumination, and viewing distance. OptiGuide and its developers shall not be liable for decisions made or lenses ordered without confirmatory clinical testing by a registered eye-care practitioner.
              </p>
            </section>
          </div>
        </div>
      )}

      {/* ================= CLINICAL DISCLAIMER ================= */}
      {page === 'disclaimer' && (
        <div>
          <span style={{ fontSize: '0.8125rem', color: '#B77932', fontWeight: 600, textTransform: 'uppercase' }}>
            Regulatory Compliance Notice
          </span>
          <h2 style={{ fontSize: '2rem', color: '#073F35', marginTop: '4px', marginBottom: '16px' }}>
            Clinical & Medical Disclaimer
          </h2>

          <div
            style={{
              backgroundColor: '#F9F1E6',
              border: '2px solid #B77932',
              borderRadius: '8px',
              padding: '28px',
              marginBottom: '32px',
            }}
          >
            <div style={{ display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
              <ShieldAlertIcon size={28} color="#B77932" />
              <div>
                <h3 style={{ fontSize: '1.25rem', color: '#6E4515', marginBottom: '10px', fontFamily: 'var(--font-heading)' }}>
                  Important Medical Limitation
                </h3>
                <p style={{ fontSize: '1rem', color: '#202823', lineHeight: 1.6, marginBottom: '14px' }}>
                  OptiGuide is strictly a preliminary screening and eyewear assistance platform. It is not an ophthalmic diagnostic instrument and does not issue prescription orders for corrective lenses, contact lenses, medications, or eye surgeries.
                </p>
                <p style={{ fontSize: '0.9375rem', color: '#202823', lineHeight: 1.6 }}>
                  Computer-screen vision tests cannot detect glaucoma, diabetic retinopathy, macular degeneration, retinal detachments, or corneal pathologies. Comprehensive dilated examinations by an optometrist or ophthalmologist are necessary to evaluate ocular health.
                </p>
              </div>
            </div>
          </div>

          <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
            <h4 style={{ fontSize: '1.125rem', color: '#073F35', marginBottom: '8px' }}>
              Emergency Clinical Guidance
            </h4>
            <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: 1.6 }}>
              If you or a patient in your care experiences sudden loss of vision in one or both eyes, sudden double vision, intense ocular pain, light flashes, or visual halos, please proceed immediately to the nearest hospital emergency department or ophthalmic casualty center.
            </p>
          </div>
        </div>
      )}

      {/* ================= ABOUT PAGE ================= */}
      {page === 'about' && (
        <div>
          <span style={{ fontSize: '0.8125rem', color: '#4F8278', fontWeight: 600, textTransform: 'uppercase' }}>
            Our Mission & Background
          </span>
          <h2 style={{ fontSize: '2rem', color: '#073F35', marginTop: '4px', marginBottom: '16px' }}>
            About OptiGuide
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', lineHeight: 1.65, fontSize: '0.9375rem' }}>
            <section style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>
                Bridging the Rural Vision Accessibility Divide
              </h3>
              <p>
                In many semi-urban and rural areas across India, access to certified optometrists is limited to infrequent mobile camps or distant district headquarters. As a consequence, uncorrected refractive errors remain a leading cause of preventable visual impairment among school children, working adults, and senior citizens.
              </p>
              <p style={{ marginTop: '12px' }}>
                OptiGuide was developed to equip community optical shopkeepers and village health workers with standardized, self-guided screening software that runs directly in any modern browser on standard laptops, tablets, or phones.
              </p>
            </section>

            <section style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>
                Core Values: Respect, Precision, and Inclusivity
              </h3>
              <p>
                We believe in genuine accessibility: interfaces designed with regional language support (English, Hindi, Odia), high text contrast, voice-assisted instructions for non-literate community members, and strict non-diagnostic boundaries so patients are promptly guided to certified doctors when clinical need arises.
              </p>
            </section>
          </div>
        </div>
      )}

      {/* ================= HOW IT WORKS PAGE ================= */}
      {page === 'how-it-works' && (
        <div>
          <span style={{ fontSize: '0.8125rem', color: '#4F8278', fontWeight: 600, textTransform: 'uppercase' }}>
            Methodology & Protocol
          </span>
          <h2 style={{ fontSize: '2rem', color: '#073F35', marginTop: '4px', marginBottom: '16px' }}>
            How OptiGuide Vision Screening Works
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', fontSize: '0.9375rem', lineHeight: 1.6 }}>
            <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '6px' }}>
                1. Device Calibration & Viewing Geometry
              </h3>
              <p style={{ color: '#686F69' }}>
                Visual acuity optotypes must occupy precise angles of resolution on the retina (standard 5 arc-minutes for 20/20). OptiGuide guides the participant to position the screen at a calibrated 50 to 60 cm distance, ensuring that Snellen fractions correspond reliably to physical dimensions.
              </p>
            </div>

            <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '6px' }}>
                2. Tumbling E Optotype Protocol
              </h3>
              <p style={{ color: '#686F69' }}>
                Unlike Roman letter charts that depend on literacy, the Tumbling E test only asks the user to identify the direction of the letter's three prongs (Up, Down, Left, Right). This makes it universally applicable across multilingual rural populations.
              </p>
            </div>

            <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '6px' }}>
                3. Reference Card Pupillary Distance (PD)
              </h3>
              <p style={{ color: '#686F69' }}>
                By using any standard bank or ID card (standardized internationally at 85.60 mm width) held flat against the forehead, the software establishes an accurate pixel-to-millimeter ratio, enabling estimation of pupillary distance without manual calipers.
              </p>
            </div>

            <div style={{ textAlign: 'center', marginTop: '16px' }}>
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
                }}
              >
                Try the Complete Screening Protocol
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================= FOR SHOPS PAGE ================= */}
      {page === 'for-shops' && (
        <div>
          <span style={{ fontSize: '0.8125rem', color: '#4F8278', fontWeight: 600, textTransform: 'uppercase' }}>
            Optical Shopkeeper Partnership
          </span>
          <h2 style={{ fontSize: '2rem', color: '#073F35', marginTop: '4px', marginBottom: '16px' }}>
            Equip Your Optical Shop With OptiGuide Kiosk
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', fontSize: '0.9375rem', lineHeight: 1.6 }}>
            <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h3 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '8px' }}>
                Turn Any Computer or Tablet Into a Citizen Vision Station
              </h3>
              <p style={{ color: '#686F69' }}>
                OptiGuide enables local optical shopkeepers to conduct preliminary walk-in vision checks, record patient contact information, track spectacle orders, and directly refer suspicious ocular symptoms to affiliated eye hospitals.
              </p>
            </div>

            <div style={{ backgroundColor: '#F0ECE2', border: '1px solid #D7D2C4', borderRadius: '6px', padding: '24px' }}>
              <h4 style={{ fontSize: '1.125rem', color: '#073F35', marginBottom: '12px' }}>
                Key Kiosk Capabilities:
              </h4>
              <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px', color: '#202823' }}>
                <li>Register walk-in citizens with mobile phone and visit complaints.</li>
                <li>Conduct Tumbling E acuity, near reading, astigmatism, and color plates.</li>
                <li>Accurately measure pupillary distance using standard card calibration.</li>
                <li>Generate and print clean PDF summaries for hospital ophthalmologist referrals.</li>
                <li>Manage inventory and spectacle fabrication status directly.</li>
              </ul>
            </div>

            <div style={{ textAlign: 'center', marginTop: '12px' }}>
              <button
                onClick={() => onNavigate('shop-dashboard')}
                style={{
                  backgroundColor: '#073F35',
                  color: '#F7F4EC',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '14px 28px',
                  fontSize: '1rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Access Shopkeeper Kiosk Terminal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================= CONTACT PAGE ================= */}
      {page === 'contact' && (
        <div>
          <span style={{ fontSize: '0.8125rem', color: '#4F8278', fontWeight: 600, textTransform: 'uppercase' }}>
            Support & Community Assistance
          </span>
          <h2 style={{ fontSize: '2rem', color: '#073F35', marginTop: '4px', marginBottom: '16px' }}>
            Contact OptiGuide Support Desk
          </h2>

          {contactSubmitted ? (
            <div
              style={{
                backgroundColor: '#E8F3ED',
                border: '1px solid #28734F',
                borderRadius: '6px',
                padding: '28px',
                textAlign: 'center',
              }}
            >
              <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: '#28734F', color: '#F7F4EC', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
                <CheckIcon size={24} color="#F7F4EC" />
              </div>
              <h3 style={{ fontSize: '1.25rem', color: '#073F35', marginBottom: '6px' }}>
                Message Received
              </h3>
              <p style={{ fontSize: '0.9375rem', color: '#686F69' }}>
                Thank you, {contactName}. A technical or clinical support representative will contact you at {contactEmail} within one business day.
              </p>
            </div>
          ) : (
            <div style={{ backgroundColor: '#F7F4EC', border: '1px solid #D7D2C4', borderRadius: '8px', padding: '32px' }}>
              <form onSubmit={handleContactSubmit}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
                  <div>
                    <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                      Your Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={contactName}
                      onChange={(e) => setContactName(e.target.value)}
                      placeholder="e.g. Dr. Smita Mohanty"
                      style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                      Email Address *
                    </label>
                    <input
                      type="email"
                      required
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                      placeholder="e.g. smita@clinic.org"
                      style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.8125rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
                      Message or Inquiry *
                    </label>
                    <textarea
                      required
                      rows={4}
                      value={contactMessage}
                      onChange={(e) => setContactMessage(e.target.value)}
                      placeholder="Explain how we can help with your clinic or screening inquiries..."
                      style={{ width: '100%', padding: '10px', border: '1px solid #D7D2C4', borderRadius: '4px', backgroundColor: '#F0ECE2' }}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  style={{
                    backgroundColor: '#073F35',
                    color: '#F7F4EC',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '12px 24px',
                    fontSize: '0.9375rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Send Inquiry
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
