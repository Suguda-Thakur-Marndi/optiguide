export interface FrameColorOption {
  hex_code: string;
  name: string;
}

export interface FrameCategory {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  is_active: boolean;
}

export interface FrameTryOnAsset {
  frame_id: string;
  sku: string;
  name: string;
  brand_name: string;
  category_name?: string | null;
  frame_type: string;
  frame_material: string;
  frame_shape: string;
  gender_target: string;
  base_price_inr: number;
  is_active: boolean;
  in_stock: boolean;
  image_url?: string | null;
  description?: string | null;

  // Try-On Asset Telemetry & Geometry
  try_on_asset_url?: string | null;
  try_on_asset_type: string;
  available_colors: FrameColorOption[];
  left_lens_center_x: number;
  left_lens_center_y: number;
  right_lens_center_x: number;
  right_lens_center_y: number;
  bridge_center_x: number;
  bridge_center_y: number;
  asset_scale: number;
  asset_rotation_offset: number;
  asset_version: string;

  // Physical Dimensions (in millimeters)
  frame_width_mm?: number | null;
  bridge_width_mm?: number | null;
  temple_length_mm?: number | null;
  lens_width_mm?: number | null;
  lens_height_mm?: number | null;

  // Availability Notice
  is_try_on_available: boolean;
  availability_notice?: string | null;
}

export interface TryOnSession {
  id: string;
  user_id?: string | null;
  screening_session_id?: string | null;
  selected_product_id?: string | null;
  selected_color: string;
  selected_scale: number;
  selected_offset_y: number;
  camera_facing: string;
  device_type: string;
  snapshots_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TryOnSnapshot {
  id: string;
  session_id: string;
  product_id?: string | null;
  selected_color: string;
  title: string;
  face_detected: boolean;
  created_at: string;
  data_url?: string;
}

export interface FavouriteItem {
  id: string;
  user_id: string;
  product_id: string;
  selected_color: string;
  notes?: string | null;
  created_at: string;
  product?: FrameTryOnAsset | null;
}

export interface Point2D {
  x: number;
  y: number;
}

export interface Point3D extends Point2D {
  z?: number;
}

export interface FaceTrackingState {
  detected: boolean;
  confidence: number;
  leftEyeCenter: Point2D;
  rightEyeCenter: Point2D;
  bridgeCenter: Point2D;
  leftTemple: Point2D;
  rightTemple: Point2D;
  interpupillaryDistancePx: number;
  faceWidthPx: number;
  rollAngleRad: number;
  smoothed: boolean;
}

export interface RenderTransform {
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  scale: number;
}
