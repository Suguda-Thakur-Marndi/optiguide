import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  CameraIcon,
  GlassesIcon,
  HeartIcon,
  SwitchCameraIcon,
  SlidersIcon,
  SparklesIcon,
  RefreshIcon,
  DownloadIcon,
  CheckIcon,
  AlertIcon,
  ShoppingBagIcon,
  EyeIcon,
} from '../components/icons';
import { apiClient } from '../services/apiClient';
import { faceTracker } from '../services/faceTracker';
import { glassesRenderer } from '../services/glassesRenderer';
import type {
  FrameTryOnAsset,
  FaceTrackingState,
  TryOnSession,
  FrameCategory,
} from '../types/tryOn';

interface VirtualTryOnPageProps {
  onNavigate?: (route: string) => void;
  onSelectProductForCheckout?: (frame: FrameTryOnAsset) => void;
}

// Built-in static fallback catalogue ensuring immediate offline rendering
const FALLBACK_FRAMES: FrameTryOnAsset[] = [
  {
    frame_id: 'd1000000-0000-0000-0000-000000000001',
    sku: 'OG-REC-01',
    name: 'OptiGuide Classic Horizon',
    brand_name: 'OptiGuide Classic',
    frame_type: 'full-rim',
    frame_material: 'acetate',
    frame_shape: 'rectangular',
    gender_target: 'unisex',
    base_price_inr: 1299,
    is_active: true,
    in_stock: true,
    try_on_asset_url: '/assets/frames/frame-rectangular.svg',
    try_on_asset_type: '2d_svg',
    available_colors: [
      { hex_code: '#111827', name: 'Onyx Black' },
      { hex_code: '#92400e', name: 'Tortoise Brown' },
      { hex_code: '#1e3a8a', name: 'Midnight Navy' },
    ],
    left_lens_center_x: 0.2875,
    left_lens_center_y: 0.5,
    right_lens_center_x: 0.7125,
    right_lens_center_y: 0.5,
    bridge_center_x: 0.5,
    bridge_center_y: 0.48,
    asset_scale: 1.0,
    asset_rotation_offset: 0.0,
    asset_version: '1.0.0',
    frame_width_mm: 138,
    bridge_width_mm: 18,
    temple_length_mm: 142,
    lens_width_mm: 53,
    lens_height_mm: 36,
    is_try_on_available: true,
  },
  {
    frame_id: 'd1000000-0000-0000-0000-000000000002',
    sku: 'OG-RND-02',
    name: 'OptiGuide Heritage Circle',
    brand_name: 'Heritage Eyewear',
    frame_type: 'full-rim',
    frame_material: 'monel',
    frame_shape: 'round',
    gender_target: 'unisex',
    base_price_inr: 1499,
    is_active: true,
    in_stock: true,
    try_on_asset_url: '/assets/frames/frame-round.svg',
    try_on_asset_type: '2d_svg',
    available_colors: [
      { hex_code: '#d97706', name: 'Vintage Gold' },
      { hex_code: '#111827', name: 'Onyx Black' },
      { hex_code: '#64748b', name: 'Pewter Silver' },
    ],
    left_lens_center_x: 0.2875,
    left_lens_center_y: 0.5,
    right_lens_center_x: 0.7125,
    right_lens_center_y: 0.5,
    bridge_center_x: 0.5,
    bridge_center_y: 0.46,
    asset_scale: 1.0,
    asset_rotation_offset: 0.0,
    asset_version: '1.0.0',
    frame_width_mm: 134,
    bridge_width_mm: 20,
    temple_length_mm: 140,
    lens_width_mm: 49,
    lens_height_mm: 45,
    is_try_on_available: true,
  },
  {
    frame_id: 'd1000000-0000-0000-0000-000000000003',
    sku: 'OG-AVI-03',
    name: 'OptiGuide SkyPilot Aviator',
    brand_name: 'AeroLite',
    frame_type: 'full-rim',
    frame_material: 'titanium',
    frame_shape: 'aviator',
    gender_target: 'unisex',
    base_price_inr: 1799,
    is_active: true,
    in_stock: true,
    try_on_asset_url: '/assets/frames/frame-aviator.svg',
    try_on_asset_type: '2d_svg',
    available_colors: [
      { hex_code: '#eab308', name: 'Champagne Gold' },
      { hex_code: '#64748b', name: 'Gunmetal Grey' },
      { hex_code: '#111827', name: 'Matte Black' },
    ],
    left_lens_center_x: 0.2875,
    left_lens_center_y: 0.52,
    right_lens_center_x: 0.7125,
    right_lens_center_y: 0.52,
    bridge_center_x: 0.5,
    bridge_center_y: 0.42,
    asset_scale: 1.0,
    asset_rotation_offset: 0.0,
    asset_version: '1.0.0',
    frame_width_mm: 140,
    bridge_width_mm: 16,
    temple_length_mm: 145,
    lens_width_mm: 58,
    lens_height_mm: 48,
    is_try_on_available: true,
  },
  {
    frame_id: 'd1000000-0000-0000-0000-000000000004',
    sku: 'OG-SQR-04',
    name: 'OptiGuide Architect Square',
    brand_name: 'VisionPro',
    frame_type: 'full-rim',
    frame_material: 'tr90',
    frame_shape: 'square',
    gender_target: 'men',
    base_price_inr: 1199,
    is_active: true,
    in_stock: true,
    try_on_asset_url: '/assets/frames/frame-square.svg',
    try_on_asset_type: '2d_svg',
    available_colors: [
      { hex_code: '#111827', name: 'Jet Black' },
      { hex_code: '#334155', name: 'Charcoal' },
      { hex_code: '#1e3a8a', name: 'Navy Blue' },
    ],
    left_lens_center_x: 0.2875,
    left_lens_center_y: 0.5,
    right_lens_center_x: 0.7125,
    right_lens_center_y: 0.5,
    bridge_center_x: 0.5,
    bridge_center_y: 0.48,
    asset_scale: 1.0,
    asset_rotation_offset: 0.0,
    asset_version: '1.0.0',
    frame_width_mm: 139,
    bridge_width_mm: 17,
    temple_length_mm: 142,
    lens_width_mm: 52,
    lens_height_mm: 40,
    is_try_on_available: true,
  },
  {
    frame_id: 'd1000000-0000-0000-0000-000000000005',
    sku: 'OG-CAT-05',
    name: 'OptiGuide Diva Winged Cat-Eye',
    brand_name: 'LuxeOptics',
    frame_type: 'full-rim',
    frame_material: 'acetate',
    frame_shape: 'cat-eye',
    gender_target: 'women',
    base_price_inr: 1599,
    is_active: true,
    in_stock: true,
    try_on_asset_url: '/assets/frames/frame-cat-eye.svg',
    try_on_asset_type: '2d_svg',
    available_colors: [
      { hex_code: '#831843', name: 'Wine Plum' },
      { hex_code: '#111827', name: 'Gloss Black' },
      { hex_code: '#92400e', name: 'Havana Tortoise' },
    ],
    left_lens_center_x: 0.2875,
    left_lens_center_y: 0.5,
    right_lens_center_x: 0.7125,
    right_lens_center_y: 0.5,
    bridge_center_x: 0.5,
    bridge_center_y: 0.46,
    asset_scale: 1.0,
    asset_rotation_offset: 0.0,
    asset_version: '1.0.0',
    frame_width_mm: 136,
    bridge_width_mm: 17,
    temple_length_mm: 140,
    lens_width_mm: 51,
    lens_height_mm: 42,
    is_try_on_available: true,
  },
  {
    frame_id: 'd1000000-0000-0000-0000-000000000006',
    sku: 'OG-WAY-06',
    name: 'OptiGuide Coastal Wayfarer',
    brand_name: 'Heritage Eyewear',
    frame_type: 'full-rim',
    frame_material: 'acetate',
    frame_shape: 'wayfarer',
    gender_target: 'unisex',
    base_price_inr: 1399,
    is_active: true,
    in_stock: true,
    try_on_asset_url: '/assets/frames/frame-wayfarer.svg',
    try_on_asset_type: '2d_svg',
    available_colors: [
      { hex_code: '#111827', name: 'Matte Black' },
      { hex_code: '#92400e', name: 'Dark Amber' },
    ],
    left_lens_center_x: 0.2875,
    left_lens_center_y: 0.5,
    right_lens_center_x: 0.7125,
    right_lens_center_y: 0.5,
    bridge_center_x: 0.5,
    bridge_center_y: 0.48,
    asset_scale: 1.0,
    asset_rotation_offset: 0.0,
    asset_version: '1.0.0',
    frame_width_mm: 142,
    bridge_width_mm: 19,
    temple_length_mm: 145,
    lens_width_mm: 54,
    lens_height_mm: 43,
    is_try_on_available: true,
  },
  {
    frame_id: 'd1000000-0000-0000-0000-000000000007',
    sku: 'OG-SEMI-07',
    name: 'OptiGuide Executive Club Browline',
    brand_name: 'VisionPro',
    frame_type: 'semi-rimless',
    frame_material: 'metal',
    frame_shape: 'semi-rimless',
    gender_target: 'unisex',
    base_price_inr: 1699,
    is_active: true,
    in_stock: true,
    try_on_asset_url: '/assets/frames/frame-semi-rimless.svg',
    try_on_asset_type: '2d_svg',
    available_colors: [
      { hex_code: '#111827', name: 'Black & Gold' },
      { hex_code: '#92400e', name: 'Tortoise & Silver' },
    ],
    left_lens_center_x: 0.2875,
    left_lens_center_y: 0.48,
    right_lens_center_x: 0.7125,
    right_lens_center_y: 0.48,
    bridge_center_x: 0.5,
    bridge_center_y: 0.45,
    asset_scale: 1.0,
    asset_rotation_offset: 0.0,
    asset_version: '1.0.0',
    frame_width_mm: 137,
    bridge_width_mm: 18,
    temple_length_mm: 140,
    lens_width_mm: 50,
    lens_height_mm: 39,
    is_try_on_available: true,
  },
  {
    frame_id: 'd1000000-0000-0000-0000-000000000008',
    sku: 'OG-RIM-08',
    name: 'OptiGuide FeatherLight Silhouette',
    brand_name: 'AeroLite',
    frame_type: 'rimless',
    frame_material: 'titanium',
    frame_shape: 'rimless',
    gender_target: 'unisex',
    base_price_inr: 2199,
    is_active: true,
    in_stock: true,
    try_on_asset_url: '/assets/frames/frame-rimless.svg',
    try_on_asset_type: '2d_svg',
    available_colors: [
      { hex_code: '#64748b', name: 'Titanium Silver' },
      { hex_code: '#eab308', name: 'Rose Gold' },
    ],
    left_lens_center_x: 0.2875,
    left_lens_center_y: 0.5,
    right_lens_center_x: 0.7125,
    right_lens_center_y: 0.5,
    bridge_center_x: 0.5,
    bridge_center_y: 0.48,
    asset_scale: 1.0,
    asset_rotation_offset: 0.0,
    asset_version: '1.0.0',
    frame_width_mm: 135,
    bridge_width_mm: 19,
    temple_length_mm: 142,
    lens_width_mm: 52,
    lens_height_mm: 35,
    is_try_on_available: true,
  },
];

export const VirtualTryOnPage: React.FC<VirtualTryOnPageProps> = ({
  onNavigate,
  onSelectProductForCheckout,
}) => {
  // Video and Canvas DOM refs
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameIdRef = useRef<number | null>(null);

  // Catalogue & Frame selection state
  const [frames, setFrames] = useState<FrameTryOnAsset[]>(FALLBACK_FRAMES);
  const [categories, setCategories] = useState<FrameCategory[]>([]);
  const [selectedShape, setSelectedShape] = useState<string>('all');
  const [selectedFrame, setSelectedFrame] = useState<FrameTryOnAsset>(FALLBACK_FRAMES[0]);
  const [selectedColor, setSelectedColor] = useState<string>(
    FALLBACK_FRAMES[0].available_colors[0]?.hex_code || '#111827'
  );

  // AR Try-On Session telemetry state
  const [tryOnSession, setTryOnSession] = useState<TryOnSession | null>(null);
  const [favouriteFrames, setFavouriteFrames] = useState<Set<string>>(new Set());

  // Camera & Tracking state
  const [cameraActive, setCameraActive] = useState<boolean>(false);
  const [cameraFacing, setCameraFacing] = useState<'user' | 'environment'>('user');
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [faceState, setFaceState] = useState<FaceTrackingState>({
    detected: false,
    confidence: 0,
    leftEyeCenter: { x: 0, y: 0 },
    rightEyeCenter: { x: 0, y: 0 },
    bridgeCenter: { x: 0, y: 0 },
    leftTemple: { x: 0, y: 0 },
    rightTemple: { x: 0, y: 0 },
    interpupillaryDistancePx: 0,
    faceWidthPx: 0,
    rollAngleRad: 0,
    smoothed: false,
  });

  // User calibration offsets
  const [userScale, setUserScale] = useState<number>(1.0);
  const [userOffsetY, setUserOffsetY] = useState<number>(0);
  const [showAdjustmentDrawer, setShowAdjustmentDrawer] = useState<boolean>(false);
  const [showDebugLandmarks, setShowDebugLandmarks] = useState<boolean>(false);

  // Snapshot Capture Modal state
  const [capturedSnapshot, setCapturedSnapshot] = useState<string | null>(null);
  const [snapshotSuccessToast, setSnapshotSuccessToast] = useState<string | null>(null);

  // 1. Fetch frames and categories from backend
  useEffect(() => {
    let isMounted = true;

    async function loadCatalogue() {
      try {
        const [fetchedFrames, fetchedCategories] = await Promise.all([
          apiClient.listTryOnFrames().catch(() => FALLBACK_FRAMES),
          apiClient.listFrameCategories().catch(() => []),
        ]);

        if (isMounted) {
          if (fetchedFrames && fetchedFrames.length > 0) {
            setFrames(fetchedFrames);
            setSelectedFrame(fetchedFrames[0]);
            if (fetchedFrames[0].available_colors?.length > 0) {
              setSelectedColor(fetchedFrames[0].available_colors[0].hex_code);
            }
          }
          if (fetchedCategories && fetchedCategories.length > 0) {
            setCategories(fetchedCategories);
          }
        }
      } catch (err) {
        console.warn('Backend catalogue unavailable, falling back to built-in models:', err);
      }
    }

    loadCatalogue();

    // Initialize Face Tracking Engine
    faceTracker.initialize().catch((err) => {
      console.warn('Face tracker initialization notice:', err);
    });

    return () => {
      isMounted = false;
      stopCameraStream();
      faceTracker.destroy();
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
    };
  }, []);

  // 2. Preload active frame asset
  useEffect(() => {
    if (selectedFrame) {
      glassesRenderer.preloadFrame(selectedFrame, selectedColor);
    }
  }, [selectedFrame, selectedColor]);

  // 3. Start Camera Stream
  const startCamera = async (facing: 'user' | 'environment' = cameraFacing) => {
    setCameraError(null);
    try {
      if (videoRef.current && videoRef.current.srcObject) {
        stopCameraStream();
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facing,
          width: { ideal: 1280, min: 640 },
          height: { ideal: 720, min: 480 },
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play();
          setCameraActive(true);
          startRenderLoop();
        };
      }

      // Initialize or sync backend session
      try {
        const session = await apiClient.createTryOnSession({
          selected_product_id: selectedFrame.frame_id,
          selected_color: selectedColor,
          selected_scale: userScale,
          selected_offset_y: userOffsetY,
          camera_facing: facing,
          device_type: window.innerWidth < 768 ? 'mobile' : 'desktop',
        });
        setTryOnSession(session);
      } catch {
        // Backend offline or anonymous session
      }
    } catch (err: any) {
      console.error('Camera startup error:', err);
      if (err.name === 'NotAllowedError') {
        setCameraError('Camera access was denied. Please allow camera permissions in your browser address bar.');
      } else if (err.name === 'NotFoundError') {
        setCameraError('No camera device detected on this system.');
      } else if (err.name === 'NotReadableError') {
        setCameraError('The camera is already being used by another application or tab.');
      } else {
        setCameraError('Unable to access camera feed. Please check your system settings.');
      }
      setCameraActive(false);
    }
  };

  const stopCameraStream = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    if (animFrameIdRef.current) {
      cancelAnimationFrame(animFrameIdRef.current);
      animFrameIdRef.current = null;
    }
    setCameraActive(false);
    faceTracker.reset();
  };

  const toggleCameraFacing = async () => {
    const nextFacing = cameraFacing === 'user' ? 'environment' : 'user';
    setCameraFacing(nextFacing);
    if (cameraActive) {
      await startCamera(nextFacing);
    }
  };

  // 4. Main Real-Time 60 FPS Render Loop
  const startRenderLoop = useCallback(() => {
    const render = () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (!video || !canvas || video.readyState < 2) {
        animFrameIdRef.current = requestAnimationFrame(render);
        return;
      }

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        animFrameIdRef.current = requestAnimationFrame(render);
        return;
      }

      // Sync canvas dimensions with actual video aspect ratio
      const width = video.videoWidth || 640;
      const height = video.videoHeight || 480;
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      // 1. Draw live camera video feed
      ctx.save();
      if (cameraFacing === 'user') {
        // Mirror selfie view for natural mirror experience
        ctx.translate(width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0, width, height);
      } else {
        ctx.drawImage(video, 0, 0, width, height);
      }
      ctx.restore();

      // 2. Track Face Landmarks
      const tracking = faceTracker.detectLandmarks(video, width, height);
      setFaceState(tracking);

      // 3. Render AR Glasses Overlay
      if (tracking.detected && selectedFrame) {
        glassesRenderer.renderOverlay(ctx, tracking, selectedFrame, {
          selectedColor,
          userScale,
          userOffsetY,
          showDebugLandmarks,
        });
      }

      animFrameIdRef.current = requestAnimationFrame(render);
    };

    if (animFrameIdRef.current) {
      cancelAnimationFrame(animFrameIdRef.current);
    }
    animFrameIdRef.current = requestAnimationFrame(render);
  }, [cameraFacing, selectedFrame, selectedColor, userScale, userOffsetY, showDebugLandmarks]);

  // 5. Select frame
  const handleSelectFrame = (frame: FrameTryOnAsset) => {
    setSelectedFrame(frame);
    const primaryColor = frame.available_colors && frame.available_colors.length > 0
      ? frame.available_colors[0].hex_code
      : '#111827';
    setSelectedColor(primaryColor);

    if (tryOnSession?.id) {
      apiClient.selectTryOnFrame(tryOnSession.id, {
        product_id: frame.frame_id,
        selected_color: primaryColor,
        selected_scale: userScale,
        selected_offset_y: userOffsetY,
      }).catch(() => {});
    }
  };

  // 6. Toggle favourite
  const handleToggleFavourite = async (frame: FrameTryOnAsset) => {
    const isFav = favouriteFrames.has(frame.frame_id);
    const updated = new Set(favouriteFrames);
    if (isFav) {
      updated.delete(frame.frame_id);
    } else {
      updated.add(frame.frame_id);
    }
    setFavouriteFrames(updated);

    if (tryOnSession?.id) {
      try {
        await apiClient.toggleFavouriteFrame(tryOnSession.id, {
          product_id: frame.frame_id,
          selected_color: selectedColor,
        });
      } catch {
        // Guest mode fallback
      }
    }

    setSnapshotSuccessToast(isFav ? 'Removed from saved collection' : 'Added to saved frames');
    setTimeout(() => setSnapshotSuccessToast(null), 3000);
  };

  // 7. Capture snapshot preview
  const handleCaptureSnapshot = () => {
    const video = videoRef.current;
    if (!video || !selectedFrame) return;

    try {
      const dataUrl = glassesRenderer.captureSnapshot(video, faceState, selectedFrame, {
        selectedColor,
        userScale,
        userOffsetY,
      });

      setCapturedSnapshot(dataUrl);

      if (tryOnSession?.id) {
        apiClient.recordTryOnSnapshot(tryOnSession.id, {
          product_id: selectedFrame.frame_id,
          selected_color: selectedColor,
          title: `OptiGuide AR Preview — ${selectedFrame.name}`,
          face_detected: faceState.detected,
        }).catch(() => {});
      }
    } catch (err) {
      console.error('Snapshot capture error:', err);
    }
  };

  // Download snapshot to device
  const handleDownloadSnapshot = () => {
    if (!capturedSnapshot) return;
    const a = document.createElement('a');
    a.href = capturedSnapshot;
    a.download = `OptiGuide-TryOn-${selectedFrame.name.replace(/\s+/g, '-')}-${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // Filtered frames
  const filteredFrames = frames.filter((f) => {
    if (selectedShape === 'all') return true;
    return (
      f.frame_shape.toLowerCase() === selectedShape.toLowerCase() ||
      (f.category_name && f.category_name.toLowerCase().includes(selectedShape.toLowerCase()))
    );
  });

  // Category and shape filters for quick filter chips
  const shapeCategories = [
    { id: 'all', label: 'All Frames' },
    ...categories.map((c) => ({ id: c.slug, label: c.name })),
    { id: 'rectangular', label: 'Rectangular' },
    { id: 'round', label: 'Round' },
    { id: 'aviator', label: 'Aviator' },
    { id: 'square', label: 'Square' },
    { id: 'cat-eye', label: 'Cat-Eye' },
    { id: 'wayfarer', label: 'Wayfarer' },
    { id: 'semi-rimless', label: 'Semi-Rimless' },
    { id: 'rimless', label: 'Rimless' },
  ].filter((v, idx, arr) => arr.findIndex((item) => item.id === v.id) === idx);

  return (
    <div style={{ backgroundColor: '#F8FAFC', minHeight: '92vh', color: '#0F172A', paddingBottom: '48px' }}>
      {/* Toast Notification */}
      {snapshotSuccessToast && (
        <div
          style={{
            position: 'fixed',
            top: '80px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: '#0F766E',
            color: '#FFFFFF',
            padding: '10px 20px',
            borderRadius: '9999px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.875rem',
            fontWeight: 600,
          }}
        >
          <CheckIcon size={16} color="#FFFFFF" />
          {snapshotSuccessToast}
        </div>
      )}

      {/* Header Bar */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderBottom: '1px solid #E2E8F0',
          padding: '16px 24px',
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        }}
      >
        <div
          style={{
            maxWidth: '1360px',
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '16px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  backgroundColor: '#CCFBF1',
                  color: '#0F766E',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '3px 10px',
                  borderRadius: '9999px',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                AI Virtual Eyewear Studio
              </span>
              <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                Real-Time 3D Face Landmark Tracking
              </span>
            </div>
            <h1
              style={{
                fontSize: '1.75rem',
                fontWeight: 700,
                color: '#0F172A',
                marginTop: '4px',
                marginBottom: '2px',
                letterSpacing: '-0.02em',
              }}
            >
              Interactive AR Virtual Try-On
            </h1>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {onNavigate && (
              <button
                onClick={() => onNavigate('eyewear')}
                style={{
                  backgroundColor: '#F1F5F9',
                  border: '1px solid #CBD5E1',
                  color: '#334155',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <GlassesIcon size={16} />
                Catalogue Grid
              </button>
            )}

            {onNavigate && (
              <button
                onClick={() => onNavigate('screening')}
                style={{
                  backgroundColor: '#0F766E',
                  border: 'none',
                  color: '#FFFFFF',
                  padding: '8px 18px',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  boxShadow: '0 2px 4px rgba(15, 118, 110, 0.2)',
                }}
              >
                <EyeIcon size={16} />
                Vision Test
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Studio Viewport */}
      <div
        style={{
          maxWidth: '1360px',
          margin: '24px auto',
          padding: '0 20px',
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1fr)',
          gap: '24px',
        }}
      >
        {/* AR Camera Stage */}
        <div
          style={{
            backgroundColor: '#0F172A',
            borderRadius: '20px',
            overflow: 'hidden',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '520px',
          }}
        >
          {/* Live Hidden Video Source */}
          <video
            ref={videoRef}
            playsInline
            muted
            style={{ display: 'none' }}
          />

          {/* Active AR Canvas Output */}
          <canvas
            ref={canvasRef}
            style={{
              width: '100%',
              maxHeight: '620px',
              objectFit: 'contain',
              display: cameraActive ? 'block' : 'none',
              borderRadius: '20px',
            }}
          />

          {/* Camera Idle State Placeholder */}
          {!cameraActive && (
            <div
              style={{
                padding: '48px 24px',
                textAlign: 'center',
                maxWidth: '560px',
                color: '#FFFFFF',
              }}
            >
              <div
                style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 24px',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                }}
              >
                <CameraIcon size={40} color="#38BDF8" />
              </div>

              <h2 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '12px' }}>
                Experience Virtual Glasses on Your Face
              </h2>
              <p
                style={{
                  color: '#94A3B8',
                  fontSize: '1rem',
                  lineHeight: 1.6,
                  marginBottom: '28px',
                }}
              >
                Grant camera access to see live frames rendered with automatic eye alignment, head tilt tracking, and true-to-scale sizing.
              </p>

              {cameraError && (
                <div
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.15)',
                    border: '1px solid #EF4444',
                    color: '#FCA5A5',
                    padding: '12px 16px',
                    borderRadius: '10px',
                    fontSize: '0.875rem',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    textAlign: 'left',
                  }}
                >
                  <AlertIcon size={20} color="#EF4444" />
                  <span>{cameraError}</span>
                </div>
              )}

              <button
                onClick={() => startCamera()}
                style={{
                  backgroundColor: '#0EA5E9',
                  color: '#FFFFFF',
                  border: 'none',
                  padding: '14px 32px',
                  borderRadius: '12px',
                  fontSize: '1.0625rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(14, 165, 233, 0.4)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '10px',
                  transition: 'transform 0.15s ease',
                }}
              >
                <CameraIcon size={20} color="#FFFFFF" />
                Enable Camera & Start Try-On
              </button>

              <div
                style={{
                  marginTop: '24px',
                  color: '#64748B',
                  fontSize: '0.8125rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <SparklesIcon size={14} color="#0D9488" />
                <span>Private & Secure: Video frames are computed locally in your browser and never uploaded.</span>
              </div>
            </div>
          )}

          {/* Live Camera Overlaid HUD Controls */}
          {cameraActive && (
            <>
              {/* Top Status Bar HUD */}
              <div
                style={{
                  position: 'absolute',
                  top: '16px',
                  left: '16px',
                  right: '16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  pointerEvents: 'none',
                }}
              >
                {/* Face Tracking Pill */}
                <div
                  style={{
                    backgroundColor: 'rgba(15, 23, 42, 0.75)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    color: '#FFFFFF',
                    padding: '6px 14px',
                    borderRadius: '9999px',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    pointerEvents: 'auto',
                  }}
                >
                  <span
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: faceState.detected ? '#10B981' : '#F59E0B',
                      boxShadow: faceState.detected
                        ? '0 0 8px #10B981'
                        : '0 0 8px #F59E0B',
                    }}
                  />
                  <span>
                    {faceState.detected
                      ? `Face Tracked (${Math.round((faceState.confidence || 0.95) * 100)}%)`
                      : 'Looking for Face...'}
                  </span>
                  {faceTracker.isUsingFallback() && (
                    <span
                      style={{
                        fontSize: '0.7rem',
                        backgroundColor: '#334155',
                        padding: '1px 6px',
                        borderRadius: '4px',
                        color: '#94A3B8',
                      }}
                    >
                      Geometric Mode
                    </span>
                  )}
                </div>

                {/* Right Quick Controls HUD */}
                <div style={{ display: 'flex', gap: '8px', pointerEvents: 'auto' }}>
                  {/* Switch Front/Back Camera */}
                  <button
                    onClick={toggleCameraFacing}
                    title="Switch Front/Rear Camera"
                    style={{
                      backgroundColor: 'rgba(15, 23, 42, 0.75)',
                      backdropFilter: 'blur(8px)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      color: '#FFFFFF',
                      width: '38px',
                      height: '38px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                    }}
                  >
                    <SwitchCameraIcon size={18} color="#FFFFFF" />
                  </button>

                  {/* Calibration & Fit Adjustments */}
                  <button
                    onClick={() => setShowAdjustmentDrawer(!showAdjustmentDrawer)}
                    title="Fine-Tune Frame Position & Fit"
                    style={{
                      backgroundColor: showAdjustmentDrawer
                        ? '#0284C7'
                        : 'rgba(15, 23, 42, 0.75)',
                      backdropFilter: 'blur(8px)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      color: '#FFFFFF',
                      width: '38px',
                      height: '38px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                    }}
                  >
                    <SlidersIcon size={18} color="#FFFFFF" />
                  </button>

                  {/* Stop Camera */}
                  <button
                    onClick={stopCameraStream}
                    title="Stop Camera"
                    style={{
                      backgroundColor: 'rgba(239, 68, 68, 0.8)',
                      backdropFilter: 'blur(8px)',
                      border: 'none',
                      color: '#FFFFFF',
                      padding: '6px 14px',
                      borderRadius: '9999px',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Stop
                  </button>
                </div>
              </div>

              {/* Bottom Camera Action Bar */}
              <div
                style={{
                  position: 'absolute',
                  bottom: '20px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                }}
              >
                {/* Snapshot Shutter Button */}
                <button
                  onClick={handleCaptureSnapshot}
                  title="Capture Photo Preview"
                  style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '50%',
                    backgroundColor: '#FFFFFF',
                    border: '4px solid #0284C7',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    boxShadow: '0 8px 20px rgba(0, 0, 0, 0.3)',
                    transition: 'transform 0.1s ease',
                  }}
                >
                  <div
                    style={{
                      width: '46px',
                      height: '46px',
                      borderRadius: '50%',
                      backgroundColor: '#0284C7',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <CameraIcon size={24} color="#FFFFFF" />
                  </div>
                </button>
              </div>

              {/* Floating Fit Adjustment Panel */}
              {showAdjustmentDrawer && (
                <div
                  style={{
                    position: 'absolute',
                    top: '70px',
                    right: '16px',
                    width: '280px',
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    backdropFilter: 'blur(12px)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: '16px',
                    padding: '16px',
                    color: '#FFFFFF',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.4)',
                    zIndex: 50,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '14px',
                    }}
                  >
                    <span style={{ fontSize: '0.875rem', fontWeight: 700 }}>
                      Adjust Fit & Position
                    </span>
                    <button
                      onClick={() => {
                        setUserScale(1.0);
                        setUserOffsetY(0);
                      }}
                      style={{
                        backgroundColor: 'transparent',
                        border: 'none',
                        color: '#38BDF8',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <RefreshIcon size={12} color="#38BDF8" />
                      Reset
                    </button>
                  </div>

                  {/* Size Scale Slider */}
                  <div style={{ marginBottom: '14px' }}>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        fontSize: '0.75rem',
                        color: '#94A3B8',
                        marginBottom: '4px',
                      }}
                    >
                      <span>Scale / Width:</span>
                      <span>{Math.round(userScale * 100)}%</span>
                    </div>
                    <input
                      type="range"
                      min="0.8"
                      max="1.25"
                      step="0.01"
                      value={userScale}
                      onChange={(e) => setUserScale(parseFloat(e.target.value))}
                      style={{ width: '100%', accentColor: '#0284C7' }}
                    />
                  </div>

                  {/* Vertical Bridge Offset */}
                  <div style={{ marginBottom: '14px' }}>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        fontSize: '0.75rem',
                        color: '#94A3B8',
                        marginBottom: '4px',
                      }}
                    >
                      <span>Bridge Height:</span>
                      <span>{userOffsetY > 0 ? `+${userOffsetY}` : userOffsetY}px</span>
                    </div>
                    <input
                      type="range"
                      min="-25"
                      max="25"
                      step="1"
                      value={userOffsetY}
                      onChange={(e) => setUserOffsetY(parseInt(e.target.value, 10))}
                      style={{ width: '100%', accentColor: '#0284C7' }}
                    />
                  </div>

                  {/* Diagnostic Landmarks Toggle */}
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      fontSize: '0.75rem',
                      color: '#CBD5E1',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={showDebugLandmarks}
                      onChange={(e) => setShowDebugLandmarks(e.target.checked)}
                      style={{ accentColor: '#0284C7' }}
                    />
                    <span>Show Optical Eye Alignment Points</span>
                  </label>
                </div>
              )}
            </>
          )}
        </div>

        {/* Selected Frame Detail & Interactive Controls */}
        {selectedFrame && (
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              border: '1px solid #E2E8F0',
              padding: '24px',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '24px',
              alignItems: 'center',
            }}
          >
            {/* Left: Frame Info */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    color: '#0F766E',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  {selectedFrame.brand_name}
                </span>
                <span style={{ color: '#CBD5E1' }}>•</span>
                <span style={{ fontSize: '0.75rem', color: '#64748B', textTransform: 'capitalize' }}>
                  {selectedFrame.frame_shape} Shape ({selectedFrame.frame_material})
                </span>
              </div>

              <h2
                style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: '#0F172A',
                  marginBottom: '6px',
                }}
              >
                {selectedFrame.name}
              </h2>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '14px' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0F766E' }}>
                  ₹{Number(selectedFrame.base_price_inr).toLocaleString('en-IN')}
                </span>
                <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                  Includes prescription lens fitting & case
                </span>
              </div>

              {/* Physical Measurements Chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '16px' }}>
                <div
                  style={{
                    backgroundColor: '#F1F5F9',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '0.8125rem',
                    color: '#334155',
                  }}
                >
                  <strong>Total Width:</strong> {selectedFrame.frame_width_mm || 138} mm
                </div>
                <div
                  style={{
                    backgroundColor: '#F1F5F9',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '0.8125rem',
                    color: '#334155',
                  }}
                >
                  <strong>Lens:</strong> {selectedFrame.lens_width_mm || 52} mm
                </div>
                <div
                  style={{
                    backgroundColor: '#F1F5F9',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '0.8125rem',
                    color: '#334155',
                  }}
                >
                  <strong>Bridge:</strong> {selectedFrame.bridge_width_mm || 18} mm
                </div>
                <div
                  style={{
                    backgroundColor: '#F1F5F9',
                    padding: '6px 12px',
                    borderRadius: '8px',
                    fontSize: '0.8125rem',
                    color: '#334155',
                  }}
                >
                  <strong>Temple:</strong> {selectedFrame.temple_length_mm || 142} mm
                </div>
              </div>
            </div>

            {/* Right: Color Swatches & Action Buttons */}
            <div>
              {/* Dynamic Color Selection */}
              {selectedFrame.available_colors && selectedFrame.available_colors.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      color: '#475569',
                      marginBottom: '8px',
                    }}
                  >
                    Select Frame Color Variant:
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {selectedFrame.available_colors.map((c) => {
                      const isSelected = selectedColor === c.hex_code;
                      return (
                        <button
                          key={c.hex_code}
                          onClick={() => setSelectedColor(c.hex_code)}
                          title={c.name}
                          style={{
                            width: '36px',
                            height: '36px',
                            borderRadius: '50%',
                            backgroundColor: c.hex_code,
                            border: isSelected
                              ? '3px solid #0EA5E9'
                              : '2px solid #E2E8F0',
                            boxShadow: isSelected
                              ? '0 0 0 2px rgba(14, 165, 233, 0.4)'
                              : 'none',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                          }}
                        />
                      );
                    })}
                    <span style={{ fontSize: '0.8125rem', color: '#64748B', marginLeft: '4px' }}>
                      {selectedFrame.available_colors.find((c) => c.hex_code === selectedColor)?.name}
                    </span>
                  </div>
                </div>
              )}

              {/* Primary Actions */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                {/* Wishlist Button */}
                <button
                  onClick={() => handleToggleFavourite(selectedFrame)}
                  style={{
                    backgroundColor: favouriteFrames.has(selectedFrame.frame_id)
                      ? '#FEE2E2'
                      : '#F8FAFC',
                    border: '1px solid',
                    borderColor: favouriteFrames.has(selectedFrame.frame_id)
                      ? '#F87171'
                      : '#CBD5E1',
                    color: favouriteFrames.has(selectedFrame.frame_id)
                      ? '#DC2626'
                      : '#475569',
                    padding: '10px 18px',
                    borderRadius: '10px',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <HeartIcon
                    size={18}
                    color={favouriteFrames.has(selectedFrame.frame_id) ? '#DC2626' : '#475569'}
                    filled={favouriteFrames.has(selectedFrame.frame_id)}
                  />
                  <span>
                    {favouriteFrames.has(selectedFrame.frame_id) ? 'Saved' : 'Save Frame'}
                  </span>
                </button>

                {/* Add to Optical Cart / Inquiry */}
                <button
                  onClick={() => {
                    if (onSelectProductForCheckout) {
                      onSelectProductForCheckout(selectedFrame);
                    } else if (onNavigate) {
                      onNavigate('eyewear');
                    } else {
                      setSnapshotSuccessToast(`${selectedFrame.name} selected for optical guidance!`);
                      setTimeout(() => setSnapshotSuccessToast(null), 3000);
                    }
                  }}
                  style={{
                    backgroundColor: '#0F766E',
                    color: '#FFFFFF',
                    border: 'none',
                    padding: '10px 24px',
                    borderRadius: '10px',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    boxShadow: '0 2px 4px rgba(15, 118, 110, 0.2)',
                  }}
                >
                  <ShoppingBagIcon size={18} color="#FFFFFF" />
                  <span>Choose This Frame</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Frame Catalogue Selector Carousel */}
        <div style={{ marginTop: '8px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A' }}>
                Select Frame Style to Try On
              </h3>
              <p style={{ fontSize: '0.875rem', color: '#64748B' }}>
                Switch styles instantaneously to preview fit, bridge profile, and facial geometry.
              </p>
            </div>

            {/* Shape Filter Pills */}
            <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', maxWidth: '100%', paddingBottom: '4px' }}>
              {shapeCategories.map((cat) => {
                const isActive = selectedShape === cat.id;
                return (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedShape(cat.id)}
                    style={{
                      backgroundColor: isActive ? '#0F766E' : '#FFFFFF',
                      color: isActive ? '#FFFFFF' : '#475569',
                      border: '1px solid',
                      borderColor: isActive ? '#0F766E' : '#CBD5E1',
                      padding: '6px 14px',
                      borderRadius: '9999px',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {cat.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Frame Carousel Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))',
              gap: '16px',
            }}
          >
            {filteredFrames.map((frame) => {
              const isSelected = selectedFrame?.frame_id === frame.frame_id;
              const isFav = favouriteFrames.has(frame.frame_id);

              return (
                <div
                  key={frame.frame_id}
                  onClick={() => handleSelectFrame(frame)}
                  style={{
                    backgroundColor: '#FFFFFF',
                    borderRadius: '14px',
                    border: isSelected
                      ? '2px solid #0EA5E9'
                      : '1px solid #E2E8F0',
                    padding: '16px',
                    cursor: 'pointer',
                    boxShadow: isSelected
                      ? '0 8px 16px -2px rgba(14, 165, 233, 0.2)'
                      : '0 1px 3px rgba(0, 0, 0, 0.05)',
                    transition: 'all 0.15s ease',
                    position: 'relative',
                  }}
                >
                  {/* Favourite heart indicator */}
                  {isFav && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '12px',
                        right: '12px',
                        color: '#EF4444',
                      }}
                    >
                      <HeartIcon size={16} filled color="#EF4444" />
                    </div>
                  )}

                  {/* Frame SVG Vector Thumbnail */}
                  <div
                    style={{
                      height: '90px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: '#F8FAFC',
                      borderRadius: '10px',
                      marginBottom: '12px',
                      padding: '8px',
                    }}
                  >
                    <img
                      src={frame.try_on_asset_url || `/assets/frames/frame-${frame.frame_shape.toLowerCase().replace(/_/g, '-')}.svg`}
                      alt={frame.name}
                      style={{
                        maxWidth: '100%',
                        maxHeight: '100%',
                        objectFit: 'contain',
                        color: '#111827',
                      }}
                    />
                  </div>

                  <div style={{ fontSize: '0.75rem', color: '#64748B', fontWeight: 600 }}>
                    {frame.brand_name}
                  </div>
                  <div
                    style={{
                      fontSize: '0.9375rem',
                      fontWeight: 700,
                      color: '#0F172A',
                      marginTop: '2px',
                      marginBottom: '6px',
                      lineHeight: 1.25,
                    }}
                  >
                    {frame.name}
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginTop: '10px',
                      paddingTop: '8px',
                      borderTop: '1px solid #F1F5F9',
                    }}
                  >
                    <span style={{ fontSize: '1rem', fontWeight: 800, color: '#0F766E' }}>
                      ₹{Number(frame.base_price_inr).toLocaleString('en-IN')}
                    </span>

                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        color: isSelected ? '#0284C7' : '#64748B',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      {isSelected ? '✓ Active Try-On' : 'Try On →'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Snapshot Preview Modal */}
      {capturedSnapshot && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(8px)',
            zIndex: 1100,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '20px',
              maxWidth: '680px',
              width: '100%',
              overflow: 'hidden',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '18px 24px',
                borderBottom: '1px solid #E2E8F0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A' }}>
                  AR Try-On Snapshot
                </h3>
                <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                  {selectedFrame?.name} — {selectedFrame?.brand_name}
                </span>
              </div>

              <button
                onClick={() => setCapturedSnapshot(null)}
                style={{
                  backgroundColor: '#F1F5F9',
                  border: 'none',
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  cursor: 'pointer',
                  fontSize: '1rem',
                  fontWeight: 700,
                  color: '#64748B',
                }}
              >
                ✕
              </button>
            </div>

            {/* Image Preview Container */}
            <div
              style={{
                backgroundColor: '#0F172A',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '16px',
              }}
            >
              <img
                src={capturedSnapshot}
                alt="AR Try-On Preview"
                style={{
                  maxWidth: '100%',
                  maxHeight: '440px',
                  borderRadius: '12px',
                  objectFit: 'contain',
                }}
              />
            </div>

            {/* Modal Footer Actions */}
            <div
              style={{
                padding: '16px 24px',
                backgroundColor: '#F8FAFC',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              <span style={{ fontSize: '0.8125rem', color: '#64748B' }}>
                High-resolution frame alignment captured locally.
              </span>

              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={handleDownloadSnapshot}
                  style={{
                    backgroundColor: '#0284C7',
                    color: '#FFFFFF',
                    border: 'none',
                    padding: '10px 20px',
                    borderRadius: '10px',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <DownloadIcon size={16} color="#FFFFFF" />
                  Save Photo
                </button>

                <button
                  onClick={() => setCapturedSnapshot(null)}
                  style={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #CBD5E1',
                    color: '#334155',
                    padding: '10px 18px',
                    borderRadius: '10px',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
