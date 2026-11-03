import React from 'react';
import { LogoIcon } from '../icons';

interface FooterProps {
  onNavigate: (route: string) => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  return (
    <footer
      style={{
        backgroundColor: '#E9E5DA',
        borderTop: '1px solid #D7D2C4',
        padding: '48px 24px 32px',
        color: '#202823',
        marginTop: '64px',
      }}
    >
      <div
        style={{
          maxWidth: '1280px',
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '36px',
          marginBottom: '40px',
        }}
      >
        {/* Brand Column */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
            <LogoIcon size={30} color="#073F35" />
            <span
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.25rem',
                fontWeight: 700,
                color: '#073F35',
              }}
            >
              OptiGuide
            </span>
          </div>
          <p style={{ fontSize: '0.9375rem', color: '#686F69', lineHeight: '1.6', marginBottom: '16px' }}>
            Empowering accessible vision screening and eyewear guidance for rural and urban community health clinics.
          </p>
          <div
            style={{
              padding: '10px 14px',
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              fontSize: '0.8125rem',
              color: '#073F35',
            }}
          >
            Built for multi-device accessibility: Smartphones, tablets, and desktop workstations.
          </div>
        </div>

        {/* Navigation Column */}
        <div>
          <h4
            style={{
              fontSize: '1rem',
              fontWeight: 600,
              color: '#092D28',
              marginBottom: '14px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Navigation
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <li>
              <button
                onClick={() => onNavigate('home')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                Home
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate('how-it-works')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                How It Works
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate('screening')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                Vision Screening Flow
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate('eyewear')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                Eyewear Catalogue & Try-On
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate('for-shops')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                Optical Shop Partner Program
              </button>
            </li>
          </ul>
        </div>

        {/* Legal & Compliance Column */}
        <div>
          <h4
            style={{
              fontSize: '1rem',
              fontWeight: 600,
              color: '#092D28',
              marginBottom: '14px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Compliance & Legal
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <li>
              <button
                onClick={() => onNavigate('privacy-policy')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                Privacy Policy (Data & Camera)
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate('terms-of-service')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                Terms of Service
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate('disclaimer')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                Clinical Medical Disclaimer
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate('about')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                About Our Rural Mission
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate('contact')}
                style={{ background: 'none', border: 'none', color: '#202823', cursor: 'pointer', fontSize: '0.9375rem', padding: 0 }}
              >
                Contact & Support Desk
              </button>
            </li>
          </ul>
        </div>

        {/* Clinical Advisory Notice */}
        <div>
          <h4
            style={{
              fontSize: '1rem',
              fontWeight: 600,
              color: '#092D28',
              marginBottom: '14px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Clinical Advisory
          </h4>
          <p style={{ fontSize: '0.8125rem', color: '#686F69', lineHeight: '1.6' }}>
            OptiGuide is strictly a preliminary screening aid. It does not replace comprehensive ocular health examinations by licensed optometrists or ophthalmologists.
          </p>
          <div style={{ marginTop: '12px', fontSize: '0.8125rem', color: '#073F35', fontWeight: 600 }}>
            Emergency: If experiencing sudden loss of sight or severe eye trauma, seek immediate emergency care.
          </div>
        </div>
      </div>

      {/* Bottom Copyright */}
      <div
        style={{
          maxWidth: '1280px',
          margin: '0 auto',
          paddingTop: '24px',
          borderTop: '1px solid #D7D2C4',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.8125rem',
          color: '#686F69',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          (C) 2026 OptiGuide Initiative. All rights reserved.
        </div>
        <div>
          Editorial design standard: Forest Green, Warm Ivory, and Authentic Vision Care.
        </div>
      </div>
    </footer>
  );
};

