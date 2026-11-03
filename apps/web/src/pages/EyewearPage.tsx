import React, { useState, useRef, useEffect } from 'react';
import { CameraIcon, GlassesIcon, SearchIcon } from '../components/icons';
import { getStoredProducts } from '../services/storage';
import { EyewearProduct, ScreeningSession } from '@optiguide/shared';

interface EyewearPageProps {
  session?: ScreeningSession | null;
  onSelectProduct?: (product: EyewearProduct) => void;
}

export const EyewearPage: React.FC<EyewearPageProps> = ({ session, onSelectProduct }) => {
  const [products] = useState<EyewearProduct[]>(getStoredProducts());
  const [selectedShape, setSelectedShape] = useState<string>('all');
  const [selectedLens, setSelectedLens] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProduct, setSelectedProduct] = useState<EyewearProduct>(products[0]);

  // Virtual Try-on state
  const [tryOnActive, setTryOnActive] = useState(false);
  const [frameScale, setFrameScale] = useState(1.0);
  const [frameOffsetY, setFrameOffsetY] = useState(0);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setTryOnActive(true);
      }
    } catch {
      alert('Camera access could not be initialized. Please check browser permissions.');
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    setTryOnActive(false);
  };

  // Filter products
  const filteredProducts = products.filter((p) => {
    const matchesShape = selectedShape === 'all' || p.frameShape === selectedShape;
    const matchesLens = selectedLens === 'all' || p.lensType === selectedLens;
    const matchesSearch =
      p.modelName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.brand.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesShape && matchesLens && matchesSearch;
  });

  return (
    <div style={{ maxWidth: '1280px', margin: '32px auto', padding: '0 24px', color: '#202823' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <span style={{ fontSize: '0.8125rem', color: '#4F8278', fontWeight: 600, textTransform: 'uppercase' }}>
          Eyewear & Lens Guidance
        </span>
        <h2 style={{ fontSize: '2rem', color: '#073F35', marginTop: '2px', marginBottom: '8px' }}>
          Prescription Compatible Frames & Virtual Try-On
        </h2>
        <p style={{ fontSize: '1rem', color: '#686F69', maxWidth: '720px', lineHeight: 1.55 }}>
          Curated eyewear designs selected for ergonomic comfort, rural durability, and compatibility with your preliminary screening parameters.
        </p>

        {session && session.results?.pdEstimation && (
          <div
            style={{
              marginTop: '16px',
              padding: '12px 18px',
              backgroundColor: '#EBF3F1',
              border: '1px solid #A5C9C1',
              borderRadius: '6px',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '0.875rem',
            }}
          >
            <GlassesIcon size={20} color="#073F35" />
            <span>
              Configured for Participant PD:{' '}
              <strong>{session.results?.pdEstimation?.pupillaryDistanceMm.toFixed(1)} mm</strong>
            </span>
          </div>
        )}
      </div>

      {/* Virtual Try-On Stage */}
      <div
        style={{
          backgroundColor: '#F0ECE2',
          border: '1px solid #D7D2C4',
          borderRadius: '8px',
          padding: '24px',
          marginBottom: '40px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', color: '#073F35', fontFamily: 'var(--font-heading)' }}>
              Interactive Virtual Try-On Studio
            </h3>
            <span style={{ fontSize: '0.8125rem', color: '#686F69' }}>
              Notice: Virtual try-on is an appearance and aesthetic preview, not a substitute for clinical dispensing fitting.
            </span>
          </div>

          {!tryOnActive ? (
            <button
              onClick={startCamera}
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
              <CameraIcon size={18} color="#F7F4EC" />
              Enable Live Try-On Camera
            </button>
          ) : (
            <button
              onClick={stopCamera}
              style={{
                backgroundColor: '#E9E5DA',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '8px 16px',
                fontSize: '0.875rem',
                color: '#A9473E',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              Turn Off Camera
            </button>
          )}
        </div>

        {/* Viewport & Overlay */}
        <div
          style={{
            height: '340px',
            backgroundColor: '#F7F4EC',
            border: '1px solid #D7D2C4',
            borderRadius: '6px',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
          }}
        >
          {tryOnActive ? (
            <>
              <video
                ref={videoRef}
                playsInline
                muted
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  transform: 'scaleX(-1)', // Mirror
                }}
              />

              {/* Virtual Frame SVG Overlay on Face */}
              <div
                style={{
                  position: 'absolute',
                  top: `calc(42% + ${frameOffsetY}px)`,
                  left: '50%',
                  transform: `translate(-50%, -50%) scale(${frameScale})`,
                  pointerEvents: 'none',
                  transition: 'none',
                }}
              >
                <svg width="220" height="90" viewBox="0 0 220 90">
                  {/* Left Lens Frame */}
                  <rect
                    x="10"
                    y="15"
                    width="85"
                    height="60"
                    rx={selectedProduct.frameShape === 'round' ? '30' : '8'}
                    fill="none"
                    stroke="#092D28"
                    strokeWidth="4"
                  />
                  {/* Right Lens Frame */}
                  <rect
                    x="125"
                    y="15"
                    width="85"
                    height="60"
                    rx={selectedProduct.frameShape === 'round' ? '30' : '8'}
                    fill="none"
                    stroke="#092D28"
                    strokeWidth="4"
                  />
                  {/* Nose Bridge */}
                  <path d="M95 38 Q110 30 125 38" fill="none" stroke="#092D28" strokeWidth="4" />
                  {/* Left Temple Joint */}
                  <line x1="10" y1="25" x2="0" y2="22" stroke="#092D28" strokeWidth="3" />
                  {/* Right Temple Joint */}
                  <line x1="210" y1="25" x2="220" y2="22" stroke="#092D28" strokeWidth="3" />
                </svg>
              </div>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  backgroundColor: '#E9E5DA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 12px',
                  color: '#073F35',
                }}
              >
                <GlassesIcon size={32} color="#073F35" />
              </div>
              <div style={{ fontSize: '1.125rem', fontWeight: 600, color: '#073F35', marginBottom: '4px' }}>
                Previewing: {selectedProduct.modelName}
              </div>
              <p style={{ fontSize: '0.875rem', color: '#686F69', maxWidth: '420px', margin: '0 auto 16px' }}>
                Activate your camera above to see this frame superimposed in real time over your face.
              </p>
            </div>
          )}
        </div>

        {tryOnActive && (
          <div
            style={{
              marginTop: '16px',
              display: 'flex',
              gap: '24px',
              alignItems: 'center',
              backgroundColor: '#F7F4EC',
              padding: '12px 18px',
              borderRadius: '6px',
              border: '1px solid #D7D2C4',
              flexWrap: 'wrap',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.875rem' }}>
              <span>Frame Size Scale:</span>
              <input
                type="range"
                min="0.7"
                max="1.4"
                step="0.05"
                value={frameScale}
                onChange={(e) => setFrameScale(parseFloat(e.target.value))}
                style={{ accentColor: '#073F35' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.875rem' }}>
              <span>Vertical Adjustment:</span>
              <input
                type="range"
                min="-40"
                max="40"
                step="2"
                value={frameOffsetY}
                onChange={(e) => setFrameOffsetY(parseInt(e.target.value))}
                style={{ accentColor: '#073F35' }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Filter & Search Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '28px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
              Frame Shape:
            </span>
            <select
              value={selectedShape}
              onChange={(e) => setSelectedShape(e.target.value)}
              style={{
                backgroundColor: '#F7F4EC',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '8px 12px',
                fontSize: '0.875rem',
                color: '#202823',
                cursor: 'pointer',
              }}
            >
              <option value="all">All Frame Shapes</option>
              <option value="rectangular">Rectangular</option>
              <option value="round">Round</option>
              <option value="square">Square</option>
              <option value="aviator">Aviator</option>
              <option value="oval">Oval</option>
            </select>
          </div>

          <div>
            <span style={{ fontSize: '0.75rem', color: '#686F69', display: 'block', marginBottom: '4px' }}>
              Lens Recommendation:
            </span>
            <select
              value={selectedLens}
              onChange={(e) => setSelectedLens(e.target.value)}
              style={{
                backgroundColor: '#F7F4EC',
                border: '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '8px 12px',
                fontSize: '0.875rem',
                color: '#202823',
                cursor: 'pointer',
              }}
            >
              <option value="all">All Lens Types</option>
              <option value="single_vision">Single Vision</option>
              <option value="progressive">Progressive Support</option>
              <option value="blue_cut">Blue Cut / Screen Protective</option>
              <option value="bifocal">Bifocal</option>
            </select>
          </div>
        </div>

        <div style={{ position: 'relative', minWidth: '240px' }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search frames by name..."
            style={{
              width: '100%',
              backgroundColor: '#F7F4EC',
              border: '1px solid #D7D2C4',
              borderRadius: '6px',
              padding: '8px 12px 8px 36px',
              fontSize: '0.875rem',
              color: '#202823',
            }}
          />
          <div style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#686F69' }}>
            <SearchIcon size={16} />
          </div>
        </div>
      </div>

      {/* Catalogue Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '24px',
        }}
      >
        {filteredProducts.map((p) => {
          const isSelected = selectedProduct.id === p.id;
          return (
            <div
              key={p.id}
              style={{
                backgroundColor: '#F7F4EC',
                border: isSelected ? '2px solid #073F35' : '1px solid #D7D2C4',
                borderRadius: '6px',
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: '#4F8278',
                      textTransform: 'uppercase',
                    }}
                  >
                    {p.brand}
                  </span>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      backgroundColor: p.inStock ? '#E8F3ED' : '#F8ECEB',
                      color: p.inStock ? '#28734F' : '#A9473E',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontWeight: 600,
                    }}
                  >
                    {p.inStock ? `${p.stockCount} in stock` : 'Out of stock'}
                  </span>
                </div>

                <h4 style={{ fontSize: '1.1875rem', color: '#073F35', marginBottom: '6px' }}>
                  {p.modelName}
                </h4>

                <p style={{ fontSize: '0.875rem', color: '#686F69', lineHeight: 1.5, marginBottom: '14px' }}>
                  {p.description}
                </p>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
                  <span style={{ fontSize: '0.75rem', backgroundColor: '#E9E5DA', padding: '3px 8px', borderRadius: '4px', color: '#202823' }}>
                    Shape: {p.frameShape}
                  </span>
                  <span style={{ fontSize: '0.75rem', backgroundColor: '#E9E5DA', padding: '3px 8px', borderRadius: '4px', color: '#202823' }}>
                    Material: {p.material}
                  </span>
                  <span style={{ fontSize: '0.75rem', backgroundColor: '#E9E5DA', padding: '3px 8px', borderRadius: '4px', color: '#202823' }}>
                    Lens: {p.lensType.replace('_', ' ')}
                  </span>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderTop: '1px solid #D7D2C4', paddingTop: '12px' }}>
                  <span style={{ fontSize: '0.8125rem', color: '#686F69' }}>Standard Kiosk Price:</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#073F35' }}>
                    ₹{p.priceINR.toLocaleString('en-IN')}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => {
                      setSelectedProduct(p);
                      window.scrollTo({ top: 180, behavior: 'smooth' });
                    }}
                    style={{
                      flex: 1,
                      backgroundColor: isSelected ? '#073F35' : '#E9E5DA',
                      color: isSelected ? '#F7F4EC' : '#073F35',
                      border: '1px solid #D7D2C4',
                      borderRadius: '6px',
                      padding: '8px',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {isSelected ? 'Active in Try-On' : 'Try-On This Frame'}
                  </button>

                  {onSelectProduct && (
                    <button
                      onClick={() => onSelectProduct(p)}
                      style={{
                        backgroundColor: '#073F35',
                        color: '#F7F4EC',
                        border: 'none',
                        borderRadius: '6px',
                        padding: '8px 14px',
                        fontSize: '0.875rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      Select
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
