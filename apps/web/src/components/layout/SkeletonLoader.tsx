import React from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '20px',
  borderRadius = '4px',
  style,
}) => {
  return (
    <div
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: '#E4DFD3',
        opacity: 0.7,
        animation: 'skeleton-pulse 1.8s ease-in-out infinite',
        ...style,
      }}
    />
  );
};

export const CardSkeleton: React.FC = () => {
  return (
    <div
      style={{
        padding: '24px',
        backgroundColor: '#F0ECE2',
        border: '1px solid #D7D2C4',
        borderRadius: '6px',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
    >
      <Skeleton width="40%" height="24px" />
      <Skeleton width="100%" height="16px" />
      <Skeleton width="90%" height="16px" />
      <Skeleton width="60%" height="16px" />
      <div style={{ marginTop: '12px' }}>
        <Skeleton width="120px" height="38px" borderRadius="6px" />
      </div>
    </div>
  );
};

