import React from 'react';
import { ShieldAlertIcon } from '../icons';
import { useLanguage } from '../../localization/useLanguage';

interface ClinicalDisclaimerBannerProps {
  onLearnMore?: () => void;
  compact?: boolean;
}

export const ClinicalDisclaimerBanner: React.FC<ClinicalDisclaimerBannerProps> = ({
  onLearnMore,
  compact = false,
}) => {
  const { t } = useLanguage();

  return (
    <div
      role="alert"
      style={{
        backgroundColor: '#F9F1E6',
        border: '1px solid #D7D2C4',
        borderRadius: '6px',
        padding: compact ? '10px 16px' : '14px 20px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '14px',
        color: '#202823',
      }}
    >
      <div style={{ color: '#B77932', marginTop: '2px', flexShrink: 0 }}>
        <ShieldAlertIcon size={20} color="#B77932" />
      </div>
      <div style={{ flex: 1, fontSize: compact ? '0.875rem' : '0.9375rem', lineHeight: '1.45' }}>
        <strong style={{ display: 'block', color: '#6E4515', marginBottom: '2px', fontFamily: 'var(--font-heading)' }}>
          {t.clinicalNotice}
        </strong>
        <span>{t.clinicalDisclaimerText}</span>
        {onLearnMore && (
          <button
            onClick={onLearnMore}
            style={{
              display: 'inline-block',
              marginLeft: '8px',
              background: 'none',
              border: 'none',
              color: '#073F35',
              fontWeight: 600,
              textDecoration: 'underline',
              cursor: 'pointer',
              fontSize: 'inherit',
              padding: 0,
            }}
          >
            Review Clinical Disclaimer
          </button>
        )}
      </div>
    </div>
  );
};

