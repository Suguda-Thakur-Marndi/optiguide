import React, { useState } from 'react';
import { LogoIcon, UserIcon, EyeIcon } from '../icons';
import { useLanguage } from '../../localization/useLanguage';
import { LanguageCode } from '../../localization/translations';
import { UserProfile } from '@optiguide/shared';

interface NavbarProps {
  currentRoute: string;
  onNavigate: (route: string) => void;
  currentUser: UserProfile | null;
  onSelectRole: (role: any) => void;
  backendOnline: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentRoute,
  onNavigate,
  currentUser,
  onSelectRole,
  backendOnline,
}) => {
  const { language, setLanguage, t } = useLanguage();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { id: 'home', label: t.nav.home },
    { id: 'how-it-works', label: t.nav.howItWorks },
    { id: 'screening', label: t.nav.screening },
    { id: 'eyewear', label: 'Eyewear' },
    { id: 'for-shops', label: t.nav.forShops },
    { id: 'about', label: t.nav.about },
  ];

  const handleNavClick = (id: string) => {
    onNavigate(id);
    setMobileMenuOpen(false);
  };

  return (
    <header
      style={{
        backgroundColor: '#F7F4EC',
        borderBottom: '1px solid #D7D2C4',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Top micro-bar: Health, rural language indicator and role switcher */}
      <div
        style={{
          borderBottom: '1px solid #E4DFD3',
          padding: '6px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.8125rem',
          color: '#686F69',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: backendOnline ? '#28734F' : '#B77932',
                display: 'inline-block',
              }}
            />
            {backendOnline ? 'FastAPI Backend Connected' : 'Local Standalone Mode (Port 8000 Offline)'}
          </span>
          <span style={{ color: '#D7D2C4' }}>|</span>
          <span>Community Eye Health Initiative</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Active Role Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <UserIcon size={14} color="#073F35" />
            <span>Role:</span>
            <select
              value={currentUser?.role || 'guest'}
              onChange={(e) => onSelectRole(e.target.value)}
              aria-label="Select User Role"
              style={{
                backgroundColor: '#E9E5DA',
                border: '1px solid #D7D2C4',
                borderRadius: '4px',
                padding: '2px 8px',
                fontSize: '0.8125rem',
                color: '#202823',
                cursor: 'pointer',
              }}
            >
              <option value="guest">Guest (No Registration)</option>
              <option value="individual">Individual (Patient)</option>
              <option value="shopkeeper">Shopkeeper (Drishti Kiosk)</option>
              <option value="admin">Administrator</option>
              <option value="optometrist">Eye Care Professional</option>
            </select>
          </div>

          <span style={{ color: '#D7D2C4' }}>|</span>

          {/* Language Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontWeight: 500 }}>Language:</span>
            {(['en', 'hi', 'or'] as LanguageCode[]).map((code) => {
              const labels: Record<LanguageCode, string> = { en: 'EN', hi: 'हिन्दी', or: 'ଓଡ଼ିଆ' };
              const active = language === code;
              return (
                <button
                  key={code}
                  onClick={() => setLanguage(code)}
                  style={{
                    background: active ? '#073F35' : 'transparent',
                    color: active ? '#F7F4EC' : '#202823',
                    border: active ? '1px solid #073F35' : '1px solid #D7D2C4',
                    borderRadius: '4px',
                    padding: '2px 8px',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    fontWeight: active ? 600 : 400,
                  }}
                >
                  {labels[code]}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main navigation row */}
      <div
        style={{
          maxWidth: '1280px',
          margin: '0 auto',
          padding: '14px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand Logo */}
        <button
          onClick={() => handleNavClick('home')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            textAlign: 'left',
            padding: 0,
          }}
        >
          <LogoIcon size={34} color="#073F35" />
          <div>
            <div
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.375rem',
                fontWeight: 700,
                color: '#073F35',
                letterSpacing: '-0.01em',
                lineHeight: 1.1,
              }}
            >
              OptiGuide
            </div>
            <div
              style={{
                fontSize: '0.75rem',
                color: '#686F69',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              Vision Screening & Eyewear Guidance
            </div>
          </div>
        </button>

        {/* Desktop Navigation Links */}
        <nav
          style={{
            display: 'none',
            gap: '24px',
            alignItems: 'center',
          }}
          className="desktop-nav"
        >
          {navLinks.map((link) => {
            const active = currentRoute === link.id;
            return (
              <button
                key={link.id}
                onClick={() => handleNavClick(link.id)}
                style={{
                  background: 'none',
                  border: 'none',
                  borderBottom: active ? '2px solid #073F35' : '2px solid transparent',
                  padding: '8px 2px',
                  fontFamily: 'var(--font-body)',
                  fontSize: '0.9375rem',
                  fontWeight: active ? 600 : 400,
                  color: active ? '#073F35' : '#202823',
                  cursor: 'pointer',
                }}
              >
                {link.label}
              </button>
            );
          })}

          {currentUser?.role === 'shopkeeper' && (
            <button
              onClick={() => handleNavClick('shop-dashboard')}
              style={{
                background: currentRoute === 'shop-dashboard' ? '#073F35' : '#E9E5DA',
                color: currentRoute === 'shop-dashboard' ? '#F7F4EC' : '#073F35',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Shop Dashboard
            </button>
          )}

          {currentUser?.role === 'admin' && (
            <button
              onClick={() => handleNavClick('admin-dashboard')}
              style={{
                background: currentRoute === 'admin-dashboard' ? '#073F35' : '#E9E5DA',
                color: currentRoute === 'admin-dashboard' ? '#F7F4EC' : '#073F35',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Admin Dashboard
            </button>
          )}

          {/* Start Screening CTA */}
          <button
            onClick={() => handleNavClick('screening')}
            style={{
              backgroundColor: '#073F35',
              color: '#F7F4EC',
              border: 'none',
              borderRadius: '6px',
              padding: '10px 20px',
              fontFamily: 'var(--font-body)',
              fontSize: '0.9375rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <EyeIcon size={18} color="#F7F4EC" />
            {t.nav.startScreening}
          </button>
        </nav>

        {/* Mobile menu hamburger toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle Navigation Menu"
          style={{
            display: 'block',
            background: '#E9E5DA',
            border: '1px solid #D7D2C4',
            borderRadius: '6px',
            padding: '8px 12px',
            fontSize: '1rem',
            cursor: 'pointer',
          }}
          className="mobile-toggle"
        >
          {mobileMenuOpen ? '✕' : '☰'}
        </button>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div
          style={{
            borderTop: '1px solid #D7D2C4',
            backgroundColor: '#F7F4EC',
            padding: '16px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          {navLinks.map((link) => (
            <button
              key={link.id}
              onClick={() => handleNavClick(link.id)}
              style={{
                textAlign: 'left',
                background: currentRoute === link.id ? '#E9E5DA' : 'transparent',
                border: 'none',
                padding: '10px 12px',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: currentRoute === link.id ? 600 : 400,
                color: '#073F35',
                cursor: 'pointer',
              }}
            >
              {link.label}
            </button>
          ))}

          {currentUser?.role === 'shopkeeper' && (
            <button
              onClick={() => handleNavClick('shop-dashboard')}
              style={{
                textAlign: 'left',
                background: '#E9E5DA',
                border: '1px solid #D7D2C4',
                padding: '10px 12px',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: 600,
                color: '#073F35',
                cursor: 'pointer',
              }}
            >
              Shop Dashboard
            </button>
          )}

          {currentUser?.role === 'admin' && (
            <button
              onClick={() => handleNavClick('admin-dashboard')}
              style={{
                textAlign: 'left',
                background: '#E9E5DA',
                border: '1px solid #D7D2C4',
                padding: '10px 12px',
                borderRadius: '6px',
                fontSize: '1rem',
                fontWeight: 600,
                color: '#073F35',
                cursor: 'pointer',
              }}
            >
              Admin Dashboard
            </button>
          )}

          <button
            onClick={() => handleNavClick('screening')}
            style={{
              backgroundColor: '#073F35',
              color: '#F7F4EC',
              border: 'none',
              borderRadius: '6px',
              padding: '12px',
              fontWeight: 600,
              fontSize: '1rem',
              cursor: 'pointer',
              marginTop: '8px',
            }}
          >
            {t.nav.startScreening}
          </button>
        </div>
      )}

      {/* Responsive media query styling */}
      <style>{`
        @media (min-width: 860px) {
          .desktop-nav {
            display: flex !important;
          }
          .mobile-toggle {
            display: none !important;
          }
        }
      `}</style>
    </header>
  );
};

