import type {
  FaceTrackingState,
  FrameTryOnAsset,
  RenderTransform,
} from '../types/tryOn';

/**
 * OptiGuide Real-Time AR Glasses Canvas Rendering Engine
 *
 * Key Capabilities:
 * - Geometric alignment of glasses bridge to detected facial nose bridge
 * - Interpupillary distance (IPD) based proportional scaling
 * - 2D Roll angle rotation transformation
 * - Dynamic color tinting via vector SVG recoloring & offscreen compositing
 * - High-speed image caching for smooth 60 FPS rendering
 * - High-resolution snapshot capture combining camera feed and AR frame
 */

export interface GlassesRenderOptions {
  selectedColor?: string;
  userScale?: number; // 0.8 to 1.2 (default 1.0)
  userOffsetY?: number; // -30 to +30 pixels (default 0)
  showDebugLandmarks?: boolean;
}

const ASSET_NATURAL_WIDTH = 800;
const ASSET_NATURAL_HEIGHT = 300;

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
   * Computes the geometric transformation matrix parameters for the glasses overlay.
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

    // Asset reference coordinates
    const leftLensX = frame.left_lens_center_x ?? 0.2875;
    const rightLensX = frame.right_lens_center_x ?? 0.7125;

    const lensSpanNorm = Math.abs(rightLensX - leftLensX);
    if (lensSpanNorm <= 0.01) {
      return null;
    }

    // Target frame pixel width matching face IPD
    // frame.asset_scale typically 1.0
    const assetScale = frame.asset_scale ?? 1.0;
    const targetWidth =
      (faceState.interpupillaryDistancePx / lensSpanNorm) * assetScale * userScale;
    const aspectRatio = ASSET_NATURAL_HEIGHT / ASSET_NATURAL_WIDTH;
    const targetHeight = targetWidth * aspectRatio;

    // Bridge anchor coordinate on screen
    const anchorScreenX = faceState.bridgeCenter.x;
    const anchorScreenY = faceState.bridgeCenter.y + userOffsetY;

    // Rotation angle
    const rotation = faceState.rollAngleRad + (frame.asset_rotation_offset ?? 0);

    return {
      x: anchorScreenX,
      y: anchorScreenY,
      width: targetWidth,
      height: targetHeight,
      rotation,
      scale: userScale,
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

      // Translate to bridge anchor
      ctx.translate(transform.x, transform.y);
      ctx.rotate(transform.rotation);

      // In the asset coordinate system, the bridge is at (bridge_center_x, bridge_center_y)
      const bridgeNormX = frame.bridge_center_x ?? 0.5;
      const bridgeNormY = frame.bridge_center_y ?? 0.48;

      const drawOffsetX = -bridgeNormX * transform.width;
      const drawOffsetY = -bridgeNormY * transform.height;

      // Draw tinted frame image with subtle drop shadow for depth realism
      ctx.shadowColor = 'rgba(15, 23, 42, 0.25)';
      ctx.shadowBlur = Math.max(4, transform.width * 0.015);
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = Math.max(2, transform.height * 0.02);

      ctx.drawImage(cachedImage, drawOffsetX, drawOffsetY, transform.width, transform.height);

      ctx.restore();
    } else {
      // Trigger preload for upcoming frames
      this.preloadFrame(frame, color);
    }

    // Optional debug landmark rendering for clinical verification
    if (options.showDebugLandmarks) {
      this.drawDebugLandmarks(ctx, faceState);
    }
  }

  /**
   * Draws tracking alignment markers (pupils, bridge, face width) for diagnostic inspection.
   */
  public drawDebugLandmarks(ctx: CanvasRenderingContext2D, faceState: FaceTrackingState): void {
    ctx.save();

    // Pupil points
    ctx.fillStyle = '#10b981'; // Teal
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;

    [faceState.leftEyeCenter, faceState.rightEyeCenter].forEach((pt) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    });

    // Bridge center
    ctx.fillStyle = '#0284c7'; // Blue
    ctx.beginPath();
    ctx.arc(faceState.bridgeCenter.x, faceState.bridgeCenter.y, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();

    // Connecting IPD baseline
    ctx.strokeStyle = 'rgba(14, 165, 233, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(faceState.leftEyeCenter.x, faceState.leftEyeCenter.y);
    ctx.lineTo(faceState.rightEyeCenter.x, faceState.rightEyeCenter.y);
    ctx.stroke();

    ctx.restore();
  }

  /**
   * Captures a high-resolution snapshot merging the camera video frame with the overlaid frame.
   */
  public captureSnapshot(
    video: HTMLVideoElement,
    faceState: FaceTrackingState,
    frame: FrameTryOnAsset,
    options: GlassesRenderOptions = {}
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

    // 1. Draw raw video feed
    // Mirror horizontally if user-facing camera
    ctx.save();
    ctx.translate(width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, width, height);
    ctx.restore();

    // 2. Compute face state scaled to snapshot canvas dimensions
    const scaleX = width / (video.clientWidth || width);
    const scaleY = height / (video.clientHeight || height);

    const scaledFaceState: FaceTrackingState = {
      ...faceState,
      leftEyeCenter: {
        x: faceState.leftEyeCenter.x * scaleX,
        y: faceState.leftEyeCenter.y * scaleY,
      },
      rightEyeCenter: {
        x: faceState.rightEyeCenter.x * scaleX,
        y: faceState.rightEyeCenter.y * scaleY,
      },
      bridgeCenter: {
        x: faceState.bridgeCenter.x * scaleX,
        y: faceState.bridgeCenter.y * scaleY,
      },
      interpupillaryDistancePx: faceState.interpupillaryDistancePx * scaleX,
      faceWidthPx: faceState.faceWidthPx * scaleX,
    };

    // 3. Render AR glasses overlay
    this.renderOverlay(ctx, scaledFaceState, frame, options);

    // 4. Return high-quality PNG data URI
    return offscreen.toDataURL('image/png', 0.95);
  }
}

export const glassesRenderer = new GlassesRenderer();
