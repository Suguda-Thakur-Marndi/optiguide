import type {
  FaceTrackingState,
  FrameTryOnAsset,
  RenderTransform,
  Point2D,
} from '../types/tryOn';

/**
 * OptiGuide Real-Time AR Glasses Canvas Rendering Engine
 *
 * Conformal Affine 2-Point Eye Anchoring:
 * - Maps the frame asset's left and right optical lens centers directly to the user's
 *   detected screen left and right eye centers.
 * - Uses exact Euclidean distance between eyes (interpupillary distance - IPD) to compute
 *   proportional scaling without arbitrary CSS offsets.
 * - Rotates along the eye baseline angle (roll) to maintain true horizontal alignment.
 * - Supports mirrored (selfie) and unmirrored (environment) views identically.
 * - Offscreen SVG dynamic tinting with client-side caching for 60 FPS performance.
 * - Comprehensive clinical and diagnostic HUD telemetry in debug mode.
 */

export interface GlassesRenderOptions {
  selectedColor?: string;
  userScale?: number; // 0.8 to 1.2 (default 1.0)
  userOffsetY?: number; // -30 to +30 pixels (default 0)
  showDebugLandmarks?: boolean;
}

export const ASSET_NATURAL_WIDTH = 800;
export const ASSET_NATURAL_HEIGHT = 300;

export class GlassesRenderer {
  private imageCache = new Map<string, HTMLImageElement>();
  private svgTextCache = new Map<string, string>();
  private loadingPromises = new Map<string, Promise<HTMLImageElement>>();

  /**
   * Clears cached frame images.
   */
  public clearCache(): void {
    this.imageCache.clear();
    this.svgTextCache.clear();
    this.loadingPromises.clear();
  }

  /**
   * Pre-loads a frame asset SVG and prepares tinted variants.
   */
  public async preloadFrame(frame: FrameTryOnAsset, colorHex?: string): Promise<HTMLImageElement | null> {
    const url = frame.try_on_asset_url || `/assets/frames/frame-${frame.frame_shape.toLowerCase().replace(/_/g, '-')}.svg`;
    const color = colorHex || (frame.available_colors && frame.available_colors[0]?.hex_code) || '#111827';
    const cacheKey = `${url}::${color}`;

    if (this.imageCache.has(cacheKey)) {
      return this.imageCache.get(cacheKey)!;
    }

    if (this.loadingPromises.has(cacheKey)) {
      return this.loadingPromises.get(cacheKey)!;
    }

    const promise = this.loadTintedImage(url, color)
      .then((img) => {
        this.imageCache.set(cacheKey, img);
        this.loadingPromises.delete(cacheKey);
        return img;
      })
      .catch((err) => {
        console.error('Failed to load frame asset:', url, err);
        this.loadingPromises.delete(cacheKey);
        return null;
      });

    this.loadingPromises.set(cacheKey, promise as Promise<HTMLImageElement>);
    return promise;
  }

  /**
   * Loads an SVG file, replaces currentColor with the chosen hex color, and creates an Image.
   */
  private async loadTintedImage(url: string, colorHex: string): Promise<HTMLImageElement> {
    let svgText = this.svgTextCache.get(url);

    if (!svgText) {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch SVG asset at ${url} (HTTP ${response.status})`);
      }
      svgText = await response.text();
      this.svgTextCache.set(url, svgText);
    }

    // Replace currentColor with selected color
    const tintedSvg = svgText.replace(/currentColor/g, colorHex);
    const blob = new Blob([tintedSvg], { type: 'image/svg+xml' });
    const blobUrl = URL.createObjectURL(blob);

    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        URL.revokeObjectURL(blobUrl);
        resolve(img);
      };
      img.onerror = (e) => {
        URL.revokeObjectURL(blobUrl);
        reject(e);
      };
      img.src = blobUrl;
    });
  }

  /**
   * Calculates the 2-point conformal affine transformation mapping glasses lens anchors
   * to detected eye centers.
   */
  public calculateTransform(
    faceState: FaceTrackingState,
    frame: FrameTryOnAsset,
    _canvasWidth: number,
    _canvasHeight: number,
    options: GlassesRenderOptions = {}
  ): RenderTransform | null {
    if (!faceState.detected || faceState.interpupillaryDistancePx <= 0) {
      return null;
    }

    const userScale = options.userScale ?? 1.0;
    const userOffsetY = options.userOffsetY ?? 0.0;

    // 1. Detected eyes on screen (guaranteed screenLeftEye.x <= screenRightEye.x)
    const eyeL = faceState.screenLeftEyeCenter;
    const eyeR = faceState.screenRightEyeCenter;

    const dxEye = eyeR.x - eyeL.x;
    const dyEye = eyeR.y - eyeL.y;
    const distEye = Math.hypot(dxEye, dyEye);

    if (distEye <= 1) {
      return null;
    }

    // Base eye angle on screen (roll)
    const rollAngle = Math.atan2(dyEye, dxEye);
    const rotation = rollAngle + (frame.asset_rotation_offset ?? 0);

    // Target midpoint on screen between the eyes (with optional user vertical trim)
    const midEyeScreenX = (eyeL.x + eyeR.x) * 0.5;
    const midEyeScreenY = (eyeL.y + eyeR.y) * 0.5 + userOffsetY;

    // 2. Normalized asset anchor points relative to 800x300 natural canvas
    const leftLensNormX = frame.left_lens_center_x ?? 0.29375;
    const leftLensNormY = frame.left_lens_center_y ?? 0.5;
    const rightLensNormX = frame.right_lens_center_x ?? 0.70625;
    const rightLensNormY = frame.right_lens_center_y ?? 0.5;
    const bridgeNormX = frame.bridge_center_x ?? 0.5;
    const bridgeNormY = frame.bridge_center_y ?? 0.48;

    // Asset anchor coordinates in natural asset pixels
    const leftLensAsset: Point2D = {
      x: leftLensNormX * ASSET_NATURAL_WIDTH,
      y: leftLensNormY * ASSET_NATURAL_HEIGHT,
    };
    const rightLensAsset: Point2D = {
      x: rightLensNormX * ASSET_NATURAL_WIDTH,
      y: rightLensNormY * ASSET_NATURAL_HEIGHT,
    };
    const bridgeAsset: Point2D = {
      x: bridgeNormX * ASSET_NATURAL_WIDTH,
      y: bridgeNormY * ASSET_NATURAL_HEIGHT,
    };

    // Asset optical lens span
    const dxAsset = rightLensAsset.x - leftLensAsset.x;
    const dyAsset = rightLensAsset.y - leftLensAsset.y;
    const distAsset = Math.hypot(dxAsset, dyAsset);

    if (distAsset <= 1) {
      return null;
    }

    // Midpoint between the two lenses in asset space
    const midLensAssetX = (leftLensAsset.x + rightLensAsset.x) * 0.5;
    const midLensAssetY = (leftLensAsset.y + rightLensAsset.y) * 0.5;

    // 3. Conformal scaling factor: maps asset lens span exactly to face eye span
    const assetScale = frame.asset_scale ?? 1.0;
    const finalScale = (distEye / distAsset) * assetScale * userScale;

    // Rendered frame dimensions
    const renderedWidth = ASSET_NATURAL_WIDTH * finalScale;
    const renderedHeight = ASSET_NATURAL_HEIGHT * finalScale;

    // 4. Helper to project any asset anchor point to screen space
    const projectAssetAnchor = (anchor: Point2D): Point2D => {
      const relX = (anchor.x - midLensAssetX) * finalScale;
      const relY = (anchor.y - midLensAssetY) * finalScale;
      const cos = Math.cos(rotation);
      const sin = Math.sin(rotation);
      return {
        x: midEyeScreenX + (relX * cos - relY * sin),
        y: midEyeScreenY + (relX * sin + relY * cos),
      };
    };

    const projectedLensLeft = projectAssetAnchor(leftLensAsset);
    const projectedLensRight = projectAssetAnchor(rightLensAsset);
    const projectedBridge = projectAssetAnchor(bridgeAsset);

    return {
      centerScreenX: midEyeScreenX,
      centerScreenY: midEyeScreenY,
      scale: finalScale,
      rotation,
      width: renderedWidth,
      height: renderedHeight,
      projectedLensLeft,
      projectedLensRight,
      projectedBridge,

      // Backwards compatibility aliases
      x: midEyeScreenX,
      y: midEyeScreenY,
    };
  }

  /**
   * Renders the glasses overlay onto the canvas based on current face landmarks.
   */
  public renderOverlay(
    ctx: CanvasRenderingContext2D,
    faceState: FaceTrackingState,
    frame: FrameTryOnAsset,
    options: GlassesRenderOptions = {}
  ): void {
    if (!faceState.detected) {
      return;
    }

    const canvas = ctx.canvas;
    const transform = this.calculateTransform(
      faceState,
      frame,
      canvas.width,
      canvas.height,
      options
    );

    if (!transform) {
      return;
    }

    const url = frame.try_on_asset_url || `/assets/frames/frame-${frame.frame_shape.toLowerCase().replace(/_/g, '-')}.svg`;
    const color = options.selectedColor || (frame.available_colors && frame.available_colors[0]?.hex_code) || '#111827';
    const cacheKey = `${url}::${color}`;

    const cachedImage = this.imageCache.get(cacheKey);

    if (cachedImage && cachedImage.complete && cachedImage.naturalWidth > 0) {
      ctx.save();

      // Translate to the screen midpoint of the eyes and rotate along the face roll axis
      ctx.translate(transform.centerScreenX, transform.centerScreenY);
      ctx.rotate(transform.rotation);

      // Midpoint between the two lenses in asset space
      const leftLensNormX = frame.left_lens_center_x ?? 0.29375;
      const leftLensNormY = frame.left_lens_center_y ?? 0.5;
      const rightLensNormX = frame.right_lens_center_x ?? 0.70625;
      const rightLensNormY = frame.right_lens_center_y ?? 0.5;

      const midLensNormX = (leftLensNormX + rightLensNormX) * 0.5;
      const midLensNormY = (leftLensNormY + rightLensNormY) * 0.5;

      const drawOffsetX = -midLensNormX * transform.width;
      const drawOffsetY = -midLensNormY * transform.height;

      // Draw subtle optical drop shadow for natural depth
      ctx.shadowColor = 'rgba(15, 23, 42, 0.28)';
      ctx.shadowBlur = Math.max(4, transform.width * 0.015);
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = Math.max(2, transform.height * 0.02);

      ctx.drawImage(cachedImage, drawOffsetX, drawOffsetY, transform.width, transform.height);

      ctx.restore();
    } else {
      // Trigger preload for upcoming frames
      this.preloadFrame(frame, color);
    }

    // Diagnostic HUD and calibration markers in debug mode
    if (options.showDebugLandmarks) {
      this.drawDebugLandmarks(ctx, faceState, transform);
    }
  }

  /**
   * Draws diagnostic alignment markers and clinical telemetry HUD:
   * - Green circles at detected screen eye centers
   * - Cyan dots at eye inner & outer corners
   * - Blue circle at detected nasal bridge
   * - Yellow circles at projected glasses lens anchors (which overlay green eye centers)
   * - Dashed eye baseline connecting eye centers
   * - Clinical telemetry HUD box with IPD, roll angle, scale factor, resolution, mirroring status
   */
  public drawDebugLandmarks(
    ctx: CanvasRenderingContext2D,
    faceState: FaceTrackingState,
    transform?: RenderTransform | null
  ): void {
    ctx.save();

    // 1. Dashed IPD baseline connecting eye centers
    ctx.strokeStyle = 'rgba(14, 165, 233, 0.8)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    ctx.moveTo(faceState.screenLeftEyeCenter.x, faceState.screenLeftEyeCenter.y);
    ctx.lineTo(faceState.screenRightEyeCenter.x, faceState.screenRightEyeCenter.y);
    ctx.stroke();
    ctx.setLineDash([]);

    // 2. Cyan dots at eye corners (inner & outer canthi)
    ctx.fillStyle = '#06b6d4'; // Cyan
    const corners = [
      faceState.screenLeftEyeCornerInner,
      faceState.screenLeftEyeCornerOuter,
      faceState.screenRightEyeCornerInner,
      faceState.screenRightEyeCornerOuter,
    ].filter((pt): pt is Point2D => Boolean(pt && pt.x > 0));

    corners.forEach((pt) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 3, 0, 2 * Math.PI);
      ctx.fill();
    });

    // 3. Green circles at detected screen eye centers
    ctx.fillStyle = '#10b981'; // Emerald Green
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;

    [faceState.screenLeftEyeCenter, faceState.screenRightEyeCenter].forEach((pt) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 5, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    });

    // 4. Blue circle at detected nasal bridge
    ctx.fillStyle = '#0284c7'; // Sky Blue
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(faceState.screenBridgeCenter.x, faceState.screenBridgeCenter.y, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    // 5. Yellow circles at projected glasses anchors (if transform provided)
    let alignmentErrorPx = 0;
    if (transform) {
      ctx.fillStyle = '#eab308'; // Amber Yellow
      ctx.strokeStyle = '#000000';
      ctx.lineWidth = 1.5;

      [transform.projectedLensLeft, transform.projectedLensRight].forEach((pt) => {
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3.5, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
      });

      // Projected bridge
      ctx.fillStyle = '#f97316'; // Orange
      ctx.beginPath();
      ctx.arc(transform.projectedBridge.x, transform.projectedBridge.y, 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // Calculate lens-to-eye alignment discrepancy in screen pixels
      const errL = Math.hypot(
        faceState.screenLeftEyeCenter.x - transform.projectedLensLeft.x,
        faceState.screenLeftEyeCenter.y - transform.projectedLensLeft.y
      );
      const errR = Math.hypot(
        faceState.screenRightEyeCenter.x - transform.projectedLensRight.x,
        faceState.screenRightEyeCenter.y - transform.projectedLensRight.y
      );
      alignmentErrorPx = (errL + errR) * 0.5;
    }

    // 6. On-Canvas Telemetry HUD Box
    const hudX = 14;
    const hudY = 14;
    const hudW = 270;
    const hudH = 145;

    ctx.fillStyle = 'rgba(15, 23, 42, 0.88)'; // Dark slate background
    ctx.strokeStyle = '#0284c7'; // Sky border
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect(hudX, hudY, hudW, hudH, 8);
    ctx.fill();
    ctx.stroke();

    // Telemetry text rows
    ctx.fillStyle = '#38bdf8'; // Sky light
    ctx.font = 'bold 11px system-ui, -apple-system, sans-serif';
    ctx.fillText('OPTIGUIDE AR ALIGNMENT HUD', hudX + 12, hudY + 20);

    ctx.font = '10px monospace';
    ctx.fillStyle = '#f8fafc';
    const rollDeg = (faceState.rollAngleRad * 180) / Math.PI;
    const ipdPx = faceState.interpupillaryDistancePx.toFixed(1);
    const rollStr = `${rollDeg >= 0 ? '+' : ''}${rollDeg.toFixed(1)}°`;
    const mirrorMode = faceState.isMirrored ? 'Mirrored (Selfie)' : 'Direct (Back)';
    const scaleStr = transform ? transform.scale.toFixed(3) : '1.000';
    const resStr = `${ctx.canvas.width}x${ctx.canvas.height}px`;
    const confStr = `${Math.round(faceState.confidence * 100)}%`;
    const errStr = alignmentErrorPx < 0.1 ? '< 0.1 px (Locked)' : `${alignmentErrorPx.toFixed(1)} px`;

    ctx.fillText(`• Feed Mode:     ${mirrorMode}`, hudX + 12, hudY + 38);
    ctx.fillText(`• Canvas Res:    ${resStr}`, hudX + 12, hudY + 53);
    ctx.fillText(`• Screen IPD:    ${ipdPx} px`, hudX + 12, hudY + 68);
    ctx.fillText(`• Roll Angle:    ${rollStr}`, hudX + 12, hudY + 83);
    ctx.fillText(`• Affine Scale:  ${scaleStr}x`, hudX + 12, hudY + 98);
    ctx.fillText(`• Anchor Error:  ${errStr}`, hudX + 12, hudY + 113);
    ctx.fillText(`• Confidence:    ${confStr}`, hudX + 12, hudY + 128);

    ctx.restore();
  }

  /**
   * Captures a high-resolution snapshot merging the camera video frame with the overlaid frame.
   */
  public captureSnapshot(
    video: HTMLVideoElement,
    faceState: FaceTrackingState,
    frame: FrameTryOnAsset,
    options: GlassesRenderOptions = {},
    isMirrored?: boolean
  ): string {
    const offscreen = document.createElement('canvas');
    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;
    offscreen.width = width;
    offscreen.height = height;

    const ctx = offscreen.getContext('2d');
    if (!ctx) {
      throw new Error('Unable to obtain 2D canvas context for snapshot capture');
    }

    const mirrorActive = isMirrored !== undefined ? isMirrored : faceState.isMirrored;

    // 1. Draw raw video feed matching mirror mode
    ctx.save();
    if (mirrorActive) {
      ctx.translate(width, 0);
      ctx.scale(-1, 1);
    }
    ctx.drawImage(video, 0, 0, width, height);
    ctx.restore();

    // 2. Render AR glasses overlay if face detected
    if (faceState.detected) {
      // Determine if face state was computed at a different canvas scale
      const currentCanvasWidth = video.clientWidth > 0 ? video.clientWidth : width;
      const currentCanvasHeight = video.clientHeight > 0 ? video.clientHeight : height;

      let scaledFaceState = faceState;
      if (Math.abs(currentCanvasWidth - width) > 2 || Math.abs(currentCanvasHeight - height) > 2) {
        const sx = width / currentCanvasWidth;
        const sy = height / currentCanvasHeight;

        const scalePt = (pt: Point2D): Point2D => ({ x: pt.x * sx, y: pt.y * sy });

        scaledFaceState = {
          ...faceState,
          isMirrored: mirrorActive,
          screenLeftEyeCenter: scalePt(faceState.screenLeftEyeCenter),
          screenRightEyeCenter: scalePt(faceState.screenRightEyeCenter),
          screenBridgeCenter: scalePt(faceState.screenBridgeCenter),
          screenLeftTemple: scalePt(faceState.screenLeftTemple),
          screenRightTemple: scalePt(faceState.screenRightTemple),
          screenLeftEyeCornerInner: scalePt(faceState.screenLeftEyeCornerInner),
          screenLeftEyeCornerOuter: scalePt(faceState.screenLeftEyeCornerOuter),
          screenRightEyeCornerInner: scalePt(faceState.screenRightEyeCornerInner),
          screenRightEyeCornerOuter: scalePt(faceState.screenRightEyeCornerOuter),
          leftEyeCenter: scalePt(faceState.leftEyeCenter),
          rightEyeCenter: scalePt(faceState.rightEyeCenter),
          bridgeCenter: scalePt(faceState.bridgeCenter),
          leftTemple: scalePt(faceState.leftTemple),
          rightTemple: scalePt(faceState.rightTemple),
          interpupillaryDistancePx: faceState.interpupillaryDistancePx * sx,
          faceWidthPx: faceState.faceWidthPx * sx,
        };
      }

      this.renderOverlay(ctx, scaledFaceState, frame, options);
    }

    // 3. Return high-quality PNG data URI
    return offscreen.toDataURL('image/png', 0.95);
  }
}

export const glassesRenderer = new GlassesRenderer();
