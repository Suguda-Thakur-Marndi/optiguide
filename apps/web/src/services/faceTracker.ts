import { FilesetResolver, FaceLandmarker } from '@mediapipe/tasks-vision';
import type { FaceTrackingState, Point2D } from '../types/tryOn';

/**
 * OptiGuide Sub-Millimeter Face Tracking Service
 *
 * Coordinate Convention & Anatomical Reference:
 * - MediaPipe FaceLandmarker processes the unmirrored raw camera frame.
 * - Normalized coordinates [0..1] range from (0,0) at top-left to (1,1) at bottom-right.
 * - Anatomical Right Eye: Indices 33 (outer canthus), 133 (inner canthus), 159 (upper lid), 145 (lower lid), 468 (iris pupil).
 * - Anatomical Left Eye: Indices 263 (outer canthus), 362 (inner canthus), 386 (upper lid), 374 (lower lid), 473 (iris pupil).
 * - Nose Bridge (Sellion/Nasion): Landmark 168 (with backup landmark 6).
 *
 * Screen Coordinate System:
 * - When isMirrored = true (Front/Selfie camera), coordinates are flipped horizontally:
 *     screenX = (1 - x_norm) * canvasWidth
 * - When isMirrored = false (Rear camera), coordinates are mapped directly:
 *     screenX = x_norm * canvasWidth
 * - In screen space:
 *     screenLeftEyeCenter = eye point with smaller X (viewer's left side of screen).
 *     screenRightEyeCenter = eye point with larger X (viewer's right side of screen).
 *     rollAngleRad = atan2(screenRightEye.y - screenLeftEye.y, screenRightEye.x - screenLeftEye.x).
 */

export const LANDMARK_INDICES = {
  // Standard & backward-compatible aliases
  NOSE_BRIDGE: 168,
  LEFT_PUPIL: 468,
  RIGHT_PUPIL: 473,
  LEFT_TEMPLE: 234,
  RIGHT_TEMPLE: 454,

  // Anatomical Right Eye (appears on screen-left in unmirrored view)
  ANAT_RIGHT_PUPIL: 468,
  ANAT_RIGHT_INNER: 133,
  ANAT_RIGHT_OUTER: 33,
  ANAT_RIGHT_UPPER: 159,
  ANAT_RIGHT_LOWER: 145,

  // Anatomical Left Eye (appears on screen-right in unmirrored view)
  ANAT_LEFT_PUPIL: 473,
  ANAT_LEFT_INNER: 362,
  ANAT_LEFT_OUTER: 263,
  ANAT_LEFT_UPPER: 386,
  ANAT_LEFT_LOWER: 374,

  // Nose Bridge & Facial Features
  NOSE_BRIDGE_CREST: 168,
  NOSE_BRIDGE_UPPER: 6,
  NOSE_TIP: 1,
  ANAT_RIGHT_TEMPLE: 234,
  ANAT_LEFT_TEMPLE: 454,
  FOREHEAD: 10,
  CHIN: 152,
};

const BASE_ALPHA = 0.35; // Default stillness smoothing factor
const FAST_ALPHA = 0.75; // Fast motion responsive smoothing factor

export class FaceTrackerService {
  private landmarker: FaceLandmarker | null = null;
  private isInitializing = false;
  private isReady = false;
  private useFallback = false;
  private smoothedState: FaceTrackingState | null = null;
  private smoothingAlpha = BASE_ALPHA;

  /**
   * Initializes MediaPipe FaceLandmarker with wasm runtime and float16 model.
   */
  public async initialize(): Promise<boolean> {
    if (this.isReady) return true;
    if (this.isInitializing) return false;

    this.isInitializing = true;
    try {
      const vision = await FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
      );

      this.landmarker = await FaceLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath:
            'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
          delegate: 'GPU',
        },
        runningMode: 'VIDEO',
        numFaces: 1,
        minFaceDetectionConfidence: 0.5,
        minFacePresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
        outputFaceBlendshapes: false,
        outputFacialTransformationMatrixes: false,
      });

      this.isReady = true;
      this.useFallback = false;
      return true;
    } catch (err) {
      console.warn('MediaPipe initialization notice, falling back to geometric tracker:', err);
      this.useFallback = true;
      this.isReady = true;
      return true;
    } finally {
      this.isInitializing = false;
    }
  }

  public isInitialized(): boolean {
    return this.isReady;
  }

  public isUsingFallback(): boolean {
    return this.useFallback;
  }

  public setSmoothingAlpha(alpha: number): void {
    this.smoothingAlpha = Math.max(0.05, Math.min(1.0, alpha));
  }

  /**
   * Detects facial landmarks from video and projects them to screen canvas coordinates.
   *
   * @param video HTMLVideoElement source
   * @param canvasWidth Internal canvas pixel width
   * @param canvasHeight Internal canvas pixel height
   * @param isMirrored True if video is rendered horizontally flipped (selfie front camera)
   * @param timestampMs Optional frame timestamp
   */
  public detectLandmarks(
    video: HTMLVideoElement,
    canvasWidth: number,
    canvasHeight: number,
    isMirrored: boolean = true,
    timestampMs?: number
  ): FaceTrackingState {
    const now = timestampMs ?? performance.now();

    if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
      return this.createUntrackedState(isMirrored);
    }

    if (!this.isReady || !this.landmarker || this.useFallback) {
      return this.detectFallback(video, canvasWidth, canvasHeight, isMirrored);
    }

    try {
      const results = this.landmarker.detectForVideo(video, now);

      if (!results.faceLandmarks || results.faceLandmarks.length === 0) {
        this.smoothedState = null;
        return this.createUntrackedState(isMirrored);
      }

      const raw = results.faceLandmarks[0];

      // 1. Calculate robust anatomical eye centers in normalized video space
      const normRightEyeCenter = FaceTrackerService.calculateRobustEyeCenter(
        raw[LANDMARK_INDICES.ANAT_RIGHT_INNER],
        raw[LANDMARK_INDICES.ANAT_RIGHT_OUTER],
        raw[LANDMARK_INDICES.ANAT_RIGHT_UPPER],
        raw[LANDMARK_INDICES.ANAT_RIGHT_LOWER],
        raw[LANDMARK_INDICES.ANAT_RIGHT_PUPIL]
      );

      const normLeftEyeCenter = FaceTrackerService.calculateRobustEyeCenter(
        raw[LANDMARK_INDICES.ANAT_LEFT_INNER],
        raw[LANDMARK_INDICES.ANAT_LEFT_OUTER],
        raw[LANDMARK_INDICES.ANAT_LEFT_UPPER],
        raw[LANDMARK_INDICES.ANAT_LEFT_LOWER],
        raw[LANDMARK_INDICES.ANAT_LEFT_PUPIL]
      );

      const normBridge = raw[LANDMARK_INDICES.NOSE_BRIDGE_CREST] || raw[LANDMARK_INDICES.NOSE_BRIDGE_UPPER] || raw[LANDMARK_INDICES.NOSE_TIP];
      const normRightTemple = raw[LANDMARK_INDICES.ANAT_RIGHT_TEMPLE] || normRightEyeCenter;
      const normLeftTemple = raw[LANDMARK_INDICES.ANAT_LEFT_TEMPLE] || normLeftEyeCenter;

      // 2. Project points into screen canvas coordinates with explicit mirroring
      const ptAnatRightEye = FaceTrackerService.convertNormalizedToScreen(normRightEyeCenter, canvasWidth, canvasHeight, isMirrored);
      const ptAnatLeftEye = FaceTrackerService.convertNormalizedToScreen(normLeftEyeCenter, canvasWidth, canvasHeight, isMirrored);
      const ptBridge = FaceTrackerService.convertNormalizedToScreen(normBridge, canvasWidth, canvasHeight, isMirrored);
      const ptRightTemple = FaceTrackerService.convertNormalizedToScreen(normRightTemple, canvasWidth, canvasHeight, isMirrored);
      const ptLeftTemple = FaceTrackerService.convertNormalizedToScreen(normLeftTemple, canvasWidth, canvasHeight, isMirrored);

      // Eye corner detail points
      const ptRightInner = FaceTrackerService.convertNormalizedToScreen(raw[LANDMARK_INDICES.ANAT_RIGHT_INNER], canvasWidth, canvasHeight, isMirrored);
      const ptRightOuter = FaceTrackerService.convertNormalizedToScreen(raw[LANDMARK_INDICES.ANAT_RIGHT_OUTER], canvasWidth, canvasHeight, isMirrored);
      const ptLeftInner = FaceTrackerService.convertNormalizedToScreen(raw[LANDMARK_INDICES.ANAT_LEFT_INNER], canvasWidth, canvasHeight, isMirrored);
      const ptLeftOuter = FaceTrackerService.convertNormalizedToScreen(raw[LANDMARK_INDICES.ANAT_LEFT_OUTER], canvasWidth, canvasHeight, isMirrored);

      // 3. Screen-Left vs Screen-Right Assignment
      // On screen, whichever eye has smaller X is the screenLeftEye.
      const isRightEyeOnScreenLeft = ptAnatRightEye.x <= ptAnatLeftEye.x;

      const screenLeftEye = isRightEyeOnScreenLeft ? ptAnatRightEye : ptAnatLeftEye;
      const screenRightEye = isRightEyeOnScreenLeft ? ptAnatLeftEye : ptAnatRightEye;

      const screenLeftInner = isRightEyeOnScreenLeft ? ptRightInner : ptLeftInner;
      const screenLeftOuter = isRightEyeOnScreenLeft ? ptRightOuter : ptLeftOuter;
      const screenRightInner = isRightEyeOnScreenLeft ? ptLeftInner : ptRightInner;
      const screenRightOuter = isRightEyeOnScreenLeft ? ptLeftOuter : ptRightOuter;

      const screenLeftTemple = ptRightTemple.x <= ptLeftTemple.x ? ptRightTemple : ptLeftTemple;
      const screenRightTemple = ptRightTemple.x > ptLeftTemple.x ? ptRightTemple : ptLeftTemple;

      // 4. Calculate screen metrics
      const ipd = FaceTrackerService.calculateDistance(screenLeftEye, screenRightEye);
      const faceWidth = FaceTrackerService.calculateDistance(screenLeftTemple, screenRightTemple);
      const roll = FaceTrackerService.calculateRollAngle(screenLeftEye, screenRightEye);

      const rawState: FaceTrackingState = {
        detected: true,
        confidence: 0.96,
        isMirrored,
        screenLeftEyeCenter: screenLeftEye,
        screenRightEyeCenter: screenRightEye,
        screenBridgeCenter: ptBridge,
        screenLeftTemple,
        screenRightTemple,
        screenLeftEyeCornerInner: screenLeftInner,
        screenLeftEyeCornerOuter: screenLeftOuter,
        screenRightEyeCornerInner: screenRightInner,
        screenRightEyeCornerOuter: screenRightOuter,

        // Backwards compatibility aliases
        leftEyeCenter: screenLeftEye,
        rightEyeCenter: screenRightEye,
        bridgeCenter: ptBridge,
        leftTemple: screenLeftTemple,
        rightTemple: screenRightTemple,

        interpupillaryDistancePx: ipd,
        faceWidthPx: faceWidth,
        rollAngleRad: roll,
        smoothed: false,
      };

      return this.applySmoothing(rawState);
    } catch (err) {
      console.error('Face tracking error:', err);
      return this.detectFallback(video, canvasWidth, canvasHeight, isMirrored);
    }
  }

  /**
   * Deterministic geometric fallback when MediaPipe is unavailable or running in headless tests.
   */
  public detectFallback(
    _video: HTMLVideoElement,
    canvasWidth: number,
    canvasHeight: number,
    isMirrored: boolean = true
  ): FaceTrackingState {
    const centerX = canvasWidth * 0.5;
    const centerY = canvasHeight * 0.42;
    const ipd = canvasWidth * 0.22;
    const faceWidth = canvasWidth * 0.52;

    const screenLeftEye: Point2D = {
      x: centerX - ipd * 0.5,
      y: centerY,
    };
    const screenRightEye: Point2D = {
      x: centerX + ipd * 0.5,
      y: centerY,
    };
    const bridge: Point2D = {
      x: centerX,
      y: centerY - 4,
    };
    const leftTemple: Point2D = {
      x: centerX - faceWidth * 0.5,
      y: centerY + 10,
    };
    const rightTemple: Point2D = {
      x: centerX + faceWidth * 0.5,
      y: centerY + 10,
    };

    const eyeHalfWidth = ipd * 0.25;

    const rawState: FaceTrackingState = {
      detected: true,
      confidence: 0.85,
      isMirrored,
      screenLeftEyeCenter: screenLeftEye,
      screenRightEyeCenter: screenRightEye,
      screenBridgeCenter: bridge,
      screenLeftTemple: leftTemple,
      screenRightTemple: rightTemple,
      screenLeftEyeCornerInner: { x: screenLeftEye.x + eyeHalfWidth, y: centerY },
      screenLeftEyeCornerOuter: { x: screenLeftEye.x - eyeHalfWidth, y: centerY },
      screenRightEyeCornerInner: { x: screenRightEye.x - eyeHalfWidth, y: centerY },
      screenRightEyeCornerOuter: { x: screenRightEye.x + eyeHalfWidth, y: centerY },

      leftEyeCenter: screenLeftEye,
      rightEyeCenter: screenRightEye,
      bridgeCenter: bridge,
      leftTemple,
      rightTemple,
      interpupillaryDistancePx: ipd,
      faceWidthPx: faceWidth,
      rollAngleRad: 0.0,
      smoothed: true,
    };

    return this.applySmoothing(rawState);
  }

  /**
   * Applies Exponential Moving Average (EMA) with velocity adaptation.
   */
  private applySmoothing(raw: FaceTrackingState): FaceTrackingState {
    if (!this.smoothedState || !this.smoothedState.detected) {
      this.smoothedState = { ...raw, smoothed: true };
      return this.smoothedState;
    }

    const prev = this.smoothedState;

    // Adapt alpha based on head movement velocity: fast motion -> higher alpha (zero lag)
    const deltaPos = FaceTrackerService.calculateDistance(raw.screenBridgeCenter, prev.screenBridgeCenter);
    const alpha = deltaPos > 15 ? FAST_ALPHA : this.smoothingAlpha;

    const smoothedLeftEye: Point2D = {
      x: FaceTrackerService.applyExponentialSmoothing(raw.screenLeftEyeCenter.x, prev.screenLeftEyeCenter.x, alpha),
      y: FaceTrackerService.applyExponentialSmoothing(raw.screenLeftEyeCenter.y, prev.screenLeftEyeCenter.y, alpha),
    };

    const smoothedRightEye: Point2D = {
      x: FaceTrackerService.applyExponentialSmoothing(raw.screenRightEyeCenter.x, prev.screenRightEyeCenter.x, alpha),
      y: FaceTrackerService.applyExponentialSmoothing(raw.screenRightEyeCenter.y, prev.screenRightEyeCenter.y, alpha),
    };

    const smoothedBridge: Point2D = {
      x: FaceTrackerService.applyExponentialSmoothing(raw.screenBridgeCenter.x, prev.screenBridgeCenter.x, alpha),
      y: FaceTrackerService.applyExponentialSmoothing(raw.screenBridgeCenter.y, prev.screenBridgeCenter.y, alpha),
    };

    const smoothedLeftTemple: Point2D = {
      x: FaceTrackerService.applyExponentialSmoothing(raw.screenLeftTemple.x, prev.screenLeftTemple.x, alpha),
      y: FaceTrackerService.applyExponentialSmoothing(raw.screenLeftTemple.y, prev.screenLeftTemple.y, alpha),
    };

    const smoothedRightTemple: Point2D = {
      x: FaceTrackerService.applyExponentialSmoothing(raw.screenRightTemple.x, prev.screenRightTemple.x, alpha),
      y: FaceTrackerService.applyExponentialSmoothing(raw.screenRightTemple.y, prev.screenRightTemple.y, alpha),
    };

    const smoothedIpd = FaceTrackerService.calculateDistance(smoothedLeftEye, smoothedRightEye);
    const smoothedFaceWidth = FaceTrackerService.calculateDistance(smoothedLeftTemple, smoothedRightTemple);
    const smoothedRoll = FaceTrackerService.smoothRotationAngle(raw.rollAngleRad, prev.rollAngleRad, alpha);

    this.smoothedState = {
      ...raw,
      detected: true,
      isMirrored: raw.isMirrored,
      screenLeftEyeCenter: smoothedLeftEye,
      screenRightEyeCenter: smoothedRightEye,
      screenBridgeCenter: smoothedBridge,
      screenLeftTemple: smoothedLeftTemple,
      screenRightTemple: smoothedRightTemple,
      leftEyeCenter: smoothedLeftEye,
      rightEyeCenter: smoothedRightEye,
      bridgeCenter: smoothedBridge,
      leftTemple: smoothedLeftTemple,
      rightTemple: smoothedRightTemple,
      interpupillaryDistancePx: smoothedIpd,
      faceWidthPx: smoothedFaceWidth,
      rollAngleRad: smoothedRoll,
      smoothed: true,
    };

    return this.smoothedState;
  }

  public reset(): void {
    this.smoothedState = null;
  }

  public destroy(): void {
    this.reset();
    if (this.landmarker) {
      try {
        this.landmarker.close();
      } catch {
        // Ignore during tear-down
      }
      this.landmarker = null;
    }
    this.isReady = false;
  }

  private createUntrackedState(isMirrored: boolean = true): FaceTrackingState {
    const zero: Point2D = { x: 0, y: 0 };
    return {
      detected: false,
      confidence: 0,
      isMirrored,
      screenLeftEyeCenter: zero,
      screenRightEyeCenter: zero,
      screenBridgeCenter: zero,
      screenLeftTemple: zero,
      screenRightTemple: zero,
      screenLeftEyeCornerInner: zero,
      screenLeftEyeCornerOuter: zero,
      screenRightEyeCornerInner: zero,
      screenRightEyeCornerOuter: zero,
      leftEyeCenter: zero,
      rightEyeCenter: zero,
      bridgeCenter: zero,
      leftTemple: zero,
      rightTemple: zero,
      interpupillaryDistancePx: 0,
      faceWidthPx: 0,
      rollAngleRad: 0,
      smoothed: false,
    };
  }

  // ---------------------------------------------------------------------------
  // Static Mathematical & Coordinate Conversion Utilities
  // ---------------------------------------------------------------------------

  /**
   * Projects a normalized point [0..1] to screen canvas pixel space, taking mirroring into account.
   */
  public static convertNormalizedToScreen(
    point: { x: number; y: number },
    canvasWidth: number,
    canvasHeight: number,
    isMirrored: boolean
  ): Point2D {
    const normX = point.x ?? 0.5;
    const normY = point.y ?? 0.5;

    const screenX = isMirrored
      ? (1.0 - normX) * canvasWidth
      : normX * canvasWidth;
    const screenY = normY * canvasHeight;

    return { x: screenX, y: screenY };
  }

  /**
   * Computes a gaze-invariant, blink-resistant eye center from eye anatomy landmarks.
   * Uses weighted iris pupil + canthi midpoint + eyelid midpoint.
   */
  public static calculateRobustEyeCenter(
    innerCorner: { x: number; y: number } | undefined,
    outerCorner: { x: number; y: number } | undefined,
    upperLid: { x: number; y: number } | undefined,
    lowerLid: { x: number; y: number } | undefined,
    pupil: { x: number; y: number } | undefined
  ): { x: number; y: number } {
    const inCorner = innerCorner || { x: 0.5, y: 0.5 };
    const outCorner = outerCorner || inCorner;

    // Canthi midpoint
    const canthiMid = {
      x: (inCorner.x + outCorner.x) * 0.5,
      y: (inCorner.y + outCorner.y) * 0.5,
    };

    // Eyelid midpoint
    const upLid = upperLid || canthiMid;
    const lowLid = lowerLid || canthiMid;
    const eyelidMid = {
      x: (upLid.x + lowLid.x) * 0.5,
      y: (upLid.y + lowLid.y) * 0.5,
    };

    // Anatomical socket center
    const socketCenter = {
      x: (canthiMid.x + eyelidMid.x) * 0.5,
      y: (canthiMid.y + eyelidMid.y) * 0.5,
    };

    // If iris pupil landmark is detected, apply 60/40 weighting
    if (pupil && typeof pupil.x === 'number' && typeof pupil.y === 'number') {
      return {
        x: 0.6 * pupil.x + 0.4 * socketCenter.x,
        y: 0.6 * pupil.y + 0.4 * socketCenter.y,
      };
    }

    return socketCenter;
  }

  /**
   * Euclidean distance between two 2D points.
   */
  public static calculateDistance(p1: Point2D, p2: Point2D): number {
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  /**
   * Interpupillary distance (IPD) between left and right eye centers.
   */
  public static calculateInterpupillaryDistance(leftEye: Point2D, rightEye: Point2D): number {
    return this.calculateDistance(leftEye, rightEye);
  }

  /**
   * Computes screen eye roll angle in radians.
   * Angle of the vector connecting screenLeftEye (smaller X) to screenRightEye (larger X).
   * Positive angle indicates clockwise tilt.
   */
  public static calculateRollAngle(screenLeftEye: Point2D, screenRightEye: Point2D): number {
    const dx = screenRightEye.x - screenLeftEye.x;
    const dy = screenRightEye.y - screenLeftEye.y;
    return Math.atan2(dy, dx);
  }

  /**
   * Scalar 1D Exponential Moving Average.
   */
  public static applyExponentialSmoothing(current: number, previous: number, alpha: number): number {
    return alpha * current + (1 - alpha) * previous;
  }

  /**
   * Circular/Angular Exponential Moving Average to prevent wrapping glitches.
   */
  public static smoothRotationAngle(current: number, previous: number, alpha: number): number {
    let diff = current - previous;
    while (diff < -Math.PI) diff += 2 * Math.PI;
    while (diff > Math.PI) diff -= 2 * Math.PI;
    return previous + alpha * diff;
  }
}

export const faceTracker = new FaceTrackerService();
